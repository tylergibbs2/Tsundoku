import { getInjector } from "../../fluent";
import { BaseSyntheticEvent, Dispatch, SetStateAction } from "react";
import { Show } from "../../interfaces";

import ReactHtmlParser from "react-html-parser";
import { IonIcon } from "../../icon";

const _ = getInjector();

interface CardParams {
  textFilter: string;
  filters: string[];
  show: Show;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
  setActiveShow: Dispatch<SetStateAction<Show | null>>;
}

export const Card = ({
  textFilter,
  filters,
  show,
  setCurrentModal,
  setActiveShow,
}: CardParams) => {
  let title: any;
  if (show.metadata.link)
    title = (
      <a href={show.metadata.link}>
        <b>{show.title}</b>
      </a>
    );
  else title = <b>{show.title}</b>;

  let shouldShow: boolean = true;
  if (show.metadata.kitsu_id !== null) {
    if (filters.length !== 0)
      shouldShow = filters.includes(show.metadata.status);

    if (shouldShow)
      shouldShow = show.title.toLowerCase().includes(textFilter.toLowerCase());
  }

  const openEditModal = () => {
    setActiveShow(show);
    setCurrentModal("edit");
  };

  const openDeleteModal = () => {
    setActiveShow(show);
    setCurrentModal("delete");
  };

  const reportPoster404 = async (err: BaseSyntheticEvent) => {
    let request = {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    };

    await fetch(`/api/v1/shows/${show.id_}/cache`, request);
  };

  return (
    <div
      className={
        "column is-12-mobile is-4-tablet is-2-desktop " +
        (shouldShow ? "" : "is-hidden")
      }
    >
      <div className="card">
        {show.metadata.poster && (
          <div className="card-image">
            {show.metadata.html_status &&
              ReactHtmlParser(show.metadata.html_status)}
            <a href={show.metadata.link} target="_blank">
              <figure className="image is-3by4">
                <img
                  src={show.metadata.poster}
                  loading="lazy"
                  onError={reportPoster404}
                />
              </figure>
            </a>
          </div>
        )}
        <div className="card-content">
          <p
            className="subtitle has-tooltip-arrow has-tooltip-multiline has-tooltip-up"
            data-tooltip={show.title}
          >
            <span>{title}</span>
          </p>
        </div>
        <footer className="card-footer">
          <p className="card-footer-item">
            <a onClick={openEditModal}>{_("show-edit-link")}</a>
          </p>
          <p className="card-footer-item">
            <a onClick={openDeleteModal}>{_("show-delete-link")}</a>
          </p>
        </footer>
      </div>
    </div>
  );
};

interface AddShowCardParams {
  setCurrentModal: Dispatch<SetStateAction<string>>;
  isOnlyCardInRow: boolean;
}

export const AddShowCard = ({ setCurrentModal, isOnlyCardInRow }: AddShowCardParams) => {
  const openModal = () => {
    setCurrentModal("add");
  };

  return (
    <>
      <div className="column is-2">
        <button
          onClick={openModal}
          style={{ height: "100%" }}
          className="button is-outlined is-success is-large is-fullwidth"
        >
          <span className="icon">
            <IonIcon name="add-circle" />
          </span>
        </button>
      </div>
      { isOnlyCardInRow && <div className="column is-2 is-invisible">
        <div className="card">
          <figure className="image is-3by4"></figure>

          <div className="card-content"></div>
          <footer className="card-footer">
            <p className="card-footer-item">
              <a>Placeholder</a>
            </p>
          </footer>
        </div>
      </div> }
    </>
  );
};
