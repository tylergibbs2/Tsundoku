import { ChangeEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { getInjector } from "../../fluent";
import { MutateConfigVars } from "../../interfaces";
import { fetchConfig, setConfig } from "../../queries";

const _ = getInjector();

interface FeedsConfig {
  polling_interval?: number;
  complete_check_interval?: number;
  fuzzy_cutoff?: number;
  seed_ratio_limit?: number;
}

export const FeedsConfig = () => {
  const queryClient = useQueryClient();

  const config = useQuery(["config", "feeds"], async () => {
    return await fetchConfig<FeedsConfig>("feeds");
  });

  const mutation = useMutation(
    async ({ key, value }: MutateConfigVars) => {
      return await setConfig<FeedsConfig>("feeds", key, value);
    },
    {
      onSuccess: (newConfig) => {
        queryClient.setQueryData(["config", "feeds"], newConfig);
      },
    }
  );

  if (config.isLoading) return <GlobalLoading heightTranslation="none" />;

  const inputPollingInterval = async (e: ChangeEvent<HTMLInputElement>) => {
    mutation.mutate({ key: "polling_interval", value: e.target.value });
  };

  const inputCompleteCheck = async (e: ChangeEvent<HTMLInputElement>) => {
    mutation.mutate({ key: "complete_check_interval", value: e.target.value });
  };

  const inputFuzzyCutoff = async (e: ChangeEvent<HTMLInputElement>) => {
    mutation.mutate({ key: "fuzzy_cutoff", value: e.target.value });
  };

  const inputSeedRatioLimit = async (e: ChangeEvent<HTMLInputElement>) => {
    e.target.value = parseFloat(e.target.value).toFixed(2);

    mutation.mutate({ key: "seed_ratio_limit", value: e.target.value });
  };

  return (
    <div className="box">
      <div className="columns">
        <div className="column is-3 my-auto">
          <h1 className="title is-5">{_("feeds-fuzzy-cutoff-title")}</h1>
          <h2 className="subtitle is-6">{_("feeds-fuzzy-cutoff-subtitle")}</h2>
          <div className="field has-addons">
            <div className="control">
              <input
                className="input"
                type="number"
                min="0"
                max="100"
                placeholder="90"
                defaultValue={config.data?.fuzzy_cutoff}
                onChange={inputFuzzyCutoff}
              />
            </div>
            <div className="control">
              <a className="button is-static">%</a>
            </div>
          </div>
        </div>
        <div className="column is-3 my-auto">
          <h1 className="title is-5">
            <span
              className="has-tooltip-bottom has-tooltip-multiline"
              data-tooltip={_("feeds-pollinginterval-tooltip")}
            >
              {_("feeds-pollinginterval-title")}
            </span>
          </h1>
          <h2 className="subtitle is-6">
            {_("feeds-pollinginterval-subtitle")}
          </h2>
          <div className="field has-addons">
            <div className="control">
              <input
                className="input"
                type="number"
                min="180"
                placeholder="900"
                defaultValue={config.data?.polling_interval}
                onChange={inputPollingInterval}
              />
            </div>
            <div className="control">
              <a className="button is-static">{_("seconds-suffix")}</a>
            </div>
          </div>
        </div>
        <div className="column is-3 my-auto">
          <h1 className="title is-5">{_("feeds-completioncheck-title")}</h1>
          <h2 className="subtitle is-6">
            {_("feeds-completioncheck-subtitle")}
          </h2>
          <div className="field has-addons">
            <div className="control">
              <input
                className="input"
                type="number"
                min="1"
                placeholder="15"
                defaultValue={config.data?.complete_check_interval}
                onChange={inputCompleteCheck}
              />
            </div>
            <div className="control">
              <a className="button is-static">{_("seconds-suffix")}</a>
            </div>
          </div>
        </div>
        <div className="column is-3 my-auto">
          <h1 className="title is-5">{_("feeds-seedratio-title")}</h1>
          <h2 className="subtitle is-6">{_("feeds-seedratio-subtitle")}</h2>
          <div className="field">
            <div className="control">
              <input
                className="input"
                type="number"
                min="0.0"
                placeholder="0.0"
                step="0.1"
                defaultValue={config.data?.seed_ratio_limit?.toFixed(2)}
                onChange={inputSeedRatioLimit}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
