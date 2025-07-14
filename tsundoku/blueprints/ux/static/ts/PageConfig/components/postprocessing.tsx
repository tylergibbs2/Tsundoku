import React, {
  ChangeEvent,
  useEffect,
  useState,
  useImperativeHandle,
  forwardRef,
} from "react";
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

interface PostProcessingProps {
  onDirtyChange: (dirty: boolean) => void;
}

export const PostProcessing = forwardRef(
  ({ onDirtyChange }: PostProcessingProps, ref) => {
    const queryClient = useQueryClient();

    const config = useQuery(["config", "encode"], async () => {
      return await fetchConfig("encode");
    });

    const mutation = useMutation(
      async ({ key, value }: MutateConfigVars) => {
        return await setConfig("encode", key, value);
      },
      {
        onSuccess: (newConfig) => {
          queryClient.setQueryData(["config", "encode"], newConfig);
        },
      }
    );

    const [fields, setFields] = useState<any>({});
    const [dirty, setDirty] = useState(false);
    const [encodeStats, setEncodeStats] = useState<any>({});

    useEffect(() => {
      if (config.data && typeof config.data === "object") {
        setFields({ ...config.data });
        setDirty(false);
        onDirtyChange(false);
      }
    }, [config.data]);

    useEffect(() => {
      if (!config.data) return;
      const isDirty = Object.keys(fields).some(
        (key) => fields[key] !== config.data[key]
      );
      setDirty(isDirty);
      onDirtyChange(isDirty);
    }, [fields, config.data]);

    useImperativeHandle(ref, () => ({
      async save() {
        if (!dirty) return;
        const promises = Object.keys(fields).map((key) => {
          if (fields[key] !== config.data[key]) {
            return mutation.mutateAsync({ key, value: fields[key] });
          }
          return null;
        });
        await Promise.all(promises);
        setDirty(false);
        onDirtyChange(false);
      },
    }));

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

    const handleChange = (key: string, value: any) => {
      setFields((prev) => ({ ...prev, [key]: value }));
    };

    const disabled = !(fields.enabled && fields.has_ffmpeg);

    // Helper for quality value
    const getQualityValue = () => {
      switch (fields.quality_preset) {
        case "high":
          return 2;
        case "moderate":
          return 1;
        default:
          return 0;
      }
    };

    const encoderIsUnavailable = (encoder: string): boolean => {
      return !fields?.available_encoders?.includes(encoder);
    };

    return (
      <>
        <div className="field">
          <input
            id="enableEncode"
            type="checkbox"
            className="switch"
            checked={!!fields.enabled && fields.has_ffmpeg}
            onChange={(e) => handleChange("enabled", e.target.checked)}
            disabled={!fields.has_ffmpeg}
          />
          <label htmlFor="enableEncode">{_("checkbox-enabled")}</label>
          {!fields.has_ffmpeg && (
            <span className="tag is-danger ml-1">{_("ffmpeg-missing")}</span>
          )}
        </div>
        <div className="box">
          {Object.keys(encodeStats).length > 0 && (
            <div className="columns">
              <div className="column is-one-fifth my-auto">
                <p>
                  {_("encode-stats-total-encoded", {
                    total_encoded: encodeStats.total_encoded,
                  })}
                </p>
              </div>
              <div className="column is-one-fifth my-auto">
                <p>
                  {_("encode-stats-total-saved-gb", {
                    total_saved_gb: (
                      encodeStats.total_saved_bytes /
                      1024 ** 3
                    ).toFixed(1),
                  })}
                </p>
              </div>
              <div className="column is-one-fifth my-auto">
                <p>
                  {_("encode-stats-avg-saved-mb", {
                    avg_saved_mb: (
                      encodeStats.avg_saved_bytes /
                      1024 ** 2
                    ).toFixed(1),
                  })}
                </p>
              </div>
              <div className="column is-one-fifth my-auto">
                <p>
                  {_("encode-stats-median-time-hours", {
                    median_time_hours:
                      encodeStats.median_time_spent_hours?.toFixed(2),
                  })}
                </p>
              </div>
              <div className="column is-one-fifth my-auto">
                <p>
                  {_("encode-stats-avg-time-hours", {
                    avg_time_hours:
                      encodeStats.avg_time_spent_hours?.toFixed(2),
                  })}
                </p>
              </div>
            </div>
          )}
          <div className="columns">
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("process-max-title")}</h1>
              <h2 className="subtitle is-6">{_("process-max-subtitle")}</h2>
              <input
                className="input"
                type="number"
                value={fields.maximum_encodes ?? ""}
                onChange={(e) =>
                  handleChange("maximum_encodes", e.target.value)
                }
                disabled={disabled}
              />
            </div>
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("process-quality-title")}</h1>
              <h2 className="subtitle is-6">{_("process-quality-subtitle")}</h2>
              <input
                className="slider is-fullwidth"
                type="range"
                min="0"
                max="2"
                value={getQualityValue()}
                onChange={(e) => {
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
                  handleChange("quality_preset", preset);
                }}
                disabled={disabled}
              />
            </div>
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("process-speed-title")}</h1>
              <h2 className="subtitle is-6">{_("process-speed-subtitle")}</h2>
              <div className="select is-fullwidth is-vcentered">
                <select
                  onChange={(e) => handleChange("speed_preset", e.target.value)}
                  disabled={disabled}
                  value={
                    fields.speed_preset ?? (config.data as any)?.speed_preset
                  }
                >
                  <option value="ultrafast">
                    {_("encode-speed-ultrafast")}
                  </option>
                  <option value="superfast">
                    {_("encode-speed-superfast")}
                  </option>
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
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("encode-encoder-title")}</h1>
              <h2 className="subtitle is-6">{_("encode-encoder-subtitle")}</h2>
              <div className="select is-fullwidth is-vcentered">
                <select
                  onChange={(e) => handleChange("encoder", e.target.value)}
                  disabled={disabled}
                  value={fields.encoder ?? (config.data as any)?.encoder}
                >
                  <option
                    disabled={encoderIsUnavailable("libx264")}
                    value="libx264"
                  >
                    H.264
                  </option>
                  <option
                    disabled={encoderIsUnavailable("libx265")}
                    value="libx265"
                  >
                    H.265
                  </option>
                </select>
              </div>
            </div>
          </div>
          <div className="columns">
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("encode-timed-title")}</h1>
              <h2 className="subtitle is-6">{_("encode-timed-subtitle")}</h2>
              <input
                id="timedEncodingCheck"
                type="checkbox"
                className="switch"
                checked={!!fields.timed_encoding}
                onChange={(e) =>
                  handleChange("timed_encoding", e.target.checked)
                }
                disabled={disabled}
              />
              <label htmlFor="timedEncodingCheck">
                {_("checkbox-enabled")}
              </label>
            </div>
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("encode-hourstart-title")}</h1>
              <h2 className="subtitle is-6">
                {_("encode-hourstart-subtitle")}
              </h2>
              <div className="select is-fullwidth">
                <select
                  onChange={(e) => handleChange("hour_start", e.target.value)}
                  disabled={disabled}
                  value={fields.hour_start ?? (config.data as any)?.hour_start}
                >
                  {[...Array(24).keys()].map((h) => (
                    <option key={h} value={h}>
                      {h}:00
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("encode-hourend-title")}</h1>
              <h2 className="subtitle is-6">{_("encode-hourend-subtitle")}</h2>
              <div className="select is-fullwidth">
                <select
                  onChange={(e) => handleChange("hour_end", e.target.value)}
                  disabled={disabled}
                  value={fields.hour_end ?? (config.data as any)?.hour_end}
                >
                  {[...Array(24).keys()].map((h) => (
                    <option key={h} value={h}>
                      {h}:00
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="column is-3 my-auto">
              <h1 className="title is-5">{_("encode-minimum-size-title")}</h1>
              <h2 className="subtitle is-6">
                {_("encode-minimum-size-subtitle")}
              </h2>
              <div className="select is-fullwidth">
                <select
                  onChange={(e) =>
                    handleChange("minimum_file_size", e.target.value)
                  }
                  disabled={disabled}
                  value={
                    fields.minimum_file_size ??
                    (config.data as any)?.minimum_file_size
                  }
                >
                  <option value="0">0 MB</option>
                  <option value="50">50 MB</option>
                  <option value="100">100 MB</option>
                  <option value="200">200 MB</option>
                  <option value="500">500 MB</option>
                  <option value="1000">1 GB</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }
);
