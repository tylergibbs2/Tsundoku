import { useState, useEffect } from "react";

import { NyaaIndividualResult, Show, GeneralConfig } from "../interfaces";
import { NyaaShowModal } from "./modal";
import { SearchBox, SearchTable, SpaceHolder } from "./search";
import { getInjector } from "../fluent";

import "../../css/nyaa_search.css";
import { useQuery } from "react-query";
import { fetchConfig } from "../queries";

let resources = ["nyaa_search"];

const _ = getInjector(resources);

export const NyaaSearchApp = () => {
  document.getElementById("navNyaa").classList.add("is-active");

  const [userShows, setUserShows] = useState<Show[]>([]);
  const [results, setResults] = useState<NyaaIndividualResult[]>([]);
  const [choice, setChoice] = useState<NyaaIndividualResult>(null);

  const generalConfig = useQuery(["config", "general"], async () => {
    return await fetchConfig<GeneralConfig>("general");
  });

  const fetchUserShows = async () => {
    let request = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    };

    let response = await fetch("/api/v1/shows", request);
    if (!response.ok) return;

    let data = await response.json();
    setUserShows(data.result);
  };

  useEffect(() => {
    fetchUserShows();
  }, []);

  return (
    <div className={choice ? "is-clipped" : ""}>
      <NyaaShowModal
        setChoice={setChoice}
        choice={choice}
        shows={userShows}
        generalConfig={generalConfig.data}
      />
      <div className="columns is-vcentered">
        <div className="column is-4">
          <div className="container">
            <h1 className="title">{_("nyaa-page-title")}</h1>
            <h2 className="subtitle">{_("nyaa-page-subtitle")}</h2>
          </div>
        </div>
        <div className="column is-4 is-offset-4">
          <SearchBox setResults={setResults} />
        </div>
      </div>

      <div id="search-container" className="container">
        {results.length ? (
          <SearchTable setChoice={setChoice} results={results} />
        ) : (
          <SpaceHolder />
        )}
      </div>
    </div>
  );
};
