import React, { ChangeEvent, useEffect, useState } from "react";
import {
  UseMutateFunction,
  useMutation,
  useQuery,
  useQueryClient,
} from "react-query";
import { getInjector } from "../../fluent";
import { MutateConfigVars } from "../../interfaces";
import { fetchConfig, setConfig } from "../../queries";

import "bulma-extensions/dist/css/bulma-extensions.min.css";
import { GlobalLoading } from "../../Components/GlobalLoading";

const _ = getInjector();

interface EncodeConfig {
  enabled?: boolean;
  quality_preset?: string;
  speed_preset?: string;
  maximum_encodes?: number;
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
  const queryClient = useQueryClient();

  const config = useQuery(["config", "encode"], async () => {
    return await fetchConfig<EncodeConfig>("encode");
  });

  const mutation = useMutation(
    async ({ key, value }: MutateConfigVars) => {
      return await setConfig<EncodeConfig>("encode", key, value);
    },
    {
      onSuccess: (newConfig) => {
        queryClient.setQueryData(["config", "encode"], newConfig);
      },
    }
  );

  const [encodeStats, setEncodeStats] = useState<EncodeStats>({});

  const getEncodingStats = async () => {
    let resp = await fetch("/api/v1/config/encode/stats");
    if (resp.ok) {
      let data = await resp.json();
      setEncodeStats(data.result);
    }
  };

  useEffect(() => {
    getEncodingStats();
  }, []);

  if (config.isLoading) return <GlobalLoading heightTranslation="none" />;

  const inputEnabled = (e: React.MouseEvent<HTMLInputElement>): void => {
    if (e.currentTarget.checked)
      mutation.mutate({ key: "enabled", value: true });
    else mutation.mutate({ key: "enabled", value: false });
  };

  return (
    <>
      <div className="field">
        <input
          id="enableEncode"
          type="checkbox"
          className="switch"
          onClick={inputEnabled}
          defaultChecked={config.data?.enabled && config.data?.has_ffmpeg}
          disabled={!config.data?.has_ffmpeg}
        />
        <label htmlFor="enableEncode">{_("checkbox-enabled")}</label>
        {!config.data?.has_ffmpeg && (
          <span className="tag is-danger ml-1">{_("ffmpeg-missing")}</span>
        )}
      </div>
      <PostProcessingForm
        config={config.data}
        stats={encodeStats}
        updateConfig={mutation.mutate}
      />
    </>
  );
};

interface PostProcessingFormParams {
  config: EncodeConfig;
  stats: EncodeStats;
  updateConfig: UseMutateFunction<EncodeConfig, any, MutateConfigVars, any>;
}

