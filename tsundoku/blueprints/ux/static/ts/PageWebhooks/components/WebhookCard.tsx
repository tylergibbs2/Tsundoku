import { Dispatch, SetStateAction } from "react";
import { getInjector } from "../../fluent";
import { WebhookBase } from "../../interfaces";
import { useQuery } from "react-query";

import { fetchWebhookValidityById } from "../../queries";

interface WebhookCardParams {
  setActiveModal: Dispatch<SetStateAction<string | null>>;
  setActiveWebhook: Dispatch<SetStateAction<WebhookBase | null>>;
  webhook: WebhookBase;
}

const _ = getInjector();

export const WebhookCard = ({
  setActiveModal,
  setActiveWebhook,
  webhook,
}: WebhookCardParams) => {
  const { data, isLoading } = useQuery(
    ["webhook_validity", webhook.base_id],
    async () => fetchWebhookValidityById(webhook.base_id)
  );

  const openEditModal = () => {
    setActiveModal("edit");
    setActiveWebhook(webhook);
  };

  const openDeleteModal = () => {
    setActiveModal("delete");
    setActiveWebhook(webhook);
  };

  return (
    <div className="column is-one-quarter">
      <div className="card">
        <header className="card-header">
          <p className="card-header-title">{webhook.name}</p>
          <a className="card-header-icon">
            <span className="icon">
              <figure className="image is-16x16">
                {webhook.service === "discord" && (
                  <img src="/ux/static/img/discord.png" />
                )}
                {webhook.service === "slack" && (
                  <img src="/ux/static/img/slack.png" />
                )}
              </figure>
            </span>
          </a>
        </header>
        <div className="card-content">
          <p className="is-size-6 has-text-centered py-4">
            {isLoading && <b>{_("webhook-status-loading")}</b>}
            {!isLoading && data && <b>{_("webhook-status-valid")}</b>}
            {!isLoading && !data && <b>{_("webhook-status-invalid")}</b>}
          </p>
        </div>
        <footer className="card-footer">
          <p className="card-footer-item">
            <a onClick={openEditModal}>{_("webhook-edit-link")}</a>
          </p>
          <p className="card-footer-item">
            <a onClick={openDeleteModal}>{_("webhook-delete-link")}</a>
          </p>
        </footer>
      </div>
    </div>
  );
};
