import type { BaseSyntheticEvent, Dispatch, SetStateAction } from "react";
import ReactHtmlParser from "react-html-parser";
import type { Entry, Show } from "../../api";
import { getInjector } from "../../fluent";
import { IonIcon } from "../../icon";
import {
  localizePythonTimeAbsolute,
  localizePythonTimeRelative,
} from "../../utils";

const _ = getInjector();

const sortByDate = (a: Entry, b: Entry): number => {
  const dateA = new Date(a.last_update);
  const dateB = new Date(b.last_update);

  return dateB > dateA ? 1 : -1;
};

interface ListItemParams {
  textFilter: string;
  filters: string[];
  show: Show;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
  setActiveShow: Dispatch<SetStateAction<Show | null>>;
}

export const ListItem = ({
  textFilter: _textFilter,
  filters: _filters,
  show,
  setCurrentModal,
  setActiveShow,
}: ListItemParams) => {
  let title: any;
  if (show.metadata?.link)
    title = (
      <a
        className="ml-1"
        title={show.title}
        href={show.metadata?.link ?? undefined}
        target="_blank"
        rel="noopener"
      >
        <b>{show.title}</b>
      </a>
    );
  else
    title = (
      <b className="ml-1" title={show.title}>
        {show.title}
      </b>
    );

  let timeDisplay: any;
  if ((show.entries ?? []).length !== 0) {
    const sorted = [...(show.entries ?? [])].sort(sortByDate);
    const entry = sorted[0];

    const localized = localizePythonTimeRelative(entry.last_update);
    const localizedTitle = localizePythonTimeAbsolute(entry.last_update);
    timeDisplay = (
      <span title={localizedTitle}>
        {_("edit-entries-last-update", { time: localized })}
      </span>
    );
  } else timeDisplay = "";

  const openEditModal = () => {
    setActiveShow(show);
    setCurrentModal("edit");
  };

  const openDeleteModal = () => {
    setActiveShow(show);
    setCurrentModal("delete");
  };

  const reportPoster404 = async (_err: BaseSyntheticEvent) => {
    const request = {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    };

    await fetch(`/api/v1/shows/${show.id_}/cache`, request);
  };

  return (
    <tr>
      <td className="is-vcentered">
        <a
          href={show.metadata?.link ?? undefined}
          target="_blank"
          rel="noopener"
        >
          <figure className="image is-3by4">
            <img
              src={show.metadata?.poster ?? undefined}
              loading="lazy"
              onError={reportPoster404}
            />
          </figure>
        </a>
      </td>
      <td
        className="is-vcentered"
        style={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {show.metadata?.html_status &&
          ReactHtmlParser(show.metadata?.html_status)}{" "}
        {title}
      </td>
      <td className="is-vcentered">{timeDisplay}</td>
      <td className="is-vcentered">
        <a
          className="button is-info mr-1"
          onClick={openEditModal}
          title={_("show-edit-link")}
        >
          <span className="icon">
            <IonIcon name="pencil-sharp" />
          </span>
        </a>
        <a
          className="button is-danger"
          onClick={openDeleteModal}
          title={_("show-delete-link")}
        >
          <span className="icon">
            <IonIcon name="trash" />
          </span>
        </a>
      </td>
    </tr>
  );
};

interface AddShowLIParams {
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
}

export const AddShowLI = ({ setCurrentModal }: AddShowLIParams) => {
  const openModal = () => {
    setCurrentModal("add");
  };

  return (
    <tr>
      <td colSpan={4}>
        <button
          onClick={openModal}
          style={{ height: "100%" }}
          className="button is-outlined is-success is-large is-fullwidth"
        >
          <span className="icon">
            <IonIcon name="add-circle" />
          </span>
        </button>
      </td>
    </tr>
  );
};
