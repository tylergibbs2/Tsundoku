import { WebhookBase } from "../interfaces";
import { getInjector } from "../fluent";

import "../../css/webhooks.css";
import { useQuery } from "react-query";
import { fetchWebhookBases } from "../queries";
import { WebhookCard } from "./components/WebhookCard";
import { AddModal } from "./add_modal";
import { EditModal } from "./edit_modal";
import { DeleteModal } from "./delete_modal";
import { useEffect, useState } from "react";

let resources = [
    "webhooks"
];

const _ = getInjector(resources);


export const WebhooksApp = () => {
    document.getElementById("navWebhooks").classList.add("is-active");

    const bases = useQuery("webhooks", fetchWebhookBases);

    const [activeModal, setActiveModal] = useState<string | null>(null);
    const [activeWebhook, setActiveWebhook] = useState<WebhookBase | null>(null);

    useEffect(() => {
        if (activeModal)
            document.body.classList.add("is-clipped");
        else
            document.body.classList.remove("is-clipped");
    }, [activeModal]);

    if (bases.isLoading)
        return (
            <progress className="progress is-large is-primary" style={{ transform: "translateY(33vh)" }} max="100" />
        )

    return (
        <>
            <AddModal
                activeModal={activeModal}
                setActiveModal={setActiveModal}
            />

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
                    {bases.data.length === 0 &&
                        <div className="container has-text-centered my-6">
                            <h3 className="title is-3">{_("webhook-page-empty")}</h3>
                            <h4 className="subtitle is-5">{_("webhook-page-empty-subtitle")}</h4>
                        </div>
                    }
                    {bases.data.length > 0 && bases.data.map((base: WebhookBase) =>
                        <WebhookCard
                            key={base.base_id}
                            setActiveModal={setActiveModal}
                            setActiveWebhook={setActiveWebhook}
                            webhook={base}
                        />)
                    }
                </div>
            </div>

            <div className="container has-text-centered mt-3">
                <button className="button is-medium is-success" onClick={() => setActiveModal("add")}>{_("webhook-add-button")}</button>
            </div>
        </>
    )
}
