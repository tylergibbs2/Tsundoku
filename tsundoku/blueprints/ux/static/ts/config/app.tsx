import { hydrate } from "preact";

import { APITokenComponent } from "./components/apitoken";
import { GeneralConfigApp } from "./components/generalconfig";
import { FeedbackBtns } from "./components/feedback_btns";
import { TorrentConfig } from "./components/torrentclient";
import { getInjector } from "../fluent";
import { PostProcessing } from "./components/postprocessing";
import { FeedsConfig } from "./components/feedsconfig"

import "bulma-dashboard/dist/bulma-dashboard.min.css";

let resources = [
    "config"
];

const _ = getInjector(resources);

const ConfigApp = () => {

    return (
        <>
            <div class="columns">
                <div class="column is-full">
                    <h1 class="title">{_("config-page-title")}</h1>
                    <h2 class="subtitle">{_("config-page-subtitle")}</h2>
                </div>
            </div>
            <FeedbackBtns />
            <section class="section">
                <h1 class="title is-4">{_("section-general-title")}</h1>
                <h2 class="subtitle is-6">{_("section-general-subtitle")}</h2>
                <GeneralConfigApp />
            </section>
            <section class="section">
                <h1 class="title is-4">{_("section-feeds-title")}</h1>
                <h2 class="subtitle is-6">{_("section-feeds-subtitle")}</h2>
                <FeedsConfig />
            </section>
            <section class="section">
                <h1 class="title is-4">{_("section-torrent-title")}</h1>
                <h2 class="subtitle is-6">{_("section-torrent-subtitle")}</h2>
                <TorrentConfig />
            </section>
            <section class="section">
                <h1 class="title is-4">{_("section-api-title")}</h1>
                <h2 class="subtitle is-6">{_("section-api-subtitle")}</h2>
                <div class="box" style={{width: "50%"}}>
                    <APITokenComponent />
                    <a href="https://tsundoku.moe/docs" class="button is-info mt-2">{_("config-api-documentation")}</a>
                </div>
            </section>
            <section class="section">
                <h1 class="title is-4">{_("section-encode-title")}</h1>
                <h2 class="subtitle is-6">{_("section-encode-subtitle")}</h2>
                <PostProcessing />
            </section>
        </>
    )
}


hydrate(<ConfigApp />, document.getElementById("config-main"));
