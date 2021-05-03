import { useEffect, useState } from "preact/hooks";

import { getInjector } from "../../fluent";
import { IonIcon } from "../../icon";


let resources = [
    "config"
];

const _ = getInjector(resources);

export const APITokenComponent = () => {
    const [localToken, setLocalToken] = useState<string | null>(null);
    const [isFetching, setIsFetching] = useState<boolean>(false);

    const getToken = async () => {
        setIsFetching(true);

        let request = {
            method: "GET"
        };

        let resp = await fetch("/api/v1/config/token", request);
        let resp_json: any;
        if (resp.ok)
            resp_json = await resp.json();
        else
            return;

        setLocalToken(resp_json.result);
        setIsFetching(false);
    }

    const setToken = async () => {
        setIsFetching(true);

        let request = {
            method: "POST"
        };

        let resp = await fetch("/api/v1/config/token", request);
        let resp_json: any;
        if (resp.ok)
            resp_json = await resp.json();
        else
            return;

        setLocalToken(resp_json.result);
        setIsFetching(false);
    }

    useEffect(() => {
        getToken();
    }, [])

    return (
        <div class="field has-addons">
            <div class="control is-expanded">
                <input class="input" type="text" readonly={true} value={localToken} />
            </div>
            <div class="control">
                <button onClick={setToken} title={_("api-key-refresh")} class={"button is-danger " + (isFetching ? "is-loading" : "")}>
                    <span class="icon">
                        <IonIcon name="refresh" />
                    </span>
                </button>
            </div>
        </div>
    )
}
