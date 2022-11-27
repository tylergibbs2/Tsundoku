import { hydrate } from "preact";
import { useState, useEffect } from "preact/hooks";

import { NyaaIndividualResult, Show, GeneralConfig } from "../interfaces";
import { NyaaShowModal } from "./modal";
import { SearchBox, SearchTable, SpaceHolder } from "./search";
import { getInjector } from "../fluent";

import "bulma-dashboard/dist/bulma-dashboard.min.css";

let resources = [
    "nyaa_search"
];

const _ = getInjector(resources);

const NyaaSearchApp = () => {
    const [userShows, setUserShows] = useState<Show[]>([]);
    const [results, setResults] = useState<NyaaIndividualResult[]>([]);
    const [choice, setChoice] = useState<NyaaIndividualResult>(null);
    const [generalConfig, setGeneralConfig] = useState<GeneralConfig>({});

    const fetchConfig = async () => {
        let request = {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        };

        let resp = await fetch("/api/v1/config/general", request);
        let resp_json: any;
        if (resp.ok)
            resp_json = await resp.json();
        else
            return;

        setGeneralConfig(resp_json.result);
    }

    const fetchUserShows = async () => {
        let request = {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        };

        let response = await fetch("/api/v1/shows", request);
        if (!response.ok)
            return;

        let data = await response.json();
        setUserShows(data.result);
    }

    useEffect(() => {
        fetchConfig();
        fetchUserShows();
    }, [])

    return (
        <div class={choice ? "is-clipped" : ""}>
            <NyaaShowModal setChoice={setChoice} choice={choice} shows={userShows} generalConfig={generalConfig} />
            <div class="columns is-vcentered">
                <div class="column is-4">
                    <div class="container">
                        <h1 class="title">{_("nyaa-page-title")}</h1>
                        <h2 class="subtitle">{_("nyaa-page-subtitle")}</h2>
                    </div>
                </div>
                <div class="column is-4 is-offset-4">
                    <SearchBox setResults={setResults} />
                </div>
            </div>

            <div id="search-container" class="container">
                {results.length ? <SearchTable setChoice={setChoice} results={results} /> : <SpaceHolder />}
            </div>
        </div>
    )
}

hydrate(<NyaaSearchApp />, document.getElementById("nyaa-main"));