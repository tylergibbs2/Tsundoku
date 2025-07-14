import {
  ChangeEvent,
  useEffect,
  useRef,
  useImperativeHandle,
  forwardRef,
  useState,
} from "react";
import { GeneralConfig, MutateConfigVars } from "../../interfaces";
import { getInjector } from "../../fluent";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetchConfig, setConfig } from "../../queries";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { DirectorySelect } from "../../Components/DirectorySelect";

const _ = getInjector();

export const GeneralConfigApp = forwardRef(
  ({ onDirtyChange }: { onDirtyChange: (dirty: boolean) => void }, ref) => {
    const queryClient = useQueryClient();

    const config = useQuery(["config", "general"], async () => {
      return await fetchConfig<GeneralConfig>("general");
    });

    const mutation = useMutation(
      async ({ key, value }: MutateConfigVars) => {
        return await setConfig<GeneralConfig>("general", key, value);
      },
      {
        onSuccess: (newConfig) => {
          queryClient.setQueryData(["config", "general"], newConfig);
        },
      }
    );

    // Local state for all fields
    const [fields, setFields] = useState<Partial<GeneralConfig>>({});
    const [dirty, setDirty] = useState(false);

    // Initialize local state from config
    useEffect(() => {
      if (config.data) {
        setFields({ ...config.data });
        setDirty(false);
        onDirtyChange(false);
      }
    }, [config.data]);

    // Dirty tracking
    useEffect(() => {
      if (!config.data) return;
      const isDirty = Object.keys(fields).some(
        (key) => fields[key] !== config.data[key]
      );
      setDirty(isDirty);
      onDirtyChange(isDirty);
    }, [fields, config.data]);

    // Expose save method to parent
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

    if (config.isLoading) return <GlobalLoading heightTranslation="none" />;

    // Handlers for each field
    const handleChange = (key: keyof GeneralConfig, value: any) => {
      setFields((prev) => ({ ...prev, [key]: value }));
    };

    return (
      <div className="box">
        <div className="columns is-multiline">
          <div className="column is-3 my-auto">
            <h1 className="title is-5">
              <span
                className="has-tooltip-bottom"
                data-tooltip={_("general-host-tooltip")}
              >
                {_("general-host-title")}
              </span>
            </h1>
            <h2 className="subtitle is-6">{_("general-host-subtitle")}</h2>
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
                  placeholder="6439"
                  min="1024"
                  max="65535"
                  value={fields.port ?? ""}
                  onChange={(e) => handleChange("port", e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="column is-3 my-auto">
            <h1 className="title is-5">{_("general-loglevel-title")}</h1>
            <h2 className="subtitle is-6">{_("general-loglevel-subtitle")}</h2>
            <div className="select is-fullwidth">
              <select
                value={fields.log_level ?? config.data?.log_level}
                onChange={(e) => handleChange("log_level", e.target.value)}
              >
                <option value="error">{_("log-level-error")}</option>
                <option value="warning">{_("log-level-warning")}</option>
                <option value="info">{_("log-level-info")}</option>
                <option value="debug">{_("log-level-debug")}</option>
              </select>
            </div>
          </div>
          <div className="column is-3 my-auto">
            <h1 className="title is-5">
              <span
                className="has-tooltip-bottom"
                data-tooltip={_("general-locale-tooltip")}
              >
                {_("general-locale-title")}
              </span>
            </h1>
            <h2 className="subtitle is-6">{_("general-locale-subtitle")}</h2>
            <div className="select is-fullwidth">
              <select
                value={fields.locale ?? config.data?.locale}
                onChange={(e) => handleChange("locale", e.target.value)}
              >
                <option value="en">English</option>
                <option value="ru">русский</option>
                <option value="ja">日本語</option>
              </select>
            </div>
          </div>
          <div className="column is-3 my-auto">
            <h1 className="title is-5">
              <span
                className="has-tooltip-bottom"
                data-tooltip={_("general-updatecheck-tooltip")}
              >
                {_("general-updatecheck-title")}
              </span>
            </h1>
            <h2 className="subtitle is-6">
              {_("general-updatecheck-subtitle")}
            </h2>
            <div className="field">
              <input
                id="updateCheck"
                type="checkbox"
                className="switch"
                checked={!!fields.update_do_check}
                onChange={(e) =>
                  handleChange("update_do_check", e.target.checked)
                }
              />
              <label htmlFor="updateCheck">{_("checkbox-enabled")}</label>
            </div>
          </div>
          <div className="column is-4 my-auto">
            <h1 className="title is-5">
              <span className="has-tooltip-bottom">
                {_("general-defaultformat-title")}
              </span>
            </h1>
            <h2 className="subtitle is-6">
              {_("general-defaultformat-subtitle")}
            </h2>
            <input
              className="input"
              type="text"
              value={fields.default_desired_format ?? ""}
              onChange={(e) =>
                handleChange("default_desired_format", e.target.value)
              }
            />
          </div>
          <div className="column is-4 my-auto">
            <h1 className="title is-5">Use Season Folder</h1>
            <h2 className="subtitle is-6">
              Whether or not a season folder should be created when moving a
              show
            </h2>
            <div className="field">
              <input
                id="seasonFolderCheck"
                type="checkbox"
                className="switch"
                checked={!!fields.use_season_folder}
                onChange={(e) =>
                  handleChange("use_season_folder", e.target.checked)
                }
              />
              <label htmlFor="seasonFolderCheck">{_("checkbox-enabled")}</label>
            </div>
          </div>
          <div className="column is-4 my-auto">
            <h1 className="title is-5">{_("general-unwatchfinished-title")}</h1>
            <h2 className="subtitle is-6">
              {_("general-unwatchfinished-subtitle")}
            </h2>
            <div className="field">
              <input
                id="unwatchCheck"
                type="checkbox"
                className="switch"
                checked={!!fields.unwatch_when_finished}
                onChange={(e) =>
                  handleChange("unwatch_when_finished", e.target.checked)
                }
              />
              <label htmlFor="unwatchCheck">{_("checkbox-enabled")}</label>
            </div>
          </div>
        </div>
      </div>
    );
  }
);
