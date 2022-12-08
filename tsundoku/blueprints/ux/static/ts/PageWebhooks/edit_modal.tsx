import { toast } from "bulma-toast";
import { Dispatch, SetStateAction, useEffect } from "react";
import { SubmitHandler, useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "react-query";
import { getInjector } from "../fluent";
import { WebhookBase } from "../interfaces";
import { updateWebhookById } from "../queries";

let resources = ["webhooks"];

const _ = getInjector(resources);

interface EditModalParams {
  activeModal?: string;
  setActiveModal: Dispatch<SetStateAction<string | null>>;
  activeWebhook: WebhookBase | null;
  setActiveWebhook: Dispatch<SetStateAction<WebhookBase | null>>;
}

type EditWebhookFormValues = {
  name: string;
  service: string;
  url: string;
  content_fmt: string;
};

export const EditModal = ({
  activeModal,
  setActiveModal,
  activeWebhook,
  setActiveWebhook,
}: EditModalParams) => {
  const queryClient = useQueryClient();

  const mutation = useMutation(updateWebhookById, {
    onSuccess: (updatedWebhook) => {
      queryClient.setQueryData(["webhooks"], (oldWebhooks: WebhookBase[]) => [
        ...oldWebhooks.filter((wh) => wh.base_id !== updatedWebhook.base_id),
        updatedWebhook,
      ]);
      toast({
        message: _("webhook-edit-success"),
        duration: 5000,
        position: "bottom-right",
        type: "is-success",
        dismissible: true,
        animate: { in: "fadeIn", out: "fadeOut" },
      });

      setActiveModal(null);
    },
  });

  let defaultValues = {
    name: activeWebhook?.name,
    service: activeWebhook?.service,
    url: activeWebhook?.url,
    content_fmt: activeWebhook?.content_fmt,
  };

  const { register, handleSubmit, reset } = useForm({
    defaultValues: defaultValues,
  });

  useEffect(() => {
    if (activeWebhook) reset(defaultValues);
  }, [activeModal, activeWebhook]);

  const submitHandler: SubmitHandler<EditWebhookFormValues> = (
    formData: EditWebhookFormValues
  ) => {
    mutation.mutate({
      base_id: activeWebhook.base_id,
      valid: false,
      ...formData,
    });
  };

  const cancel = () => {
    if (mutation.isLoading) return;

    setActiveModal(null);
  };

  return (
    <div
      className={
        "modal modal-fx-fadeInScale " +
        (activeModal === "edit" ? "is-active" : "")
      }
    >
      <div className="modal-background" onClick={cancel}></div>
      <div className="modal-card">
        <header className="modal-card-head">
          <p className="modal-card-title">{_("edit-modal-header")}</p>
          <button
            className="delete"
            onClick={cancel}
            aria-label="close"
          ></button>
        </header>

        <section className="modal-card-body">
          <form id="edit-webhook-form" onSubmit={handleSubmit(submitHandler)}>
            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-form-name-tt")}
                >
                  {_("add-form-name-field")}
                </span>
              </label>
              <div className="control">
                <input
                  {...register("name", { required: true })}
                  className="input"
                  type="text"
                  placeholder={_("add-form-name-placeholder")}
                />
              </div>
            </div>

            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-form-service-tt")}
                >
                  {_("add-form-service-field")}
                </span>
              </label>
              <div className="select">
                <select {...register("service")}>
                  <option value="discord">Discord</option>
                  <option value="slack">Slack</option>
                </select>
              </div>
            </div>

            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-form-url-tt")}
                >
                  {_("add-form-url-field")}
                </span>
              </label>
              <div className="control">
                <input
                  {...register("url", { required: true })}
                  className="input"
                  pattern="https://.*"
                  type="url"
                />
              </div>
            </div>

            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-form-content-tt")}
                >
                  {_("add-form-content-field")}
                </span>
              </label>
              <div className="control">
                <input
                  {...register("content_fmt")}
                  className="input"
                  type="text"
                  placeholder="{name}, episode {episode}, has been marked as {state}"
                />
              </div>
            </div>
          </form>
        </section>

        <footer className="modal-card-foot is-size-7">
          <button
            className={
              "button is-success " + (mutation.isLoading ? "is-loading" : "")
            }
            type="submit"
            form="edit-webhook-form"
          >
            {_("edit-form-save-button")}
          </button>
          <button className="button" onClick={cancel}>
            {_("add-form-cancel-button")}
          </button>
        </footer>
      </div>
    </div>
  );
};
