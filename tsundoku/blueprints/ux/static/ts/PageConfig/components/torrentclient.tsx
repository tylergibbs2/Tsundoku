import {
  ChangeEvent,
  useState,
  useEffect,
  useImperativeHandle,
  forwardRef,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { getInjector } from "../../fluent";
import { testTorrentClient } from "../../api";
import type {
  TorrentConfigResponse,
  TorrentConfigUpdate,
  TorrentTestResult,
} from "../../api";
import { configKeys, saveTorrentConfig, torrentConfigQuery } from "../queries";

const _ = getInjector();

interface TorrentConfigProps {
  onDirtyChange: (dirty: boolean) => void;
}

export const TorrentConfig = forwardRef(
  ({ onDirtyChange }: TorrentConfigProps, ref) => {
    const queryClient = useQueryClient();

    const config = useQuery(torrentConfigQuery());

    const mutation = useMutation({
      mutationFn: saveTorrentConfig,
      onSuccess: (newConfig) => {
        queryClient.setQueryData(configKeys.torrent, newConfig);
      },
    });

    const [fields, setFields] = useState<Partial<TorrentConfigResponse>>({});
    const [dirty, setDirty] = useState(false);
    const [fetchingStatus, setFetchingStatus] = useState<boolean>(false);
    const [clientStatus, setClientStatus] = useState<TorrentTestResult | null>(
      null
    );

    useEffect(() => {
      if (config.data && typeof config.data === "object") {
        setFields({ ...config.data });
        setDirty(false);
        onDirtyChange(false);
      }
    }, [config.data]);

    // Returns only the fields that differ from what the server last sent.
    const changedFields = (saved: TorrentConfigResponse): TorrentConfigUpdate =>
      Object.fromEntries(
        Object.entries(fields).filter(
          ([key, value]) => value !== saved[key as keyof TorrentConfigResponse]
        )
      );

    useEffect(() => {
      if (!config.data) return;
      const isDirty = Object.keys(changedFields(config.data)).length > 0;
      setDirty(isDirty);
      onDirtyChange(isDirty);
    }, [fields, config.data]);

    useImperativeHandle(ref, () => ({
      async save() {
        if (!dirty || !config.data) return;

        // One PATCH for the whole delta; see generalconfig.tsx.
        const changed = changedFields(config.data);
        if (Object.keys(changed).length > 0)
          await mutation.mutateAsync(changed);

        setDirty(false);
        onDirtyChange(false);
      },
    }));

    const testTorrentConnection = async () => {
      if (fetchingStatus) return;
      setFetchingStatus(true);
      try {
        const { data } = await testTorrentClient({ throwOnError: true });
        setClientStatus(data.result);
      } catch (e) {
        setClientStatus({ success: false, error: String(e) });
      }
      setFetchingStatus(false);
    };

    if (config.isPending || !config.data)
      return <GlobalLoading heightTranslation="none" />;

    const handleChange = (key: string, value: any) => {
      setClientStatus(null);
      setFields((prev) => ({ ...prev, [key]: value }));
    };

    return (
      <div className="box">
        <div className="columns">
          <div className="column is-2 my-auto">
            <h1 className="title is-5">{_("torrent-client-title")}</h1>
            <h2 className="subtitle is-6">{_("torrent-client-subtitle")}</h2>
            <div className="select is-fullwidth">
              <select
                value={fields.client}
                onChange={(e) => handleChange("client", e.target.value)}
              >
                <option value="deluge">Deluge</option>
                <option value="transmission">Transmission</option>
                <option value="qbittorrent">qBittorrent</option>
              </select>
            </div>
          </div>
          <div className="column is-3 my-auto">
            <h1 className="title is-5">{_("torrent-host-title")}</h1>
            <h2 className="subtitle is-6">{_("torrent-host-subtitle")}</h2>
            <div className="field has-addons">
              <div className="control is-expanded">
                <input
                  className="input"
                  type="text"
                  placeholder="localhost"
                  value={fields.host ?? ""}
                  onChange={(e) => handleChange("host", e.target.value)}
                />
              </div>
              <div className="control">
                <input
                  className="input"
                  type="number"
                  placeholder="8080"
                  min="1"
                  max="65535"
                  value={fields.port ?? ""}
                  onChange={(e) => handleChange("port", e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="column is-2 my-auto">
            <h1 className="title is-5">{_("torrent-username-title")}</h1>
            <h2 className="subtitle is-6">{_("torrent-username-subtitle")}</h2>
            <input
              className="input"
              type="text"
              value={fields.username ?? ""}
              onChange={(e) => handleChange("username", e.target.value)}
              placeholder="admin"
              name="disableAuto"
              autoComplete="off"
            />
          </div>
          <div className="column is-2 my-auto">
            <h1 className="title is-5">{_("torrent-password-title")}</h1>
            <h2 className="subtitle is-6">{_("torrent-password-subtitle")}</h2>
            <input
              className="input"
              type="password"
              value={fields.password ?? ""}
              onChange={(e) => handleChange("password", e.target.value)}
              placeholder="********"
              name="disableAuto"
              autoComplete="off"
            />
          </div>
          <div className="column is-3 my-auto">
            <h1 className="title is-5">{_("torrent-secure-title")}</h1>
            <h2 className="subtitle is-6">{_("torrent-secure-subtitle")}</h2>
            <div className="field">
              <input
                id="secureCheck"
                type="checkbox"
                className="switch"
                checked={fields.secure ?? false}
                onChange={(e) => handleChange("secure", e.target.checked)}
              />
              <label htmlFor="secureCheck">{_("checkbox-enabled")}</label>
            </div>
          </div>
        </div>
        <div>
          <a
            onClick={testTorrentConnection}
            className={"button is-info " + (fetchingStatus ? "is-loading" : "")}
          >
            {_("config-test")}
          </a>
          <ConnectionStatus status={clientStatus} />
        </div>
      </div>
    );
  }
);

interface ConnectionStatusParams {
  status?: TorrentTestResult | null;
}

const ConnectionStatus = ({ status }: ConnectionStatusParams) => {
  if (!status) return <></>;

  if (status.success)
    return (
      <span className="tag is-success mt-2 ml-2">
        {_("config-test-success")}
      </span>
    );

  return (
    <span className="tag is-danger mt-2 ml-2">
      {status.error ?? _("config-test-failure")}
    </span>
  );
};
