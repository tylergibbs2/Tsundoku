import { GeneralConfig, NyaaIndividualResult, Show } from "../interfaces";

import { toast } from "bulma-toast";
import { useState, useEffect, Dispatch, SetStateAction } from "react";
import { useForm } from "react-hook-form";
import { getInjector } from "../fluent";
import { IonIcon } from "../icon";
import { ShowToggleButton } from "../PageIndex/components/show_toggle_button";

const _ = getInjector();

interface NyaaShowModalParams {
  shows: Show[];
  setChoice: Dispatch<SetStateAction<NyaaIndividualResult>>;
  choice?: NyaaIndividualResult;
  generalConfig: GeneralConfig;
}

export const NyaaShowModal = ({
  setChoice,
  choice,
  shows,
  generalConfig,
}: NyaaShowModalParams) => {
  let addingDefaultState = false;
  if (shows.length) addingDefaultState = true;

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [addingToExisting, setAddingToExisting] =
    useState<boolean>(addingDefaultState);
  const [showId, setShowId] = useState<number>(null);
  const [doOverwrite, setDoOverwrite] = useState<boolean>(false);
  const [watch, setWatch] = useState<boolean>(false);
  const [postProcess, setPostProcess] = useState<boolean>(false);

  const addToExisting = () => {
    setAddingToExisting(true);
  };

  const addNewShow = () => {
    setAddingToExisting(false);
  };

  const addNyaaResult = async () => {
    let request = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        show_id: showId,
        torrent_link: choice.torrent_link,
        overwrite: doOverwrite,
      }),
    };

    let response = await fetch("/api/v1/nyaa", request);
    if (!response.ok) {
      setSubmitting(false);
      return;
    }

    let data = await response.json();

    let addedCount: number = data.result.length;
    setSubmitting(false);
    setChoice(null);
    setAddingToExisting(true);
    setShowId(null);

    toast({
      message: _("entry-add-success", { count: addedCount }),
      duration: 5000,
      position: "bottom-right",
      type: "is-success",
      dismissible: true,
      animate: { in: "fadeIn", out: "fadeOut" },
    });
  };

  useEffect(() => {
    if (showId === null) return;

    addNyaaResult();
  }, [showId]);

  const returnCallback = (data: any) => {
    if ("overwrite" in data) setDoOverwrite(data.overwrite);
    if ("showId" in data) setShowId(data.showId);
  };

  const closeModal = () => {
    setChoice(null);
  };

  const receiveWatch = (_: any, state: boolean) => {
    setWatch(state);
  };

  const receivePostProcess = (_: any, state: boolean) => {
    setPostProcess(state);
  };

  return (
    <div
      id="upsert-show-modal"
      className={"modal modal-fx-fadeInScale " + (choice ? "is-active" : "")}
    >
      <div
        className="modal-background"
        onClick={submitting ? null : closeModal}
      ></div>
      <div className="modal-card">
        <header className="modal-card-head">
          <p className="modal-card-title">{_("modal-title")}</p>
          <div className="buttons">
            <ShowToggleButton
              setValue={receivePostProcess}
              attribute="post_process"
              onIcon="color-wand"
              offIcon="color-wand-outline"
              onTooltip={_("unprocess-button-title")}
              offTooltip={_("process-button-title")}
              additionalClasses="is-primary"
              disabled={addingToExisting}
            />
            <ShowToggleButton
              setValue={receiveWatch}
              attribute="watch"
              onIcon="bookmark"
              offIcon="bookmark-outline"
              onTooltip={_("unwatch-button-title")}
              offTooltip={_("watch-button-title")}
              additionalClasses="is-primary"
              disabled={addingToExisting}
            />
          </div>
        </header>

        <section className="modal-card-body">
          <div className="tabs is-centered is-toggle is-toggle-rounded">
            <ul>
              <li className={addingToExisting ? "" : "is-active"}>
                <a onClick={addNewShow}>
                  <span className="icon is-small">
                    <IonIcon name="add-circle" />
                  </span>
                  <span>{_("modal-tab-new")}</span>
                </a>
              </li>
              <li className={addingToExisting ? "is-active" : ""}>
                <a
                  onClick={shows.length ? addToExisting : null}
                  style={shows.length ? {} : { cursor: "auto" }}
                  className={shows.length ? "" : "has-text-grey-light"}
                >
                  <span className="icon is-small">
                    <IonIcon name="pencil-sharp" />
                  </span>
                  <span>{_("modal-tab-existing")}</span>
                </a>
              </li>
            </ul>
          </div>
          <ModalForm
            addingToExisting={addingToExisting}
            setSubmitting={setSubmitting}
            returnCallback={returnCallback}
            shows={shows}
            watch={watch}
            postProcess={postProcess}
            generalConfig={generalConfig}
          />
        </section>

        <footer className="modal-card-foot is-size-7">
          <button
            className={"button is-success " + (submitting ? "is-loading" : "")}
            type="submit"
            form="nyaa-result-form"
          >
            {_("add-button")}
          </button>
          <button onClick={submitting ? null : closeModal} className="button">
            {_("cancel-button")}
          </button>
        </footer>
      </div>
    </div>
  );
};

interface ModalFormParams {
  addingToExisting: boolean;
  shows: Show[];
  setSubmitting: Dispatch<SetStateAction<boolean>>;
  returnCallback?: any;
  watch: boolean;
  postProcess: boolean;
  generalConfig: GeneralConfig;
}

