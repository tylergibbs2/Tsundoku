import "bulma-extensions/dist/css/bulma-extensions.min.css";
import React, { ChangeEvent, EventHandler, useEffect, useState } from "react";
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
    timed_encoding?: boolean;
    hour_start?: number;
    hour_end?: number;
    has_ffmpeg?: boolean;
}


interface EncodeStats {
    total_encoded?: number;
    total_saved_bytes?: number;
    avg_saved_bytes?: number;
    median_time_spent_hours?: number;
    avg_time_spent_hours?: number;
}


export const PostProcessing = () => {
    const [config, setConfig] = useState<EncodeConfig>({});
    const [encodeStats, setEncodeStats] = useState<EncodeStats>({});

    const getConfig = async () => {
        let resp = await fetch("/api/v1/config/encode");
        if (resp.ok) {
            let data = await resp.json();
            setConfig(data.result);
        }
    }

    const getEncodingStats = async () => {
        let resp = await fetch("/api/v1/config/encode/stats");
        if (resp.ok) {
            let data = await resp.json();
            setEncodeStats(data.result);
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
        getEncodingStats();
    }, []);

    const inputEnabled = (e: React.MouseEvent<HTMLInputElement>): void => {
        if (e.currentTarget.checked)
            updateConfig("enabled", true);
        else
            updateConfig("enabled", false);
    }

    return (
        <>
            <div className="field">
                <input id="enableEncode" type="checkbox" className="switch" onClick={inputEnabled} checked={config.enabled && config.has_ffmpeg} disabled={!config.has_ffmpeg} />
                <label htmlFor="enableEncode">{_("checkbox-enabled")}</label>
                {!config.has_ffmpeg &&
                    <span className="tag is-danger ml-1">{_("ffmpeg-missing")}</span>
                }
            </div>
            <PostProcessingForm
                config={config}
                stats={encodeStats}
                updateConfig={updateConfig}
            />
        </>
    )
}

interface PostProcessingFormParams {
    config: EncodeConfig;
    stats: EncodeStats;
    updateConfig: any;
}

