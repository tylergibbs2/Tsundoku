import type { Dispatch, SetStateAction } from "react";
import type { Entry, Show } from "../../api";
import { getInjector } from "../../fluent";
import { AddShowCard, Card } from "./card";
import { AddShowLI, ListItem } from "./li";

const _ = getInjector();

const getSortedShows = (
  toSort: Show[],
  sortDirection: string,
  sortKey: string,
) => {
  let first = 1;
  let second = -1;
  if (sortDirection === "-") {
    first = -1;
    second = 1;
  }

  const newShows = [...toSort];
  let sortFunc: any;
  switch (sortKey) {
    case "title":
      sortFunc = (a: Show, b: Show) => {
        return a.title > b.title ? first : second;
      };
      newShows.sort(sortFunc);
      break;
    case "update": {
      const entrySortFunc = (a: Entry, b: Entry) => {
        const dateA = new Date(a.last_update);
        const dateB = new Date(b.last_update);
        return dateB > dateA ? 1 : -1;
      };
      sortFunc = (a: Show, b: Show) => {
        const aEntries = [...(a.entries ?? [])].sort(entrySortFunc);
        const bEntries = [...(b.entries ?? [])].sort(entrySortFunc);
        let dateA: Date;
        let dateB: Date;
        try {
          dateA = new Date(aEntries[0].last_update);
        } catch {
          dateA = new Date(0);
        }
        try {
          dateB = new Date(bEntries[0].last_update);
        } catch {
          dateB = new Date(0);
        }
        return dateA > dateB ? first : second;
      };
      newShows.sort(sortFunc);
      break;
    }
    case "dateAdded":
      sortFunc = (a: Show, b: Show) => {
        const dateA = new Date(a.created_at);
        const dateB = new Date(b.created_at);
        return dateA > dateB ? first : second;
      };
      newShows.sort(sortFunc);
      break;
  }

  return newShows;
};

interface ShowsParams {
  shows: Show[];
  setActiveShow: Dispatch<SetStateAction<Show | null>>;
  filters: string[];
  textFilter: string;
  sortDirection: string;
  sortKey: string;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
  viewType: string;
}

export const Shows = ({
  shows,
  setActiveShow,
  filters,
  textFilter,
  sortDirection,
  sortKey,
  setCurrentModal,
  viewType,
}: ShowsParams) => {
  if (viewType === "cards") {
    return (
      <CardView
        shows={shows}
        setActiveShow={setActiveShow}
        filters={filters}
        textFilter={textFilter}
        sortDirection={sortDirection}
        sortKey={sortKey}
        setCurrentModal={setCurrentModal}
      />
    );
  } else {
    return (
      <ListView
        shows={shows}
        setActiveShow={setActiveShow}
        filters={filters}
        textFilter={textFilter}
        sortDirection={sortDirection}
        sortKey={sortKey}
        setCurrentModal={setCurrentModal}
      />
    );
  }
};

interface ViewTypeParams {
  shows: Show[];
  setActiveShow: Dispatch<SetStateAction<Show | null>>;
  filters: string[];
  textFilter: string;
  sortDirection: string;
  sortKey: string;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
}

const CardView = ({
  shows,
  setActiveShow,
  filters,
  textFilter,
  sortDirection,
  sortKey,
  setCurrentModal,
}: ViewTypeParams) => {
  const sortedShows = getSortedShows(shows, sortDirection, sortKey);

  const isOnlyCardInRow = sortedShows.length % 6 === 0;

  return (
    <div className="columns is-mobile is-multiline">
      {sortedShows.map((show: Show) => (
        <Card
          key={show.id_}
          textFilter={textFilter}
          filters={filters}
          show={show}
          setCurrentModal={setCurrentModal}
          setActiveShow={setActiveShow}
        />
      ))}
      <AddShowCard
        setCurrentModal={setCurrentModal}
        isOnlyCardInRow={isOnlyCardInRow}
      />
    </div>
  );
};

const ListView = ({
  shows,
  setActiveShow,
  filters,
  textFilter,
  sortDirection,
  sortKey,
  setCurrentModal,
}: ViewTypeParams) => {
  return (
    <table
      className="table is-fullwidth is-striped is-hoverable"
      style={{ tableLayout: "fixed" }}
    >
      <thead>
        <tr>
          <th style={{ width: "5%" }}></th>
          <th style={{ width: "70%" }}>{_("add-form-name-field")}</th>
          <th style={{ width: "15%" }}>{_("list-view-entry-update-header")}</th>
          <th style={{ width: "10%" }}>{_("list-view-actions-header")}</th>
        </tr>
      </thead>
      <tbody>
        {getSortedShows(shows, sortDirection, sortKey).map((show: Show) => (
          <ListItem
            key={show.id_}
            textFilter={textFilter}
            filters={filters}
            show={show}
            setCurrentModal={setCurrentModal}
            setActiveShow={setActiveShow}
          />
        ))}

        <AddShowLI setCurrentModal={setCurrentModal} />
      </tbody>
    </table>
  );
};