const ModalForm = ({
  addingToExisting,
  shows,
  setSubmitting,
  returnCallback,
  watch,
  postProcess,
  generalConfig,
}: ModalFormParams) => {
  if (addingToExisting && shows.length)
    return (
      <AddToExistingShowForm
        setSubmitting={setSubmitting}
        returnCallback={returnCallback}
        shows={shows}
      />
    );
  else
    return (
      <AddShowForm
        setSubmitting={setSubmitting}
        returnCallback={returnCallback}
        watch={watch}
        postProcess={postProcess}
        generalConfig={generalConfig}
      />
    );
};

interface ExistingShowSelectInputs {
  register: any;
  name: string;
  shows: Show[];
}

const ExistingShowSelect = ({
  register,
  name,
  shows,
}: ExistingShowSelectInputs) => {
  return (
    <select {...register(name, { required: true })} required>
      {shows.map((show) => (
        <option key={show.id_} value={show.id_}>
          {show.title}
        </option>
      ))}
    </select>
  );
};

interface AddToExistingShowFormParams {
  shows: Show[];
  setSubmitting: Dispatch<SetStateAction<boolean>>;
  returnCallback?: any;
}

interface AddToExistingShowFormInputs {
  existingShow: number;
  overwrite: boolean;
}

const AddToExistingShowForm = ({
  setSubmitting,
  returnCallback,
  shows,
}: AddToExistingShowFormParams) => {
  const { register, handleSubmit } = useForm();

  const submitHandler = (data: AddToExistingShowFormInputs) => {
    setSubmitting(true);

    returnCallback({
      showId: data.existingShow,
      overwrite: data.overwrite,
    });
  };

  return (
    // @ts-ignore
    <form
      onSubmit={handleSubmit(submitHandler)}
      id="nyaa-result-form"
      className="has-text-centered"
    >
      <div className="field">
        <label className="label">
          <span
            className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
            data-tooltip={_("existing-show-tt")}
          >
            {_("existing-show-field")}
          </span>
        </label>
        <div className="select is-fullwidth">
          <ExistingShowSelect
            register={register}
            name="existingShow"
            shows={shows}
          />
        </div>
      </div>
      <label className="checkbox">
        <input {...register("overwrite")} type="checkbox" />
        <span className="ml-1">Overwrite existing entries?</span>
      </label>
    </form>
  );
};

interface AddShowFormInputs {
  title: string;
  desired_format: string;
  desired_folder: string;
  season: string;
  episode_offset: string;
}

interface AddShowFormParams {
  setSubmitting: Dispatch<SetStateAction<boolean>>;
  returnCallback?: any;
  watch: boolean;
  postProcess: boolean;
  generalConfig: GeneralConfig;
}

const AddShowForm = ({
  setSubmitting,
  returnCallback,
  watch,
  postProcess,
  generalConfig,
}: AddShowFormParams) => {
  let defaultValues = {
    title: "",
    desired_format: generalConfig?.default_desired_format,
    desired_folder: generalConfig?.default_desired_folder,
    season: 1,
    episode_offset: 0,
    watch: true,
    post_process: true,
  };

  const { register, handleSubmit, setValue, reset } = useForm({
    defaultValues: defaultValues,
  });

  useEffect(() => {
    reset(defaultValues);
  }, [generalConfig]);

  useEffect(() => {
    setValue("watch", watch);
    setValue("post_process", postProcess);
  }, [watch, postProcess]);

  const submitHandler = async (inputs: AddShowFormInputs) => {
    setSubmitting(true);

    let request = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(inputs),
    };

    let response = await fetch("/api/v1/shows", request);
    if (!response.ok) {
      setSubmitting(false);
      return;
    }

    let data = await response.json();
    if (typeof returnCallback !== "undefined") {
      returnCallback({
        showId: data.result.id_,
      });
    } else setSubmitting(false);
  };

  return (
    // @ts-ignore
    <form onSubmit={handleSubmit(submitHandler)} id="nyaa-result-form">
      <div className="form-columns columns is-multiline">
        <div className="column is-full">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_("name-tt")}
              >
                {_("name-field")}
              </span>
            </label>
            <div className="control">
              <input
                {...register("title", { required: true })}
                className="input"
                type="text"
                placeholder={_("name-placeholder")}
              />
            </div>
          </div>
        </div>

        <div className="column is-full">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_("desired-format-tt")}
              >
                {_("desired-format-field")}
              </span>
            </label>
            <div className="control">
              <input
                {...register("desired_format")}
                className="input"
                type="text"
                placeholder="{n} - {s00e00}"
              />
            </div>
          </div>
        </div>

        <div className="column is-full">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_("desired-folder-tt")}
              >
                {_("desired-folder-field")}
              </span>
            </label>
            <div className="control">
              <input
                {...register("desired_folder")}
                className="input"
                type="text"
              />
            </div>
          </div>
        </div>

        <div className="column is-half">
          <div className="field">
            <label className="label">
              <span
                className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                data-tooltip={_("season-tt")}
              >
                {_("season-field")}
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
                data-tooltip={_("episode-offset-tt")}
              >
                {_("episode-offset-field")}
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
      </div>
    </form>
  );
};
