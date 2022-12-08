import { getInjector } from "../fluent";
import { Dispatch, SetStateAction } from "react";
import { WebhookBase } from "../interfaces";
import ReactHtmlParser from "react-html-parser";
import { useMutation, useQueryClient } from "react-query";
import { deleteWebhookById } from "../queries";
import { toast } from "bulma-toast";

let resources = ["index", "webhooks"];

const _ = getInjector(resources);

interface DeleteModalParams {
  activeModal: string | null;
  setActiveModal: Dispatch<SetStateAction<string | null>>;
  activeWebhook: WebhookBase;
  setActiveWebhook: Dispatch<SetStateAction<WebhookBase | null>>;
}

export const DeleteModal = ({
  activeModal,
  setActiveModal,
  activeWebhook,
  setActiveWebhook,
}: DeleteModalParams) => {
  const queryClient = useQueryClient();

  const mutation = useMutation(deleteWebhookById, {
    onSuccess: () => {
      queryClient.setQueryData(["webhooks"], (oldWebhooks: WebhookBase[]) =>
        oldWebhooks.filter((wh) => wh.base_id !== activeWebhook?.base_id)
      );
      toast({
        message: _("webhook-delete-success"),
        duration: 5000,
        position: "bottom-right",
        type: "is-success",
        dismissible: true,
        animate: { in: "fadeIn", out: "fadeOut" },
      });

      setActiveModal(null);
      setActiveWebhook(null);
    },
  });

  const performDelete = () => {
    mutation.mutate(activeWebhook.base_id);
  };

  const cancel = () => {
    if (mutation.isLoading) return;

    setActiveWebhook(null);
    setActiveModal(null);
  };

  return (
    <div
      className={
        "modal modal-fx-fadeInScale " +
        (activeWebhook && activeModal === "delete" ? "is-active" : "")
      }
    >
      <div className="modal-background" onClick={cancel}></div>
      <div className="modal-card">
        <header className="modal-card-head">
          <p className="modal-card-title">{_("delete-webhook-modal-header")}</p>
          <button
            className="delete"
            onClick={cancel}
            aria-label="close"
          ></button>
        </header>

        <section className="modal-card-body">
          <p>
            {activeWebhook &&
              ReactHtmlParser(
                _("delete-confirm-text", { name: activeWebhook.name })
              )}
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
