import {
  ChangeEvent,
  useEffect,
  useImperativeHandle,
  forwardRef,
  useState,
} from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { getInjector } from "../../fluent";
import { MutateConfigVars } from "../../interfaces";
import { fetchConfig, setConfig } from "../../queries";

const _ = getInjector();

interface FeedsConfigProps {
  onDirtyChange: (dirty: boolean) => void;
}

export const FeedsConfig = forwardRef(
  ({ onDirtyChange }: FeedsConfigProps, ref) => {
    const queryClient = useQueryClient();

    const config = useQuery(["config", "feeds"], async () => {
      return await fetchConfig("feeds");
    });

    const mutation = useMutation(
      async ({ key, value }: MutateConfigVars) => {
        return await setConfig("feeds", key, value);
      },
      {
        onSuccess: (newConfig) => {
          queryClient.setQueryData(["config", "feeds"], newConfig);
        },
      }
    );

    const [fields, setFields] = useState<any>({});
    const [dirty, setDirty] = useState(false);

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

    if (config.isLoading) return <GlobalLoading heightTranslation="none" />;

    const handleChange = (key: string, value: any) => {
      setFields((prev) => ({ ...prev, [key]: value }));
    };

    return (
      <div className="box">
        <div className="columns">
          <div className="column is-3 my-auto">
            <h1 className="title is-5">{_("feeds-fuzzy-cutoff-title")}</h1>
            <h2 className="subtitle is-6">
              {_("feeds-fuzzy-cutoff-subtitle")}
            </h2>
            <div className="field has-addons">
              <div className="control">
                <input
                  className="input"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="90"
                  value={fields.fuzzy_cutoff ?? ""}
                  onChange={(e) => handleChange("fuzzy_cutoff", e.target.value)}
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
                  value={fields.polling_interval ?? ""}
                  onChange={(e) =>
                    handleChange("polling_interval", e.target.value)
                  }
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
                  value={fields.complete_check_interval ?? ""}
                  onChange={(e) =>
                    handleChange("complete_check_interval", e.target.value)
                  }
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
                  value={fields.seed_ratio_limit ?? ""}
                  onChange={(e) =>
                    handleChange("seed_ratio_limit", e.target.value)
                  }
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
);
