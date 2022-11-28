import { ChangeEvent, useEffect, useState } from "react";
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

    const inputHost = (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("host", e.target.value);
    }

    const inputPort = (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("port", e.target.value);
    }

    const inputUpdateCheck = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked)
            updateConfig("update_do_check", true);
        else
            updateConfig("update_do_check", false);
    }

    const inputLocale = (e: ChangeEvent<HTMLSelectElement>) => {
        updateConfig("locale", e.target.options[e.target.selectedIndex].value);
    }

    const inputLogLevel = (e: ChangeEvent<HTMLSelectElement>) => {
        updateConfig("log_level", e.target.options[e.target.selectedIndex].value);
    }

    const inputDefaultDesiredFormat = (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("default_desired_format", e.target.value);
    }

    const inputDefaultDesiredFolder = (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("default_desired_folder", e.target.value);
    }

    const inputUnwatchWhenFinished = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked)
            updateConfig("unwatch_when_finished", true);
        else
            updateConfig("unwatch_when_finished", false);
    }

    return (
        <div className="box">
            <div className="columns is-multiline">
                <div className="column is-3">
                    <h1 className="title is-5"><span className="has-tooltip-bottom" data-tooltip={_("general-host-tooltip")}>{_("general-host-title")}</span></h1>
                    <h2 className="subtitle is-6">{_("general-host-subtitle")}</h2>
                    <div className="field has-addons">
                        <div className="control is-expanded">
                            <input className="input" type="text" placeholder="localhost" value={config.host} onChange={inputHost} />
                        </div>
                        <div className="control">
                            <input className="input" type="number" placeholder="6439" min="1" max="65535" value={config.port} onChange={inputPort} />
                        </div>
                    </div>
                </div>
                <div className="column is-3">
                    <h1 className="title is-5">{_("general-loglevel-title")}</h1>
                    <h2 className="subtitle is-6">{_("general-loglevel-subtitle")}</h2>
                    <div className="select is-fullwidth">
                        <select onChange={inputLogLevel}>
                            <option value="error" selected={config.log_level === "error"}>{_("log-level-error")}</option>
                            <option value="warning" selected={config.log_level === "warning"}>{_("log-level-warning")}</option>
                            <option value="info" selected={config.log_level === "info"}>{_("log-level-info")}</option>
                            <option value="debug" selected={config.log_level === "debug"}>{_("log-level-debug")}</option>
                        </select>
                    </div>
                </div>
                <div className="column is-3">
                    <h1 className="title is-5"><span className="has-tooltip-bottom" data-tooltip={_("general-locale-tooltip")}>{_("general-locale-title")}</span></h1>
                    <h2 className="subtitle is-6">{_("general-locale-subtitle")}</h2>
                    <div className="select is-fullwidth">
                        <select onChange={inputLocale}>
                            <option value="en" selected={config.locale === "en"}>English</option>
                            <option value="ru" selected={config.locale === "ru"}>русский</option>
                        </select>
                    </div>
                </div>
                <div className="column is-3">
                    <h1 className="title is-5"><span className="has-tooltip-bottom" data-tooltip={_("general-updatecheck-tooltip")}>{_("general-updatecheck-title")}</span></h1>
                    <h2 className="subtitle is-6">{_("general-updatecheck-subtitle")}</h2>
                    <div className="field">
                        <input id="updateCheck" type="checkbox" className="switch" checked={config.update_do_check} onChange={inputUpdateCheck} />
                        <label htmlFor="updateCheck">{_("checkbox-enabled")}</label>
                    </div>
                </div>
                <div className="column is-4">
                    <h1 className="title is-5"><span className="has-tooltip-bottom">{_("general-defaultformat-title")}</span></h1>
                    <h2 className="subtitle is-6">{_("general-defaultformat-subtitle")}</h2>
                    <input className="input" type="text" value={config.default_desired_format} onChange={inputDefaultDesiredFormat} />
                </div>
                <div className="column is-4">
                <h1 className="title is-5"><span className="has-tooltip-bottom">{_("general-defaultfolder-title")}</span></h1>
                    <h2 className="subtitle is-6">{_("general-defaultfolder-subtitle")}</h2>
                    <input className="input" type="text" value={config.default_desired_folder} onChange={inputDefaultDesiredFolder} />
                </div>
                <div className="column is-4">
                    <h1 className="title is-5">{_("general-unwatchfinished-title")}</h1>
                    <h2 className="subtitle is-6">{_("general-unwatchfinished-subtitle")}</h2>
                    <div className="field">
                        <input id="unwatchCheck" type="checkbox" className="switch" checked={config.unwatch_when_finished} onChange={inputUnwatchWhenFinished} />
                        <label htmlFor="unwatchCheck">{_("checkbox-enabled")}</label>
                    </div>
                </div>
            </div>
        </div>
    )
}
