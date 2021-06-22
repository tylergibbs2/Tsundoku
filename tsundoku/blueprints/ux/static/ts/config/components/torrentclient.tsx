import { useEffect, useState } from "preact/hooks";
import { getInjector } from "../../fluent";


let resources = [
    "config",
    "logs"
];

const _ = getInjector(resources);


interface TorrentConfig {
    client?: string;
    host?: string;
    port?: number;
    username?: string;
    password?: string;
    secure?: boolean;
}


export const TorrentConfig = () => {
    const [config, setConfig] = useState<TorrentConfig>({});

    const [fetchingStatus, setFetchingStatus] = useState<boolean>(false);
    const [clientStatus, setClientStatus] = useState<boolean>(null);

    const testTorrentConnection = async () => {
        if (fetchingStatus)
            return;

        setFetchingStatus(true);

        let resp = await fetch("/api/v1/config/torrent/test");
        if (resp.ok) {
            let data = await resp.json();
            setClientStatus(data.result);
        } else {
            setClientStatus(false);
        }

        setFetchingStatus(false);
    }

    const getConfig = async () => {
        let resp = await fetch("/api/v1/config/torrent");
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

        let resp = await fetch("/api/v1/config/torrent", request);
        if (resp.ok) {
            let data = await resp.json();
            setConfig(data.result);
        }
    }

    useEffect(() => {
        getConfig();
    }, []);

    const inputClient = (e: Event) => {
        let target = e.target as HTMLSelectElement;

        setClientStatus(null);
        updateConfig("client", target.options[target.selectedIndex].value);
    }

    const inputHost = async (e: Event) => {
        setClientStatus(null);
        updateConfig("host", (e.target as HTMLInputElement).value);
    }

    const inputPort = async (e: Event) => {
        setClientStatus(null);
        updateConfig("port", (e.target as HTMLInputElement).value);
    }

    const inputUsername = async (e: Event) => {
        setClientStatus(null);
        updateConfig("username", (e.target as HTMLInputElement).value);
    }

    const inputPassword = async (e: Event) => {
        setClientStatus(null);
        updateConfig("password", (e.target as HTMLInputElement).value);
    }

    const inputSecure = async (e: Event) => {
        setClientStatus(null);
        if ((e.target as HTMLInputElement).checked)
            updateConfig("secure", true);
        else
            updateConfig("secure", false);
    }

    return (
        <div class="box">
            <div class="columns">
                <div class="column is-2">
                    <h1 class="title is-5">{_("torrent-client-title")}</h1>
                    <h2 class="subtitle is-6">{_("torrent-client-subtitle")}</h2>
                    <div class="select is-fullwidth">
                        <select onChange={inputClient}>
                            <option value="deluge" selected={config.client === "deluge"}>Deluge</option>
                            <option value="qbittorrent" selected={config.client === "qbittorrent"}>qBittorrent</option>
                        </select>
                    </div>
                </div>
                <div class="column is-3">
                    <h1 class="title is-5">{_("torrent-host-title")}</h1>
                    <h2 class="subtitle is-6">{_("torrent-host-subtitle")}</h2>
                    <div class="field has-addons">
                        <div class="control is-expanded">
                            <input class="input" type="text" placeholder="localhost" value={config.host} onChange={inputHost} />
                        </div>
                        <div class="control">
                            <input class="input" type="number" placeholder="8080" min="1" max="65535" value={config.port} onChange={inputPort} />
                        </div>
                    </div>
                </div>
                <div class="column is-2">
                    <h1 class="title is-5">{_("torrent-username-title")}</h1>
                    <h2 class="subtitle is-6">{_("torrent-username-subtitle")}</h2>
                    <input class="input" type="text" value={config.username} onChange={inputUsername} placeholder="admin" name="disableAuto" autoComplete="off" />
                </div>
                <div class="column is-2">
                    <h1 class="title is-5">{_("torrent-password-title")}</h1>
                    <h2 class="subtitle is-6">{_("torrent-password-subtitle")}</h2>
                    <input class="input" type="password" value={config.password} onChange={inputPassword} placeholder="********" name="disableAuto" autoComplete="off" />
                </div>
                <div class="column is-3">
                    <h1 class="title is-5">{_("torrent-secure-title")}</h1>
                    <h2 class="subtitle is-6">{_("torrent-secure-subtitle")}</h2>
                    <div class="field">
                        <input id="secureCheck" type="checkbox" class="switch" onChange={inputSecure} checked={config.secure} />
                        <label for="secureCheck">{_("checkbox-enabled")}</label>
                    </div>
                </div>
            </div>
            <div>
                <a onClick={testTorrentConnection} class={"button is-info " + (fetchingStatus ? "is-loading" : "")}>{_("config-test")}</a>
                <ConnectionStatus status={clientStatus} />
            </div>

        </div>
    )
}


interface ConnectionStatusParams {
    status?: boolean;
}


const ConnectionStatus = ({ status }: ConnectionStatusParams) => {
    if (status)
        return <span class="tag is-success mt-2 ml-2">{_("config-test-success")}</span>;
    else if (status === false)
        return <span class="tag is-danger mt-2 ml-2">{_("config-test-failure")}</span>;
    else
        return <></>;
}
