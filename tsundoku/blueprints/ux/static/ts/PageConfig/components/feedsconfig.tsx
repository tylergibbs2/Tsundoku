import { ChangeEvent, useEffect, useState } from "react";
import { getInjector } from "../../fluent";


let resources = [
    "config"
];

const _ = getInjector(resources);


interface FeedsConfig {
    polling_interval?: number;
    complete_check_interval?: number;
    fuzzy_cutoff?: number;
    seed_ratio_limit?: number;
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

    const inputPollingInterval = async (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("polling_interval", e.target.value);
    }

    const inputCompleteCheck = async (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("complete_check_interval", e.target.value);
    }

    const inputFuzzyCutoff = async (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("fuzzy_cutoff", e.target.value);
    }

    const inputSeedRatioLimit = async (e: ChangeEvent<HTMLInputElement>) => {
        e.target.value = parseFloat(e.target.value).toFixed(2);

        updateConfig("seed_ratio_limit", e.target.value);
    }

    return (
        <div className="box">
            <div className="columns">
                <div className="column is-3">
                    <h1 className="title is-5">{_("feeds-fuzzy-cutoff-title")}</h1>
                    <h2 className="subtitle is-6">{_("feeds-fuzzy-cutoff-subtitle")}</h2>
                    <div className="field has-addons">
                        <div className="control">
                            <input className="input" type="number" min="0" max="100" placeholder="90" value={config.fuzzy_cutoff} onChange={inputFuzzyCutoff} />
                        </div>
                        <div className="control">
                            <a className="button is-static">%</a>
                        </div>
                    </div>
                </div>
                <div className="column is-3">
                    <h1 className="title is-5"><span className="has-tooltip-bottom has-tooltip-multiline" data-tooltip={_("feeds-pollinginterval-tooltip")}>{_("feeds-pollinginterval-title")}</span></h1>
                    <h2 className="subtitle is-6">{_("feeds-pollinginterval-subtitle")}</h2>
                    <div className="field has-addons">
                        <div className="control">
                            <input className="input" type="number" min="30" placeholder="900" value={config.polling_interval} onChange={inputPollingInterval} />
                        </div>
                        <div className="control">
                            <a className="button is-static">{_("seconds-suffix")}</a>
                        </div>
                    </div>
                </div>
                <div className="column is-3">
                    <h1 className="title is-5">{_("feeds-completioncheck-title")}</h1>
                    <h2 className="subtitle is-6">{_("feeds-completioncheck-subtitle")}</h2>
                    <div className="field has-addons">
                        <div className="control">
                            <input className="input" type="number" min="1" placeholder="15" value={config.complete_check_interval} onChange={inputCompleteCheck} />
                        </div>
                        <div className="control">
                            <a className="button is-static">{_("seconds-suffix")}</a>
                        </div>
                    </div>
                </div>
                <div className="column is-3">
                    <h1 className="title is-5">{_("feeds-seedratio-title")}</h1>
                    <h2 className="subtitle is-6">{_("feeds-seedratio-subtitle")}</h2>
                    <div className="field">
                        <div className="control">
                            <input className="input" type="number" min="0.0" placeholder="0.0" step="0.1" value={config.seed_ratio_limit?.toFixed(2)} onChange={inputSeedRatioLimit} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
