import { APITokenComponent } from "./components/apitoken";
import { GeneralConfigApp } from "./components/generalconfig";
import { FeedbackBtns } from "./components/feedback_btns";
import { TorrentConfig } from "./components/torrentclient";
import { getInjector } from "../fluent";
import { PostProcessing } from "./components/postprocessing";
import { FeedsConfig } from "./components/feedsconfig"

import "../../css/config.css";

let resources = [
    "config"
];

const _ = getInjector(resources);

export const ConfigApp = () => {
    document.getElementById("navConfig").classList.add("is-active");

    return (
        <>
            <div className="columns">
                <div className="column is-full">
                    <h1 className="title">{_("config-page-title")}</h1>
                    <h2 className="subtitle">{_("config-page-subtitle")}</h2>
                </div>
            </div>
            <FeedbackBtns />
            <section className="section">
                <h1 className="title is-4">{_("section-general-title")}</h1>
                <h2 className="subtitle is-6">{_("section-general-subtitle")}</h2>
                <GeneralConfigApp />
            </section>
            <section className="section">
                <h1 className="title is-4">{_("section-feeds-title")}</h1>
                <h2 className="subtitle is-6">{_("section-feeds-subtitle")}</h2>
                <FeedsConfig />
            </section>
            <section className="section">
                <h1 className="title is-4">{_("section-torrent-title")}</h1>
                <h2 className="subtitle is-6">{_("section-torrent-subtitle")}</h2>
                <TorrentConfig />
            </section>
            <section className="section">
                <h1 className="title is-4">{_("section-api-title")}</h1>
                <h2 className="subtitle is-6">{_("section-api-subtitle")}</h2>
                <div className="box" style={{width: "50%"}}>
                    <APITokenComponent />
                    <a href="https://tsundoku.moe/docs" className="button is-info mt-2">{_("config-api-documentation")}</a>
                </div>
            </section>
            <section className="section">
                <h1 className="title is-4">{_("section-encode-title")}</h1>
                <h2 className="subtitle is-6">{_("section-encode-subtitle")}</h2>
                <PostProcessing />
            </section>
        </>
    )
}
