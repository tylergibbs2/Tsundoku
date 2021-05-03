import "bulma-extensions/dist/css/bulma-extensions.min.css";
import { useEffect, useState } from "preact/hooks";
import { getInjector } from "../../fluent";


let resources = [
    "config"
];

const _ = getInjector(resources);


interface EncodeConfig {
    enabled?: boolean;
    quality_preset?: string;
    speed_preset?: string;
    maximum_encodes?: number;
    retry_on_fail?: boolean;
    has_ffmpeg?: boolean;
}


export const PostProcessing = () => {
    const [config, setConfig] = useState<EncodeConfig>({});

    const getConfig = async () => {
        let resp = await fetch("/api/v1/config/encode");
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

        let resp = await fetch("/api/v1/config/encode", request);
        if (resp.ok) {
            let data = await resp.json();
            setConfig(data.result);
        }
    }

    useEffect(() => {
        getConfig();
    }, []);

    const inputEnabled = (e: Event) => {
        if ((e.target as HTMLInputElement).checked)
            updateConfig("enabled", true);
        else
            updateConfig("enabled", false);
    }

    return (
        <>
            <div class="field">
                <input id="enableEncode" type="checkbox" class="switch" onClick={inputEnabled} checked={config.enabled && config.has_ffmpeg} disabled={!config.has_ffmpeg} />
                <label for="enableEncode">{_("checkbox-enabled")}</label>
                {!config.has_ffmpeg &&
                    <span class="tag is-danger ml-1">{_("ffmpeg-missing")}</span>
                }
            </div>
            <PostProcessingForm
                config={config}
                updateConfig={updateConfig}
            />
        </>
    )
}

interface PostProcessingFormParams {
    config: EncodeConfig;
    updateConfig: any;
}

const PostProcessingForm = ({ config, updateConfig }: PostProcessingFormParams) => {
    let disabled = !(config.enabled && config.has_ffmpeg);

    const inputMaxEncodes = (e: Event) => {
        updateConfig("maximum_encodes", (e.target as HTMLInputElement).value);
    }

    const inputQualityValue = (e: Event) => {
        let value = parseInt((e.target as HTMLInputElement).value);
        let preset: string;
        switch (value) {
            case 2:
                preset = "high";
                break;
            case 1:
                preset = "moderate";
                break;
            default:
                preset = "low";
        }

        updateConfig("quality_preset", preset);
    }

    const inputRetryFail = (e: Event) => {
        if ((e.target as HTMLInputElement).checked)
            updateConfig("retry_on_fail", true);
        else
            updateConfig("retry_on_fail", false);
    }

    const inputSpeedPreset = (e: Event) => {
        let target = e.target as HTMLSelectElement;

        updateConfig("speed_preset", target.options[target.selectedIndex].value);
    }

    const getQualityValue = () => {
        switch (config.quality_preset) {
            case "high":
                return 2;
            case "moderate":
                return 1;
            default:
                return 0;
        }
    }

    return (
        <div class="box">
            <form>
                <div class="columns">
                    <div class="column is-half">
                        <h1 class="title is-5">{_("process-quality-title")}</h1>
                        <h2 class="subtitle is-6">{_("process-quality-subtitle")}</h2>
                        <div class="columns is-fullwidth mb-0">
                            <div class="column">
                                <strong title={`CRF 26 (${_("encode-quality-low-desc")})`}>{_("encode-quality-low")}</strong>
                            </div>
                            <div class="column has-text-centered">
                                <strong title={`CRF 22 (${_("encode-quality-moderate-desc")})`}>{_("encode-quality-moderate")}</strong>
                            </div>
                            <div class="column" style={{ textAlign: "right" }}>
                                <strong title={`CRF 18 (${_("encode-quality-high-desc")})`}>{_("encode-quality-high")}</strong>
                            </div>
                        </div>
                        <input class="slider is-fullwidth is-info mt-0" step="1" min="0" max="2" type="range" disabled={disabled} value={getQualityValue()} onChange={inputQualityValue}></input>
                    </div>
                    <div class="column is-half">
                        <h1 class="title is-5">{_("process-speed-title")}</h1>
                        <h2 class="subtitle is-6">{_("process-speed-subtitle")}</h2>
                        <div class="select is-fullwidth is-vcentered">
                            <select onChange={inputSpeedPreset} disabled={disabled}>
                                <option value="ultrafast" selected={config.speed_preset === "ultrafast"}>{_("encode-speed-ultrafast")}</option>
                                <option value="superfast" selected={config.speed_preset === "superfast"}>{_("encode-speed-superfast")}</option>
                                <option value="veryfast" selected={config.speed_preset === "veryfast"}>{_("encode-speed-veryfast")}</option>
                                <option value="faster" selected={config.speed_preset === "faster"}>{_("encode-speed-faster")}</option>
                                <option value="fast" selected={config.speed_preset === "fast"}>{_("encode-speed-fast")}</option>
                                <option value="medium" selected={config.speed_preset === "medium"}>{_("encode-speed-medium")}</option>
                                <option value="slow" selected={config.speed_preset === "slow"}>{_("encode-speed-slow")}</option>
                                <option value="slower" selected={config.speed_preset === "slower"}>{_("encode-speed-slower")}</option>
                                <option value="veryslow" selected={config.speed_preset === "veryslow"}>{_("encode-speed-veryslow")}</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="columns">
                    <div class="column is-one-half">
                        <h1 class="title is-5">{_("process-max-encode-title")}</h1>
                        <h2 class="subtitle is-6 mb-3">{_("process-max-encode-subtitle")}</h2>
                        <input class="input" type="number" min="1" value={config.maximum_encodes} onChange={inputMaxEncodes} style={{ width: "50%" }} disabled={disabled}></input>
                    </div>
                    <div class="column is-one-half">
                        <h1 class="title is-5">{_("process-retry-title")}</h1>
                        <h2 class="subtitle is-6">{_("process-retry-subtitle")}</h2>
                        <div class="field">
                            <input id="retryCheck" type="checkbox" class="switch" onChange={inputRetryFail} checked={config.retry_on_fail} disabled={disabled} />
                            <label for="retryCheck">{_("checkbox-enabled")}</label>
                        </div>
                    </div>
                </div>
            </form>
        </div>
    )
}