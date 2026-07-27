import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { Show } from "../api";
import { getInjector } from "../fluent";
import { AddModal } from "./add_modal";
import { Filters } from "./components/filters";
import { Pagination } from "./components/pagination";
import { Shows } from "./components/shows";
import { DeleteModal } from "./delete_modal";
import { EditModal } from "./edit_modal";
import { generalConfigQuery, showsQuery } from "./queries";

import "../../css/index.css";
import { GlobalLoading } from "../Components/GlobalLoading";

const _ = getInjector();

export const IndexApp = () => {
  document.getElementById("navIndex")?.classList.add("is-active");

  const storedFilters = localStorage.getItem("showFilters");
  const storedViewType = localStorage.getItem("viewType");

  const storedSortDirection = localStorage.getItem("sortDirection");
  const storedSortKey = localStorage.getItem("sortKey");
  const storedPage = localStorage.getItem("currentPage");

  const [activeShow, setActiveShow] = useState<Show | null>(null);
  const [currentModal, setCurrentModal] = useState<string | null>(null);

  const [viewType, setViewType] = useState<string>(storedViewType || "cards");
  const [currentPage, setCurrentPage] = useState<number>(
    parseInt(storedPage || "1", 10),
  );

  const [filters, setFilters] = useState<string[]>(
    JSON.parse(storedFilters ?? "null") || [
      "current",
      "finished",
      "tba",
      "unreleased",
      "upcoming",
    ],
  );
  const [textFilter, setTextFilter] = useState<string>("");

  const [sortDirection, setSortDirection] = useState<string>(
    storedSortDirection || "+",
  );
  const [sortKey, setSortKey] = useState<string>(storedSortKey || "title");

  const generalConfig = useQuery(generalConfigQuery());

  const shows = useQuery({
    ...showsQuery({
      page: currentPage,
      limit: 17,
      ...(filters.length > 0 ? { filters: filters.join(",") } : {}),
      ...(textFilter ? { text_filter: textFilter } : {}),
      ...(sortKey ? { sort_key: sortKey } : {}),
      ...(sortDirection ? { sort_direction: sortDirection } : {}),
    }),
    placeholderData: keepPreviousData,
  });

  useEffect(() => {
    localStorage.setItem("showFilters", JSON.stringify(filters));
    localStorage.setItem("viewType", viewType);
    localStorage.setItem("sortDirection", sortDirection);
    localStorage.setItem("sortKey", sortKey);
    localStorage.setItem("currentPage", currentPage.toString());
  }, [filters, viewType, sortDirection, sortKey, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
    // eslint-disable-next-line
  }, [filters, textFilter, sortKey, sortDirection]);

  useEffect(() => {
    if (currentModal) document.body.classList.add("is-clipped");
    else document.body.classList.remove("is-clipped");
  }, [currentModal]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  if (shows.isPending) return <GlobalLoading withText={true} />;

  const showsData = shows.data?.shows || [];
  const pagination = shows.data?.pagination;

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
        shows={showsData}
        setActiveShow={setActiveShow}
        filters={filters}
        textFilter={textFilter}
        sortDirection={sortDirection}
        sortKey={sortKey}
        setCurrentModal={setCurrentModal}
        viewType={viewType}
      />
      {pagination && (
        <Pagination pagination={pagination} onPageChange={handlePageChange} />
      )}
    </>
  );
};
