import {
  ChangeEvent,
  useState,
  useEffect,
  useImperativeHandle,
  forwardRef,
} from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { getInjector } from "../../fluent";
import { MutateConfigVars } from "../../interfaces";
import { fetchConfig, setConfig } from "../../queries";

const _ = getInjector();

interface TorrentConfigProps {
  onDirtyChange: (dirty: boolean) => void;
}

export const TorrentConfig = forwardRef(
  ({ onDirtyChange }: TorrentConfigProps, ref) => {
    const queryClient = useQueryClient();

    const config = useQuery(["config", "torrent"], async () => {
      return await fetchConfig("torrent");
    });

    const mutation = useMutation(
      async ({ key, value }: MutateConfigVars) => {
        return await setConfig("torrent", key, value);
      },
      {
        onSuccess: (newConfig) => {
          queryClient.setQueryData(["config", "torrent"], newConfig);
        },
      }
    );

    const [fields, setFields] = useState<any>({});
    const [dirty, setDirty] = useState(false);
    const [fetchingStatus, setFetchingStatus] = useState<boolean>(false);
    const [clientStatus, setClientStatus] = useState<boolean>(null);

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

    const testTorrentConnection = async () => {
      if (fetchingStatus) return;
      setFetchingStatus(true);
      let resp = await fetch("/api/v1/config/torrent/test");
      if (resp.ok) {
        let data = await resp.json();
        setClientStatus(data.result);
      } else {
        setClientStatus(false);
      }
      setFetchingStatus(false);
    };

    if (config.isLoading) return <GlobalLoading heightTranslation="none" />;

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
                value={fields.client ?? (config.data as any)?.client}
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
                  value={fields.host ?? (config.data as any)?.host ?? ""}
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
                  value={fields.port ?? (config.data as any)?.port ?? ""}
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
              value={fields.username ?? (config.data as any)?.username ?? ""}
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
              value={fields.password ?? (config.data as any)?.password ?? ""}
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
                checked={fields.secure ?? (config.data as any)?.secure ?? false}
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
  status?: boolean;
}

const ConnectionStatus = ({ status }: ConnectionStatusParams) => {
  if (status)
    return (
      <span className="tag is-success mt-2 ml-2">
        {_("config-test-success")}
      </span>
    );
  else if (status === false)
    return (
      <span className="tag is-danger mt-2 ml-2">
        {_("config-test-failure")}
      </span>
    );
  else return <></>;
};
