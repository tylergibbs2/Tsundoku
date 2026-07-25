import { getInjector } from "../fluent";
import { Dispatch, SetStateAction } from "react";
import { Show } from "../api";
import ReactHtmlParser from "react-html-parser";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { removeShow } from "./queries";
import { toast } from "bulma-toast";

const _ = getInjector();

interface DeleteModalParams {
  show: Show | null;
  setActiveShow: Dispatch<SetStateAction<Show | null>>;
  currentModal: string | null;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
}

export const DeleteModal = ({
  show,
  setActiveShow,
  currentModal,
  setCurrentModal,
}: DeleteModalParams) => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: removeShow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shows"] });
      toast({
        message: _("show-delete-success"),
        duration: 5000,
        position: "bottom-right",
        type: "is-success",
        dismissible: true,
        animate: { in: "fadeIn", out: "fadeOut" },
      });

      setCurrentModal(null);
      setActiveShow(null);
    },
  });

  const performDelete = () => {
    if (show) mutation.mutate(show.id_);
  };

  const cancel = () => {
    if (mutation.isPending) return;

    setActiveShow(null);
    setCurrentModal(null);
  };

  return (
    <div
      className={
        "modal modal-fx-fadeInScale " +
        (show && currentModal === "delete" ? "is-active" : "")
      }
    >
      <div className="modal-background" onClick={cancel}></div>
      <div className="modal-card">
        <header className="modal-card-head">
          <p className="modal-card-title">{_("delete-modal-header")}</p>
          <button
            className="delete"
            onClick={cancel}
            aria-label="close"
          ></button>
        </header>

        <section className="modal-card-body">
          <p>
            {show &&
              ReactHtmlParser(_("delete-confirm-text", { name: show.title }))}
          </p>
        </section>

        <footer className="modal-card-foot">
          <button className="button is-danger" onClick={performDelete}>
            {_("delete-confirm-button")}
          </button>
          <button className="button" onClick={cancel}>
            {_("delete-cancel")}
          </button>
        </footer>
      </div>
    </div>
  );
};