const PostProcessingForm = ({ config, stats, updateConfig }: PostProcessingFormParams) => {
    let disabled = !(config.enabled && config.has_ffmpeg);

    const inputMaxEncodes = (e: ChangeEvent<HTMLInputElement>) => {
        updateConfig("maximum_encodes", e.target.value);
    }

    const inputQualityValue = (e: ChangeEvent<HTMLInputElement>) => {
        let value = parseInt(e.target.value);
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

    const inputRetryFail = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked)
            updateConfig("retry_on_fail", true);
        else
            updateConfig("retry_on_fail", false);
    }

    const inputSpeedPreset = (e: ChangeEvent<HTMLSelectElement>) => {
        updateConfig("speed_preset", e.target.options[e.target.selectedIndex].value);
    }

    const inputHourStart = (e: ChangeEvent<HTMLSelectElement>) => {
        updateConfig("hour_start", e.target.options[e.target.selectedIndex].value);
    }

    const inputHourEnd = (e: ChangeEvent<HTMLSelectElement>) => {
        updateConfig("hour_end", e.target.options[e.target.selectedIndex].value);
    }

    const inputTimedEncoding = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked)
            updateConfig("timed_encoding", true);
        else
            updateConfig("timed_encoding", false);
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
        <div className="box">
            {Object.keys(stats).length > 0 &&
                <div className="columns">
                    <div className="column is-one-fifth">
                        <p>{_("encode-stats-total-encoded", { 'total_encoded': stats.total_encoded })}</p>
                    </div>
                    <div className="column is-one-fifth">
                        <p>{_("encode-stats-total-saved-gb", { 'total_saved_gb': (stats.total_saved_bytes / (1024 ** 3)).toFixed(1) })}</p>
                    </div>
                    <div className="column is-one-fifth">
                        <p>{_("encode-stats-avg-saved-mb", { 'avg_saved_mb': (stats.avg_saved_bytes / (1024 ** 2)).toFixed(1) })}</p>
                    </div>
                    <div className="column is-one-fifth">
                        <p>{_("encode-stats-median-time-hours", { 'median_time_hours': stats.median_time_spent_hours.toFixed(2) })}</p>
                    </div>
                    <div className="column is-one-fifth">
                        <p>{_("encode-stats-avg-time-hours", { 'avg_time_hours': stats.avg_time_spent_hours.toFixed(2) })}</p>
                    </div>
                </div>
            }
            <div className="columns">
                <div className="column is-half">
                    <h1 className="title is-5">{_("process-quality-title")}</h1>
                    <h2 className="subtitle is-6">{_("process-quality-subtitle")}</h2>
                    <div className="columns is-fullwidth mb-0">
                        <div className="column">
                            <strong title={`CRF 24 (${_("encode-quality-low-desc")})`}>{_("encode-quality-low")}</strong>
                        </div>
                        <div className="column has-text-centered">
                            <strong title={`CRF 21 (${_("encode-quality-moderate-desc")})`}>{_("encode-quality-moderate")}</strong>
                        </div>
                        <div className="column" style={{ textAlign: "right" }}>
                            <strong title={`CRF 18 (${_("encode-quality-high-desc")})`}>{_("encode-quality-high")}</strong>
                        </div>
                    </div>
                    <input className="slider is-fullwidth is-info mt-0" step="1" min="0" max="2" type="range" disabled={disabled} value={getQualityValue()} onChange={inputQualityValue}></input>
                </div>
                <div className="column is-half">
                    <h1 className="title is-5">{_("process-speed-title")}</h1>
                    <h2 className="subtitle is-6">{_("process-speed-subtitle")}</h2>
                    <div className="select is-fullwidth is-vcentered">
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
            <div className="columns">
                <div className="column is-one-third">
                    <h1 className="title is-5">{_("process-max-encode-title")}</h1>
                    <h2 className="subtitle is-6 mb-3">{_("process-max-encode-subtitle")}</h2>
                    <input className="input" type="number" min="1" value={config.maximum_encodes} onChange={inputMaxEncodes} disabled={disabled}></input>
                </div>
                <div className="column is-one-third">
                    <h1 className="title is-5">{_("encode-time-title")}</h1>
                    <h2 className="subtitle is-6">{_("encode-time-subtitle")}</h2>
                    <div className="columns is-vcentered">
                        <div className="column">
                            <div className="field is-vcentered">
                                <input id="timeCheck" type="checkbox" className="switch" onChange={inputTimedEncoding} checked={config.timed_encoding} disabled={disabled} />
                                <label htmlFor="timeCheck">{_("checkbox-enabled")}</label>
                            </div>
                        </div>
                        <div className="column">
                            <div className="select is-fullwidth is-vcentered">
                                <select onChange={inputHourStart} disabled={disabled}>
                                    {
                                        [...Array(24).keys()].map(hour => {
                                            if (hour >= config.hour_end) return;
                                            return <option value={hour.toString()} selected={config.hour_start === hour}>{_(`hour-${hour}`)}</option>
                                        })
                                    }
                                </select>
                            </div>
                        </div>
                        <div className="column">
                            <div className="select is-fullwidth is-vcentered ml-1">
                                <select onChange={inputHourEnd} disabled={disabled}>
                                    {
                                        [...Array(24).keys()].map(hour => {
                                            if (hour <= config.hour_start) return;
                                            return <option value={hour.toString()} selected={config.hour_end === hour}>{_(`hour-${hour}`)}</option>
                                        })
                                    }
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="column is-one-third">
                    <h1 className="title is-5">{_("process-retry-title")}</h1>
                    <h2 className="subtitle is-6">{_("process-retry-subtitle")}</h2>
                    <div className="field">
                        <input id="retryCheck" type="checkbox" className="switch" onChange={inputRetryFail} checked={config.retry_on_fail} disabled={disabled} />
                        <label htmlFor="retryCheck">{_("checkbox-enabled")}</label>
                    </div>
                </div>
            </div>
        </div>
    )
}