import { toast } from "bulma-toast";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { SubmitHandler, useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "react-query";
import { getInjector } from "../fluent";
import { IonIcon } from "../icon";
import { WebhookBase } from "../interfaces";
import { addNewWebhook } from "../queries";

const _ = getInjector();

interface AddModalParams {
  activeModal?: string;
  setActiveModal: Dispatch<SetStateAction<string | null>>;
}

export type AddWebhookFormValues = {
  name: string;
  service: string;
  url: string;
  content_fmt: string;
  default_triggers: string;
};

export const AddModal = ({ activeModal, setActiveModal }: AddModalParams) => {
  const queryClient = useQueryClient();

  const mutation = useMutation(addNewWebhook, {
    onSuccess: (newWebhook) => {
      queryClient.setQueryData(["webhooks"], (oldWebhooks: WebhookBase[]) => [
        ...oldWebhooks,
        newWebhook,
      ]);
      toast({
        message: _("webhook-add-success"),
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
    name: "",
    service: "discord",
    url: "",
    content_fmt: "{name}, episode {episode}, has been marked as {state}",
  };

  const [triggers, setTriggers] = useState<string[]>([]);

  const { register, handleSubmit, reset } = useForm({
    defaultValues: defaultValues,
  });

  useEffect(() => {
    reset(defaultValues);
  }, [activeModal]);

  const submitHandler: SubmitHandler<AddWebhookFormValues> = (
    formData: AddWebhookFormValues
  ) => {
    mutation.mutate({ ...formData, default_triggers: triggers.join(",") });
  };

  const cancel = () => {
    if (mutation.isLoading) return;

    setActiveModal(null);
  };

  const updateTriggers = (e: any) => {
    let idx = triggers.findIndex((tr) => tr === e.target.name);
    let newTrs: string[];
    if (idx === -1) {
      newTrs = [e.target.name, ...triggers];
      setTriggers(newTrs);
    } else {
      newTrs = [...triggers];
      newTrs.splice(idx, 1);
      setTriggers(newTrs);
    }
  };

  return (
    <div
      className={
        "modal modal-fx-fadeInScale " +
        (activeModal === "add" ? "is-active" : "")
      }
    >
      <div className="modal-background" onClick={cancel}></div>
      <div className="modal-card">
        <header className="modal-card-head">
          <p className="modal-card-title">{_("add-webhook-modal-header")}</p>
          <button
            className="delete"
            onClick={cancel}
            aria-label="close"
          ></button>
        </header>

        <section className="modal-card-body">
          <form id="add-webhook-form" onSubmit={handleSubmit(submitHandler)}>
            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-webhook-form-name-tt")}
                >
                  {_("add-webhook-form-name-field")}
                </span>
              </label>
              <div className="control">
                <input
                  {...register("name", { required: true })}
                  className="input"
                  type="text"
                  placeholder={_("add-webhook-form-name-placeholder")}
                />
              </div>
            </div>

            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-webhook-form-service-tt")}
                >
                  {_("add-webhook-form-service-field")}
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
                  data-tooltip={_("add-webhook-form-url-tt")}
                >
                  {_("add-webhook-form-url-field")}
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
                  data-tooltip={_("add-webhook-form-content-tt")}
                >
                  {_("add-webhook-form-content-field")}
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

            <div className="field">
              <label className="label">
                <span
                  className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                  data-tooltip={_("add-webhook-form-default-triggers-tt")}
                >
                  {_("add-webhook-form-default-triggers-field")}
                </span>
              </label>

              <table className="table is-fullwidth is-hoverable">
                <thead>
                  <tr className="has-text-centered">
                    <td>
                      <span
                        className="icon has-tooltip-arrow has-tooltip-up"
                        data-tooltip={_("edit-webhooks-th-failed")}
                      >
                        <IonIcon name="ban" />
                      </span>
                    </td>
                    <td>
                      <span
                        className="icon has-tooltip-arrow has-tooltip-up"
                        data-tooltip={_("edit-webhooks-th-downloading")}
                      >
                        <IonIcon name="download" />
                      </span>
                    </td>
                    <td>
                      <span
                        className="icon has-tooltip-arrow has-tooltip-up"
                        data-tooltip={_("edit-webhooks-th-downloaded")}
                      >
                        <IonIcon name="save" />
                      </span>
                    </td>
                    <td>
                      <span
                        className="icon has-tooltip-arrow has-tooltip-up"
                        data-tooltip={_("edit-webhooks-th-renamed")}
                      >
                        <IonIcon name="pencil-sharp" />
                      </span>
                    </td>
                    <td>
                      <span
                        className="icon has-tooltip-arrow has-tooltip-up"
                        data-tooltip={_("edit-webhooks-th-moved")}
                      >
                        <IonIcon name="arrow-forward-circle" />
                      </span>
                    </td>
                    <td>
                      <span
                        className="icon has-tooltip-arrow has-tooltip-up"
                        data-tooltip={_("edit-webhooks-th-completed")}
                      >
                        <IonIcon name="checkmark-circle" />
                      </span>
                    </td>
                  </tr>
                </thead>
                <tbody>
                  <tr className="has-text-centered">
                    <td className="is-vcentered">
                      <input
                        type="checkbox"
                        name="failed"
                        onChange={updateTriggers}
                      ></input>
                    </td>
                    <td className="is-vcentered">
                      <input
                        type="checkbox"
                        name="downloading"
                        onChange={updateTriggers}
                      ></input>
                    </td>
                    <td className="is-vcentered">
                      <input
                        type="checkbox"
                        name="downloaded"
                        onChange={updateTriggers}
                      ></input>
                    </td>
                    <td className="is-vcentered">
                      <input
                        type="checkbox"
                        name="renamed"
                        onChange={updateTriggers}
                      ></input>
                    </td>
                    <td className="is-vcentered">
                      <input
                        type="checkbox"
                        name="moved"
                        onChange={updateTriggers}
                      ></input>
                    </td>
                    <td className="is-vcentered">
                      <input
                        type="checkbox"
                        name="completed"
                        onChange={updateTriggers}
                      ></input>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </form>
        </section>

        <footer className="modal-card-foot is-size-7">
          <button
            className={
              "button is-success " + (mutation.isLoading ? "is-loading" : "")
            }
            type="submit"
            form="add-webhook-form"
          >
            {_("add-webhook-form-add-button")}
          </button>
          <button className="button" onClick={cancel}>
            {_("add-webhook-form-cancel-button")}
          </button>
        </footer>
      </div>
    </div>
  );
};
