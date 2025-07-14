import { useState, ChangeEvent } from "react";
import { NyaaSearchResult, NyaaIndividualResult } from "../interfaces";
import { getInjector } from "../fluent";
import { IonIcon } from "../icon";

const NyaaSearchURL = "/api/v1/nyaa";

const _ = getInjector();

interface NyaaSearchPanelProps {
  initialQuery?: string;
  showId: number;
  onEntryAdd: (entry: NyaaIndividualResult, overwrite: boolean) => void;
  existingEpisodes?: number[];
}

export const NyaaSearchPanel = ({
  initialQuery = "",
  showId,
  onEntryAdd,
  existingEpisodes = [],
}: NyaaSearchPanelProps) => {
  const [query, setQuery] = useState<string>(initialQuery);
  const [results, setResults] = useState<NyaaIndividualResult[]>([]);
  const [isSearching, setSearchingState] = useState<boolean>(false);
  const [selected, setSelected] = useState<NyaaIndividualResult | null>(null);
  const [adding, setAdding] = useState<boolean>(false);
  const [overwrite, setOverwrite] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const limit = 15;

  // Only update the query state with debounce, do not search
  const updateQuery = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    // No search here, just update query
  };

  // Only search when the button is clicked or page changes
  const handleSearch = (newPage?: number) => {
    setSearchingState(true);
    const pageToFetch = newPage ?? page;
    fetch(
      `${NyaaSearchURL}?` +
        new URLSearchParams({
          query: query,
          limit: limit.toString(),
          page: pageToFetch.toString(),
        })
    )
      .then((res) => res.json())
      .then((data: NyaaSearchResult) => setResults(data.result || []))
      .finally(() => setSearchingState(false));
    if (typeof newPage === "number") setPage(newPage);
  };

  const handleAdd = async (entry: NyaaIndividualResult) => {
    setAdding(true);
    // Call the parent callback to add the entry (should POST to /api/v1/nyaa)
    await onEntryAdd(entry, overwrite);
    setAdding(false);
  };

  const handlePrev = () => {
    if (page > 1) handleSearch(page - 1);
  };
  const handleNext = () => {
    if (results.length === limit) handleSearch(page + 1);
  };

  return (
    <div>
      <div className={"field has-addons"} style={{ marginBottom: "1rem" }}>
        <div
          className={
            "control has-icons-left is-expanded " +
            (isSearching ? "is-loading" : "")
          }
        >
          <input
            className="input"
            type="text"
            placeholder={_("search-placeholder")}
            value={query}
            onInput={updateQuery}
            disabled={isSearching}
          />
          <span className="icon is-small is-left">
            <IonIcon name="search" />
          </span>
        </div>
        <div className="control">
          <button
            className="button is-info"
            onClick={() => {
              setPage(1);
              handleSearch(1);
            }}
            disabled={isSearching}
          >
            {_("search-button")}
          </button>
        </div>
      </div>
      <div className="field" style={{ marginBottom: "1rem" }}>
        <div className="control">
          <label className="checkbox">
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
              style={{ marginRight: "0.5em" }}
            />
            {_("search-overwrite-checkbox")}
          </label>
        </div>
      </div>
      {results.length === 0 ? (
        <div className="container has-text-centered my-6">
          <h3 className="title is-3">{_("search-empty-results")}</h3>
          <h4 className="subtitle is-5">{_("search-start-searching")}</h4>
        </div>
      ) : (
        <div className="container">
          <table className="table is-hoverable is-fullwidth">
            <thead>
              <tr>
                <th>{_("search-th-name")}</th>
                <th>{_("search-th-size")}</th>
                <th>{_("search-th-date")}</th>
                <th title={_("search-th-seeders")}>
                  {" "}
                  <span className="icon">
                    <IonIcon name="arrow-up" />
                  </span>{" "}
                </th>
                <th title={_("search-th-leechers")}>
                  {" "}
                  <span className="icon">
                    <IonIcon name="arrow-down" />
                  </span>{" "}
                </th>
                <th title={_("search-th-link")}>
                  {" "}
                  <span className="icon">
                    <IonIcon name="link" />
                  </span>{" "}
                </th>
                <th>{_("search-th-action")}</th>
              </tr>
            </thead>
            <tbody>
              {results.map((show: NyaaIndividualResult) => {
                const episodeNum = parseInt(
                  show.title.match(/\b(?:ep?|episode)\s*(\d+)/i)?.[1] || "NaN",
                  10
                );
                const alreadyAdded = existingEpisodes.includes(episodeNum);
                return (
                  <tr key={show.post_link}>
                    <td style={{ width: "60%" }}>{show.title}</td>
                    <td>{show.size}</td>
                    <td>{show.published}</td>
                    <td className="has-text-success">{show.seeders}</td>
                    <td className="has-text-danger">{show.leechers}</td>
                    <td>
                      <a
                        href={show.post_link}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {_("search-item-link")}
                      </a>
                    </td>
                    <td>
                      <button
                        className={
                          "button is-small is-success" +
                          (adding ? " is-loading" : "")
                        }
                        onClick={() => handleAdd(show)}
                        disabled={adding || alreadyAdded}
                      >
                        {alreadyAdded
                          ? _("search-already-added")
                          : _("search-add-entry")}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <nav
            className="pagination is-centered"
            role="navigation"
            aria-label="pagination"
            style={{ marginTop: "1rem" }}
          >
            <button
              className="button"
              onClick={handlePrev}
              disabled={page === 1 || isSearching}
            >
              {_("pagination-previous")}
            </button>
            <span style={{ margin: "0 1em" }}>Page {page}</span>
            <button
              className="button"
              onClick={handleNext}
              disabled={results.length < limit || isSearching}
            >
              {_("pagination-next")}
            </button>
          </nav>
        </div>
      )}
    </div>
  );
};
