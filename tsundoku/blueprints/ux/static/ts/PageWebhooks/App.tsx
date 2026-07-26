import { getInjector } from "../fluent";

import "../../css/webhooks.css";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { WebhookBase } from "../api";
import { GlobalLoading } from "../Components/GlobalLoading";
import { AddModal } from "./add_modal";
import { WebhookCard } from "./components/WebhookCard";
import { DeleteModal } from "./delete_modal";
import { EditModal } from "./edit_modal";
import { webhookBasesQuery } from "./queries";

const _ = getInjector();

export const WebhooksApp = () => {
  document.getElementById("navWebhooks")?.classList.add("is-active");

  const bases = useQuery(webhookBasesQuery());

  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [activeWebhook, setActiveWebhook] = useState<WebhookBase | null>(null);

  useEffect(() => {
    if (activeModal) document.body.classList.add("is-clipped");
    else document.body.classList.remove("is-clipped");
  }, [activeModal]);

  // `data` stays optional in the types until it has actually resolved, so it
  // is checked alongside the pending flag rather than asserted below.
  if (bases.isPending || !bases.data) return <GlobalLoading withText={true} />;

  return (
    <>
      <AddModal activeModal={activeModal} setActiveModal={setActiveModal} />

      <EditModal
        activeModal={activeModal}
        setActiveModal={setActiveModal}
        activeWebhook={activeWebhook}
        setActiveWebhook={setActiveWebhook}
      />

      <DeleteModal
        activeModal={activeModal}
        setActiveModal={setActiveModal}
        activeWebhook={activeWebhook}
        setActiveWebhook={setActiveWebhook}
      />

      <div className="container mb-3">
        <h1 className="title">{_("webhooks-page-title")}</h1>
        <h2 className="subtitle">{_("webhooks-page-subtitle")}</h2>
      </div>

      <div className="container" style={{ padding: "15px" }}>
        <div className="columns is-multiline">
          {bases.data.length === 0 && (
            <div className="container has-text-centered my-6">
              <h3 className="title is-3">{_("webhook-page-empty")}</h3>
              <h4 className="subtitle is-5">
                {_("webhook-page-empty-subtitle")}
              </h4>
            </div>
          )}
          {bases.data.length > 0 &&
            bases.data.map((base: WebhookBase) => (
              <WebhookCard
                key={base.base_id}
                setActiveModal={setActiveModal}
                setActiveWebhook={setActiveWebhook}
                webhook={base}
              />
            ))}
        </div>
      </div>

      <div className="container has-text-centered mt-3">
        <button
          className="button is-medium is-success"
          onClick={() => setActiveModal("add")}
        >
          {_("webhook-add-button")}
        </button>
      </div>
    </>
  );
};
