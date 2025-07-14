import { getInjector } from "../../fluent";
import { useQuery } from "react-query";
import { Show, GeneralConfig } from "../../interfaces";
import { fetchConfig } from "../../queries";
import { LibrarySelect } from "./library_select";

const _ = getInjector();

interface ShowFormParams {
  mode: "add" | "edit";
  show?: Show;
  register: any;
  tab?: string;
  generalConfig?: GeneralConfig;
}

export const ShowForm = ({
  mode,
  show,
  register,
  tab,
  generalConfig,
}: ShowFormParams) => {
  const configQuery = useQuery(["config", "general"], async () => {
    return await fetchConfig<GeneralConfig>("general");
  });

  // Use provided generalConfig or fetch it
  const config = generalConfig || configQuery.data;

  if (mode === "edit" && show === null) return <></>;

  const isEditMode = mode === "edit";
  const shouldShow = isEditMode ? tab === "info" : true;

  return (
    <form
      className={isEditMode && tab !== "info" ? "is-hidden" : ""}
      style={{
        overflow: "hidden auto",
      }}
    >
      <div className="form-columns columns is-multiline">
        <div className="column is-full">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_(
                  isEditMode ? "edit-form-name-tt" : "add-form-name-tt"
                )}
              >
                {_(isEditMode ? "edit-form-name-field" : "add-form-name-field")}
              </span>
            </label>
            <div className="control">
              <input
                {...register("title", { required: true })}
                className="input"
                type="text"
                placeholder={_(
                  isEditMode
                    ? "edit-form-name-placeholder"
                    : "add-form-name-placeholder"
                )}
              />
            </div>
          </div>
        </div>

        <div className="column is-half">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_("edit-form-resolution-tt")}
              >
                {_("edit-form-resolution-field")}
              </span>
            </label>
            <div className="select is-fullwidth">
              <select
                {...register("preferred_resolution", { required: true })}
                defaultValue={
                  isEditMode && show?.preferred_resolution != null
                    ? show.preferred_resolution
                    : "0"
                }
              >
                <option value="0">Any</option>
                <option value="480p">480p</option>
                <option value="720p">720p</option>
                <option value="1080p">1080p</option>
              </select>
            </div>
          </div>
        </div>

        <div className="column is-half">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-left"
                data-tooltip={_("edit-form-release-group-tt")}
              >
                {_("edit-form-release-group-field")}
              </span>
            </label>
            <div className="control">
              <input
                {...register("preferred_release_group")}
                className="input"
              />
            </div>
          </div>
        </div>

        <div className="column is-half">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_(
                  isEditMode ? "edit-form-season-tt" : "add-form-season-tt"
                )}
              >
                {_(
                  isEditMode
                    ? "edit-form-season-field"
                    : "add-form-season-field"
                )}
              </span>
            </label>
            <div className="control">
              <input
                {...register("season", { required: true })}
                className="input"
                type="number"
              />
            </div>
          </div>
        </div>

        <div className="column is-half">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-top"
                data-tooltip={_(
                  isEditMode
                    ? "edit-form-episode-offset-tt"
                    : "add-form-episode-offset-tt"
                )}
              >
                {_(
                  isEditMode
                    ? "edit-form-episode-offset-field"
                    : "add-form-episode-offset-field"
                )}
              </span>
            </label>
            <div className="control">
              <input
                {...register("episode_offset", { required: true })}
                className="input"
                type="number"
              />
            </div>
          </div>
        </div>

        <div className="column is-full">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_(
                  isEditMode ? "edit-form-library-tt" : "add-form-library-tt"
                )}
              >
                {_(
                  isEditMode
                    ? "edit-form-library-field"
                    : "add-form-library-field"
                )}
              </span>
            </label>
            <div className="control">
              <LibrarySelect register={register} />
            </div>
          </div>
        </div>

        <div className="column is-full">
          <details>
            <summary>
              {_(isEditMode ? "edit-form-advanced" : "add-form-advanced")}
            </summary>

            <div className="columns mt-2">
              <div className="column">
                <div className="field">
                  <label className="label">
                    <span
                      className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                      data-tooltip={_(
                        isEditMode
                          ? "edit-form-desired-format-tt"
                          : "add-form-desired-format-tt"
                      )}
                    >
                      {_(
                        isEditMode
                          ? "edit-form-desired-format-field"
                          : "add-form-desired-format-field"
                      )}
                    </span>
                  </label>
                  <div className="control">
                    <input
                      {...register("desired_format")}
                      className="input"
                      type="text"
                      placeholder={
                        configQuery.isLoading
                          ? "..."
                          : config?.default_desired_format
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="column">
                <div className="field">
                  <label className="label">
                    <span
                      className="has-tooltip-arrow has-tooltip-multiline has-tooltip-left"
                      data-tooltip={_(
                        isEditMode
                          ? "edit-form-local-title-tt"
                          : "add-form-local-title-tt"
                      )}
                    >
                      {_(
                        isEditMode
                          ? "edit-form-local-title-field"
                          : "add-form-local-title-field"
                      )}
                    </span>
                  </label>
                  <div className="control">
                    <input
                      {...register("title_local")}
                      className="input"
                      type="text"
                    />
                  </div>
                </div>
              </div>
            </div>
          </details>
        </div>
      </div>
    </form>
  );
};
