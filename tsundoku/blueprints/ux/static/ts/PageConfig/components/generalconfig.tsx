import { ChangeEvent } from "react";
import { GeneralConfig, MutateConfigVars } from "../../interfaces";
import { getInjector } from "../../fluent";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetchConfig, setConfig } from "../../queries";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { DirectorySelect } from "../../Components/DirectorySelect";

const _ = getInjector();

export const GeneralConfigApp = () => {
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

  if (config.isLoading) return <GlobalLoading heightTranslation="none" />;

  const inputHost = (e: ChangeEvent<HTMLInputElement>) => {
    mutation.mutate({ key: "host", value: e.target.value });
  };

  const inputPort = (e: ChangeEvent<HTMLInputElement>) => {
    mutation.mutate({ key: "port", value: e.target.value });
  };

  const inputUpdateCheck = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked)
      mutation.mutate({ key: "update_do_check", value: true });
    else mutation.mutate({ key: "update_do_check", value: false });
  };

  const inputLocale = (e: ChangeEvent<HTMLSelectElement>) => {
    mutation.mutate({
      key: "locale",
      value: e.target.options[e.target.selectedIndex].value,
    });
  };

  const inputLogLevel = (e: ChangeEvent<HTMLSelectElement>) => {
    mutation.mutate({
      key: "log_level",
      value: e.target.options[e.target.selectedIndex].value,
    });
  };

  const inputDefaultDesiredFormat = (e: ChangeEvent<HTMLInputElement>) => {
    mutation.mutate({ key: "default_desired_format", value: e.target.value });
  };

  const inputUseSeasonFolder = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked)
      mutation.mutate({ key: "use_season_folder", value: true });
    else mutation.mutate({ key: "use_season_folder", value: false });
  };

  const inputUnwatchWhenFinished = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked)
      mutation.mutate({ key: "unwatch_when_finished", value: true });
    else mutation.mutate({ key: "unwatch_when_finished", value: false });
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
                defaultValue={config?.data?.host}
                onChange={inputHost}
              />
            </div>
            <div className="control">
              <input
                className="input"
                type="number"
                placeholder="6439"
                min="1024"
                max="65535"
                defaultValue={config?.data?.port}
                onChange={inputPort}
              />
            </div>
          </div>
        </div>
        <div className="column is-3 my-auto">
          <h1 className="title is-5">{_("general-loglevel-title")}</h1>
          <h2 className="subtitle is-6">{_("general-loglevel-subtitle")}</h2>
          <div className="select is-fullwidth">
            <select
              onChange={inputLogLevel}
              defaultValue={config?.data?.log_level}
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
            <select onChange={inputLocale} defaultValue={config?.data?.locale}>
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
          <h2 className="subtitle is-6">{_("general-updatecheck-subtitle")}</h2>
          <div className="field">
            <input
              id="updateCheck"
              type="checkbox"
              className="switch"
              defaultChecked={config?.data?.update_do_check}
              onChange={inputUpdateCheck}
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
            defaultValue={config?.data?.default_desired_format}
            onChange={inputDefaultDesiredFormat}
          />
        </div>
        <div className="column is-4 my-auto">
          <h1 className="title is-5">Use Season Folder</h1>
          <h2 className="subtitle is-6">
            Whether or not a season folder should be created when moving a show
          </h2>
          <div className="field">
            <input
              id="seasonFolderCheck"
              type="checkbox"
              className="switch"
              defaultChecked={config?.data?.use_season_folder}
              onChange={inputUseSeasonFolder}
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
              defaultChecked={config?.data?.unwatch_when_finished}
              onChange={inputUnwatchWhenFinished}
            />
            <label htmlFor="unwatchCheck">{_("checkbox-enabled")}</label>
          </div>
        </div>
      </div>
    </div>
  );
};
