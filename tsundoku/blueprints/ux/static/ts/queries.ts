import { APIResponse, GeneralConfig } from "./interfaces";


export const fetchConfigGeneral = async (): Promise<GeneralConfig> => {
    let request = {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    };

    let response = await fetch("/api/v1/config/general", request);
    if (!response.ok)
        throw new Error(`${response.status}: ${response.statusText}}`);

    let data: APIResponse<GeneralConfig> = await response.json();
    return data.result;
}
