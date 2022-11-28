import { APIResponse, Show } from "./interfaces";


export const fetchConfig = async <ConfigType>(config: string): Promise<ConfigType> => {
    let request = {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    };

    let response = await fetch(`/api/v1/config/${config}`, request);
    if (!response.ok)
        throw new Error(`${response.status}: ${response.statusText}}`);

    let data: APIResponse<ConfigType> = await response.json();
    return data.result;
}

export const setConfig = async <ConfigType>(config: string, key: string, value: string): Promise<ConfigType> => {
    let request = {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            [key]: value
        })
    };

    let resp = await fetch(`/api/v1/config/${config}`, request);
    if (resp.ok) {
        let data: APIResponse<ConfigType> = await resp.json();
        return data.result;
    }

    throw new Error(`Failed to set config, ${resp.status}: ${resp.statusText}`);
}
