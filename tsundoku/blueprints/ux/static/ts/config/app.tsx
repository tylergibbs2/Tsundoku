import { hydrate } from "preact";

import { APITokenComponent } from "./components/apitoken";
import { FeedbackBtns } from "./components/feedback_btns";
import { getInjector } from "../fluent";
import { PostProcessing } from "./components/postprocessing";

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
                <h1 class="title is-4">{_("section-api-title")}</h1>
                <h2 class="subtitle is-6">{_("section-api-subtitle")}</h2>
                <div style={{width: "50%"}}>
                    <APITokenComponent />
                </div>
                <a href="https://tsundoku.readthedocs.io/en/latest/" class="button is-info mt-2">{_("config-api-documentation")}</a>
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
