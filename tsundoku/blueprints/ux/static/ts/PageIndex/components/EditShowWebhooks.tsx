import { getInjector } from "../../fluent";
import { useState, Dispatch, SetStateAction } from "react";
import { useForm } from "react-hook-form";
import { Show, Webhook } from "../../interfaces";
import { IonIcon } from "../../icon";

const _ = getInjector();

interface EditShowWebhooksParams {
  tab: string;
  show: Show;
  webhooksToUpdate: Webhook[];
  setWebhooksToUpdate: Dispatch<SetStateAction<Webhook[]>>;
}

export const EditShowWebhooks = ({
  tab,
  show,
  webhooksToUpdate,
  setWebhooksToUpdate,
}: EditShowWebhooksParams) => {
  if (show === null) return <></>;

  return (
    <div className={tab !== "webhooks" ? "is-hidden" : ""}>
      {show.webhooks.length !== 0 && (
        <table className="table is-fullwidth is-hoverable">
          <thead>
            <tr className="has-text-centered">
              <th>{_("edit-webhooks-th-webhook")}</th>
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
            {show.webhooks.map((webhook) => (
              <EditWebhookTableRow
                key={webhook.base.base_id}
                webhook={webhook}
                webhooksToUpdate={webhooksToUpdate}
                setWebhooksToUpdate={setWebhooksToUpdate}
              />
            ))}
          </tbody>
        </table>
      )}
      {show.webhooks.length === 0 && (
        <div className="container has-text-centered mb-5">
          <h2 className="subtitle">{_("edit-webhooks-is-empty")}</h2>
        </div>
      )}
    </div>
  );
};

interface EditWebhookTableRowParams {
  webhook: Webhook;
  webhooksToUpdate: Webhook[];
  setWebhooksToUpdate: Dispatch<SetStateAction<Webhook[]>>;
}

const EditWebhookTableRow = ({
  webhook,
  webhooksToUpdate,
  setWebhooksToUpdate,
}: EditWebhookTableRowParams) => {
  const [triggers, setTriggers] = useState(webhook.triggers);

  const { register } = useForm({
    defaultValues: {
      failed: triggers.includes("failed"),
      downloading: triggers.includes("downloading"),
      downloaded: triggers.includes("downloaded"),
      renamed: triggers.includes("renamed"),
      moved: triggers.includes("moved"),
      completed: triggers.includes("completed"),
    },
  });

  const update = (e: any) => {
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

    let newWh: Webhook = JSON.parse(JSON.stringify(webhook));
    newWh.triggers = newTrs;

    idx = webhooksToUpdate.findIndex(
      (toFind) => toFind.base.base_id === newWh.base.base_id
    );
    if (idx === -1) setWebhooksToUpdate([newWh, ...webhooksToUpdate]);
    else {
      let temp = [...webhooksToUpdate];
      temp[idx] = newWh;
      setWebhooksToUpdate(temp);
    }
  };

  return (
    <tr className="has-text-centered">
      <td className="is-vcentered">{webhook.base.name}</td>
      <td className="is-vcentered">
        <input
          type="checkbox"
          {...register("failed")}
          onChange={update}
        ></input>
      </td>
      <td className="is-vcentered">
        <input
          type="checkbox"
          {...register("downloading")}
          onChange={update}
        ></input>
      </td>
      <td className="is-vcentered">
        <input
          type="checkbox"
          {...register("downloaded")}
          onChange={update}
        ></input>
      </td>
      <td className="is-vcentered">
        <input
          type="checkbox"
          {...register("renamed")}
          onChange={update}
        ></input>
      </td>
      <td className="is-vcentered">
        <input type="checkbox" {...register("moved")} onChange={update}></input>
      </td>
      <td className="is-vcentered">
        <input
          type="checkbox"
          {...register("completed")}
          onChange={update}
        ></input>
      </td>
    </tr>
  );
};
