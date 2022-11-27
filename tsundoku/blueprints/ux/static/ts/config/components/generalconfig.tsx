import { useEffect, useState } from "preact/hooks";
import { GeneralConfig } from "../../interfaces";
import { getInjector } from "../../fluent";


let resources = [
    "config",
    "logs"
];

const _ = getInjector(resources);


export const GeneralConfigApp = () => {
    const [config, setConfig] = useState<GeneralConfig>({});

    const getConfig = async () => {
        let resp = await fetch("/api/v1/config/general");
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

        let resp = await fetch("/api/v1/config/general", request);
        if (resp.ok) {
            let data = await resp.json();
            setConfig(data.result);
        }
    }

    useEffect(() => {
        getConfig();
    }, []);

    const inputHost = (e: Event) => {
        updateConfig("host", (e.target as HTMLInputElement).value);
    }

    const inputPort = (e: Event) => {
        updateConfig("port", (e.target as HTMLInputElement).value);
    }

    const inputUpdateCheck = (e: Event) => {
        if ((e.target as HTMLInputElement).checked)
            updateConfig("update_do_check", true);
        else
            updateConfig("update_do_check", false);
    }

    const inputLocale = (e: Event) => {
        let target = e.target as HTMLSelectElement;

        updateConfig("locale", target.options[target.selectedIndex].value);
    }

    const inputLogLevel = (e: Event) => {
        let target = e.target as HTMLSelectElement;

        updateConfig("log_level", target.options[target.selectedIndex].value);
    }

    const inputDefaultDesiredFormat = (e: Event) => {
        updateConfig("default_desired_format", (e.target as HTMLInputElement).value);
    }

    const inputDefaultDesiredFolder = (e: Event) => {
        updateConfig("default_desired_folder", (e.target as HTMLInputElement).value);
    }

    const inputUnwatchWhenFinished = (e: Event) => {
        if ((e.target as HTMLInputElement).checked)
            updateConfig("unwatch_when_finished", true);
        else
            updateConfig("unwatch_when_finished", false);
    }

    return (
        <div class="box">
            <div class="columns is-multiline">
                <div class="column is-3">
                    <h1 class="title is-5"><span class="has-tooltip-bottom" data-tooltip={_("general-host-tooltip")}>{_("general-host-title")}</span></h1>
                    <h2 class="subtitle is-6">{_("general-host-subtitle")}</h2>
                    <div class="field has-addons">
                        <div class="control is-expanded">
                            <input class="input" type="text" placeholder="localhost" value={config.host} onChange={inputHost} />
                        </div>
                        <div class="control">
                            <input class="input" type="number" placeholder="6439" min="1" max="65535" value={config.port} onChange={inputPort} />
                        </div>
                    </div>
                </div>
                <div class="column is-3">
                    <h1 class="title is-5">{_("general-loglevel-title")}</h1>
                    <h2 class="subtitle is-6">{_("general-loglevel-subtitle")}</h2>
                    <div class="select is-fullwidth">
                        <select onChange={inputLogLevel}>
                            <option value="error" selected={config.log_level === "error"}>{_("log-level-error")}</option>
                            <option value="warning" selected={config.log_level === "warning"}>{_("log-level-warning")}</option>
                            <option value="info" selected={config.log_level === "info"}>{_("log-level-info")}</option>
                            <option value="debug" selected={config.log_level === "debug"}>{_("log-level-debug")}</option>
                        </select>
                    </div>
                </div>
                <div class="column is-3">
                    <h1 class="title is-5"><span class="has-tooltip-bottom" data-tooltip={_("general-locale-tooltip")}>{_("general-locale-title")}</span></h1>
                    <h2 class="subtitle is-6">{_("general-locale-subtitle")}</h2>
                    <div class="select is-fullwidth">
                        <select onChange={inputLocale}>
                            <option value="en" selected={config.locale === "en"}>English</option>
                            <option value="ru" selected={config.locale === "ru"}>русский</option>
                        </select>
                    </div>
                </div>
                <div class="column is-3">
                    <h1 class="title is-5"><span class="has-tooltip-bottom" data-tooltip={_("general-updatecheck-tooltip")}>{_("general-updatecheck-title")}</span></h1>
                    <h2 class="subtitle is-6">{_("general-updatecheck-subtitle")}</h2>
                    <div class="field">
                        <input id="updateCheck" type="checkbox" class="switch" checked={config.update_do_check} onChange={inputUpdateCheck} />
                        <label for="updateCheck">{_("checkbox-enabled")}</label>
                    </div>
                </div>
                <div class="column is-4">
                    <h1 class="title is-5"><span class="has-tooltip-bottom">{_("general-defaultformat-title")}</span></h1>
                    <h2 class="subtitle is-6">{_("general-defaultformat-subtitle")}</h2>
                    <input class="input" type="text" value={config.default_desired_format} onChange={inputDefaultDesiredFormat} />
                </div>
                <div class="column is-4">
                <h1 class="title is-5"><span class="has-tooltip-bottom">{_("general-defaultfolder-title")}</span></h1>
                    <h2 class="subtitle is-6">{_("general-defaultfolder-subtitle")}</h2>
                    <input class="input" type="text" value={config.default_desired_folder} onChange={inputDefaultDesiredFolder} />
                </div>
                <div class="column is-4">
                    <h1 class="title is-5">{_("general-unwatchfinished-title")}</h1>
                    <h2 class="subtitle is-6">{_("general-unwatchfinished-subtitle")}</h2>
                    <div class="field">
                        <input id="unwatchCheck" type="checkbox" class="switch" checked={config.unwatch_when_finished} onChange={inputUnwatchWhenFinished} />
                        <label for="unwatchCheck">{_("checkbox-enabled")}</label>
                    </div>
                </div>
            </div>
        </div>
    )
}
