import { useState, useEffect } from "react";
import { useQuery } from "react-query";

import { AddModal } from "./add_modal";
import { EditModal } from "./edit_modal";
import { DeleteModal } from "./delete_modal";
import { Show, GeneralConfig } from "../interfaces";
import { getInjector } from "../fluent";
import { Filters } from "./components/filters";
import { Shows } from "./components/shows";
import { fetchConfig, fetchShows } from "../queries";

import "../../css/index.css";
import { GlobalLoading } from "../Components/GlobalLoading";

const _ = getInjector();

export const IndexApp = () => {
  document.getElementById("navIndex").classList.add("is-active");

  let storedFilters = localStorage.getItem("showFilters");
  let storedViewType = localStorage.getItem("viewType");

  let storedSortDirection = localStorage.getItem("sortDirection");
  let storedSortKey = localStorage.getItem("sortKey");

  const [activeShow, setActiveShow] = useState<Show | null>(null);
  const [currentModal, setCurrentModal] = useState<string | null>(null);

  const [viewType, setViewType] = useState<string>(storedViewType || "cards");

  const [filters, setFilters] = useState<string[]>(
    JSON.parse(storedFilters) || [
      "current",
      "finished",
      "tba",
      "unreleased",
      "upcoming",
    ]
  );
  const [textFilter, setTextFilter] = useState<string>("");

  const [sortDirection, setSortDirection] = useState<string>(
    storedSortDirection || "+"
  );
  const [sortKey, setSortKey] = useState<string>(storedSortKey || "title");

  const generalConfig = useQuery(["config", "general"], async () => {
    return await fetchConfig<GeneralConfig>("general");
  });

  const shows = useQuery(["shows"], fetchShows);

  useEffect(() => {
    localStorage.setItem("showFilters", JSON.stringify(filters));
    localStorage.setItem("viewType", viewType);
    localStorage.setItem("sortDirection", sortDirection);
    localStorage.setItem("sortKey", sortKey);
  }, [filters, viewType, sortDirection, sortKey]);

  useEffect(() => {
    if (currentModal) document.body.classList.add("is-clipped");
    else document.body.classList.remove("is-clipped");
  }, [currentModal]);

  if (shows.isLoading) return <GlobalLoading withText={true} />;

  return (
    <>
      <AddModal
        currentModal={currentModal}
        setCurrentModal={setCurrentModal}
        generalConfig={generalConfig.data}
      />

      <DeleteModal
        show={activeShow}
        setActiveShow={setActiveShow}
        currentModal={currentModal}
        setCurrentModal={setCurrentModal}
      />

      <EditModal
        activeShow={activeShow}
        setActiveShow={setActiveShow}
        currentModal={currentModal}
        setCurrentModal={setCurrentModal}
      />

      <div className="columns">
        <div className="column is-full">
          <h1 className="title">{_("shows-page-title")}</h1>
          <h2 className="subtitle">{_("shows-page-subtitle")}</h2>
        </div>
      </div>
      <Filters
        filters={filters}
        setFilters={setFilters}
        setTextFilter={setTextFilter}
        viewType={viewType}
        setViewType={setViewType}
        sortKey={sortKey}
        setSortKey={setSortKey}
        sortDirection={sortDirection}
        setSortDirection={setSortDirection}
      />
      <Shows
        shows={shows.data}
        setActiveShow={setActiveShow}
        filters={filters}
        textFilter={textFilter}
        sortDirection={sortDirection}
        sortKey={sortKey}
        setCurrentModal={setCurrentModal}
        viewType={viewType}
      />
    </>
  );
};