const PostProcessingForm = ({
  config,
  stats,
  updateConfig,
}: PostProcessingFormParams) => {
  let disabled = !(config.enabled && config.has_ffmpeg);

  const inputMaxEncodes = (e: ChangeEvent<HTMLInputElement>) => {
    updateConfig({ key: "maximum_encodes", value: e.target.value });
  };

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

    updateConfig({ key: "quality_preset", value: preset });
  };

  const inputSpeedPreset = (e: ChangeEvent<HTMLSelectElement>) => {
    updateConfig({
      key: "speed_preset",
      value: e.target.options[e.target.selectedIndex].value,
    });
  };

  const inputHourStart = (e: ChangeEvent<HTMLSelectElement>) => {
    updateConfig({
      key: "hour_start",
      value: e.target.options[e.target.selectedIndex].value,
    });
  };

  const inputHourEnd = (e: ChangeEvent<HTMLSelectElement>) => {
    updateConfig({
      key: "hour_end",
      value: e.target.options[e.target.selectedIndex].value,
    });
  };

  const inputTimedEncoding = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) updateConfig({ key: "timed_encoding", value: true });
    else updateConfig({ key: "timed_encoding", value: false });
  };

  const getQualityValue = () => {
    switch (config.quality_preset) {
      case "high":
        return 2;
      case "moderate":
        return 1;
      default:
        return 0;
    }
  };

  return (
    <div className="box">
      {Object.keys(stats).length > 0 && (
        <div className="columns">
          <div className="column is-one-fifth my-auto">
            <p>
              {_("encode-stats-total-encoded", {
                total_encoded: stats.total_encoded,
              })}
            </p>
          </div>
          <div className="column is-one-fifth my-auto">
            <p>
              {_("encode-stats-total-saved-gb", {
                total_saved_gb: (stats.total_saved_bytes / 1024 ** 3).toFixed(
                  1
                ),
              })}
            </p>
          </div>
          <div className="column is-one-fifth my-auto">
            <p>
              {_("encode-stats-avg-saved-mb", {
                avg_saved_mb: (stats.avg_saved_bytes / 1024 ** 2).toFixed(1),
              })}
            </p>
          </div>
          <div className="column is-one-fifth my-auto">
            <p>
              {_("encode-stats-median-time-hours", {
                median_time_hours: stats.median_time_spent_hours.toFixed(2),
              })}
            </p>
          </div>
          <div className="column is-one-fifth my-auto">
            <p>
              {_("encode-stats-avg-time-hours", {
                avg_time_hours: stats.avg_time_spent_hours.toFixed(2),
              })}
            </p>
          </div>
        </div>
      )}
      <div className="columns">
        <div className="column is-half my-auto">
          <h1 className="title is-5">{_("process-quality-title")}</h1>
          <h2 className="subtitle is-6">{_("process-quality-subtitle")}</h2>
          <div className="columns is-fullwidth mb-0">
            <div className="column">
              <strong title={`CRF 24 (${_("encode-quality-low-desc")})`}>
                {_("encode-quality-low")}
              </strong>
            </div>
            <div className="column has-text-centered">
              <strong title={`CRF 21 (${_("encode-quality-moderate-desc")})`}>
                {_("encode-quality-moderate")}
              </strong>
            </div>
            <div className="column" style={{ textAlign: "right" }}>
              <strong title={`CRF 18 (${_("encode-quality-high-desc")})`}>
                {_("encode-quality-high")}
              </strong>
            </div>
          </div>
          <input
            className="slider is-fullwidth is-info mt-0"
            step="1"
            min="0"
            max="2"
            type="range"
            disabled={disabled}
            defaultValue={getQualityValue()}
            onChange={inputQualityValue}
          ></input>
        </div>
        <div className="column is-half my-auto">
          <h1 className="title is-5">{_("process-speed-title")}</h1>
          <h2 className="subtitle is-6">{_("process-speed-subtitle")}</h2>
          <div className="select is-fullwidth is-vcentered">
            <select
              onChange={inputSpeedPreset}
              disabled={disabled}
              defaultValue={config?.speed_preset}
            >
              <option value="ultrafast">{_("encode-speed-ultrafast")}</option>
              <option value="superfast">{_("encode-speed-superfast")}</option>
              <option value="veryfast">{_("encode-speed-veryfast")}</option>
              <option value="faster">{_("encode-speed-faster")}</option>
              <option value="fast">{_("encode-speed-fast")}</option>
              <option value="medium">{_("encode-speed-medium")}</option>
              <option value="slow">{_("encode-speed-slow")}</option>
              <option value="slower">{_("encode-speed-slower")}</option>
              <option value="veryslow">{_("encode-speed-veryslow")}</option>
            </select>
          </div>
        </div>
      </div>
      <div className="columns">
        <div className="column is-one-third my-auto">
          <h1 className="title is-5">{_("process-max-encode-title")}</h1>
          <h2 className="subtitle is-6 mb-3">
            {_("process-max-encode-subtitle")}
          </h2>
          <input
            className="input"
            type="number"
            min="1"
            defaultValue={config.maximum_encodes}
            onChange={inputMaxEncodes}
            disabled={disabled}
          ></input>
        </div>
        <div className="column is-one-third my-auto">
          <h1 className="title is-5">{_("encode-time-title")}</h1>
          <h2 className="subtitle is-6">{_("encode-time-subtitle")}</h2>
          <div className="columns is-vcentered">
            <div className="column">
              <div className="field is-vcentered">
                <input
                  id="timeCheck"
                  type="checkbox"
                  className="switch"
                  onChange={inputTimedEncoding}
                  checked={config.timed_encoding}
                  disabled={disabled}
                />
                <label htmlFor="timeCheck">{_("checkbox-enabled")}</label>
              </div>
            </div>
            <div className="column">
              <div className="select is-fullwidth is-vcentered">
                <select
                  onChange={inputHourStart}
                  disabled={disabled}
                  defaultValue={config?.hour_start?.toString()}
                >
                  {[...Array(24).keys()].map((hour) => {
                    if (hour >= config.hour_end) return;
                    return (
                      <option key={hour} value={hour.toString()}>
                        {_(`hour-${hour}`)}
                      </option>
                    );
                  })}
                </select>
              </div>
            </div>
            <div className="column">
              <div className="select is-fullwidth is-vcentered ml-1">
                <select
                  onChange={inputHourEnd}
                  disabled={disabled}
                  defaultValue={config?.hour_end?.toString()}
                >
                  {[...Array(24).keys()].map((hour) => {
                    if (hour <= config.hour_start) return;
                    return (
                      <option key={hour} value={hour.toString()}>
                        {_(`hour-${hour}`)}
                      </option>
                    );
                  })}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
