import { useEffect, useState } from "preact/hooks";
import { getInjector } from "../../fluent";


let resources = [
    "config"
];

const _ = getInjector(resources);


interface FeedsConfig {
    polling_interval?: number;
    complete_check_interval?: number;
    fuzzy_cutoff?: number;
}


export const FeedsConfig = () => {
    const [config, setConfig] = useState<FeedsConfig>({});

    const getConfig = async () => {
        let resp = await fetch("/api/v1/config/feeds");
        if (resp.ok) {
            let data = await resp.json();
            setConfig(data.result);
        }
    }

    const updateConfig = async (key: string, value: any) => {
        let request = {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                [key]: value
            })
        };

        let resp = await fetch("/api/v1/config/feeds", request);
        if (resp.ok) {
            let data = await resp.json();
            setConfig(data.result);
        }
    }

    useEffect(() => {
        getConfig();
    }, []);

    const inputPollingInterval = async (e: Event) => {
        updateConfig("polling_interval", (e.target as HTMLInputElement).value);
    }

    const inputCompleteCheck = async (e: Event) => {
        updateConfig("complete_check_interval", (e.target as HTMLInputElement).value);
    }

    const inputFuzzyCutoff = async (e: Event) => {
        updateConfig("fuzzy_cutoff", (e.target as HTMLInputElement).value);
    }

    return (
        <div class="box">
            <div class="columns">
                <div class="column is-3">
                    <h1 class="title is-5">{_("feeds-fuzzy-cutoff-title")}</h1>
                    <h2 class="subtitle is-6">{_("feeds-fuzzy-cutoff-subtitle")}</h2>
                    <div class="field has-addons">
                        <div class="control">
                            <input class="input" type="number" min="0" max="100" placeholder="90" value={config.fuzzy_cutoff} onChange={inputFuzzyCutoff} />
                        </div>
                        <div class="control">
                            <a class="button is-static">%</a>
                        </div>
                    </div>
                </div>
                <div class="column is-3">
                    <h1 class="title is-5"><span class="has-tooltip-bottom has-tooltip-multiline" data-tooltip={_("feeds-pollinginterval-tooltip")}>{_("feeds-pollinginterval-title")}</span></h1>
                    <h2 class="subtitle is-6">{_("feeds-pollinginterval-subtitle")}</h2>
                    <div class="field has-addons">
                        <div class="control">
                            <input class="input" type="number" min="30" placeholder="900" value={config.polling_interval} onChange={inputPollingInterval} />
                        </div>
                        <div class="control">
                            <a class="button is-static">{_("seconds-suffix")}</a>
                        </div>
                    </div>
                </div>
                <div class="column is-4">
                    <h1 class="title is-5">{_("feeds-completioncheck-title")}</h1>
                    <h2 class="subtitle is-6">{_("feeds-completioncheck-subtitle")}</h2>
                    <div class="field has-addons">
                        <div class="control">
                            <input class="input" type="number" min="1" placeholder="15" value={config.complete_check_interval} onChange={inputCompleteCheck} />
                        </div>
                        <div class="control">
                            <a class="button is-static">{_("seconds-suffix")}</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
