import { toast } from "bulma-toast";
import {
  useEffect,
  Dispatch,
  SetStateAction,
  useState,
  ChangeEvent,
} from "react";
import {
  SubmitHandler,
  useForm,
  UseFormHandleSubmit,
  UseFormRegister,
  UseFormSetValue,
} from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { getInjector } from "../fluent";
import { Show, GeneralConfig } from "../interfaces";
import {
  addNewShow,
  fetchDistinctSeenReleases,
  fetchFilteredSeenReleases,
  fetchLibraries,
} from "../queries";
import { ShowToggleButton } from "./components/show_toggle_button";
import { LibrarySelect } from "./components/library_select";
import { ShowForm } from "./components/ShowForm";

const _ = getInjector();

interface AddModalParams {
  currentModal?: string;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
  generalConfig: GeneralConfig;
}

export type AddShowFormValues = {
  title: string;
  library_id: number | null;
  desired_format: string;
  title_local: string;
  season: number;
  episode_offset: number;
  watch: boolean;
  preferred_resolution: string;
  preferred_release_group: string;
};

export const AddModal = ({
  currentModal,
  setCurrentModal,
  generalConfig,
}: AddModalParams) => {
  const queryClient = useQueryClient();

  const mutation = useMutation(addNewShow, {
    onSuccess: (newShow) => {
      queryClient.invalidateQueries(["shows"]);
      toast({
        message: _("show-add-success"),
        duration: 5000,
        position: "bottom-right",
        type: "is-success",
        dismissible: true,
        animate: { in: "fadeIn", out: "fadeOut" },
      });

      setCurrentModal(null);
    },
  });

  const libraries = useQuery(["libraries"], async () => {
    return await fetchLibraries();
  });

  let defaultLibrary = libraries.data?.filter((l) => l.is_default);
  defaultLibrary ??= [];

  let defaultValues = {
    title: "",
    library_id: defaultLibrary.length > 0 ? defaultLibrary[0].id_ : null,
    title_local: "",
    desired_format: "",
    season: 1,
    episode_offset: 0,
    watch: true,
    preferred_resolution: "0",
    preferred_release_group: "",
  };

  const { register, handleSubmit, reset, setValue } = useForm({
    defaultValues: defaultValues,
  });

  const [isAddingAlreadySeen, setIsAddingAlreadySeen] =
    useState<boolean>(false);

  useEffect(() => {
    setIsAddingAlreadySeen(false);
    reset(defaultValues);
  }, [currentModal]);

  const submitHandler: SubmitHandler<AddShowFormValues> = (
    formData: AddShowFormValues
  ) => {
    mutation.mutate(formData);
  };

  const cancel = () => {
    if (mutation.isLoading) return;

    setCurrentModal(null);
  };

  return (
    <div
      className={
        "modal modal-fx-fadeInScale " +
        (currentModal === "add" ? "is-active" : "")
      }
    >
      <div className="modal-background" onClick={cancel}></div>
      <div className="modal-card">
        <header className="modal-card-head">
          <p className="modal-card-title">{_("add-modal-header")}</p>
          <div className="buttons">
            <ShowToggleButton
              setValue={setValue}
              attribute="watch"
              onIcon="eye"
              offIcon="eye-outline"
              onTooltip={_("watching-enabled")}
              offTooltip={_("watching-disabled")}
              additionalClasses="is-success"
              showLabel={true}
              labelOn={_("Watching")}
              labelOff={_("Not Watching")}
            />
          </div>
        </header>

        <section className="modal-card-body">
          {isAddingAlreadySeen ? (
            <AlreadySeenAddFormComponent
              setValue={setValue}
              setIsAddingAlreadySeen={setIsAddingAlreadySeen}
            />
          ) : (
            <form id="add-show-form" onSubmit={handleSubmit(submitHandler)}>
              <ShowForm
                mode="add"
                register={register}
                generalConfig={generalConfig}
              />
            </form>
          )}
        </section>

        <footer className="modal-card-foot is-flex is-justify-content-space-between">
          <div>
            {!isAddingAlreadySeen && (
              <button
                className={
                  "button is-success " +
                  (mutation.isLoading ? "is-loading" : "")
                }
                type="submit"
                form="add-show-form"
              >
                {_("add-form-add-button")}
              </button>
            )}
            <button className="button" onClick={cancel}>
              {_("add-form-cancel-button")}
            </button>
          </div>

          <div>
            <button
              className="button is-link"
              onClick={() => setIsAddingAlreadySeen(!isAddingAlreadySeen)}
            >
              {isAddingAlreadySeen
                ? _("add-form-mode-manual")
                : _("add-form-mode-discover")}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
};

interface AlreadySeenAddFormComponentParams {
  setValue: UseFormSetValue<AddShowFormValues>;
  setIsAddingAlreadySeen: Dispatch<SetStateAction<boolean>>;
}

const AlreadySeenAddFormComponent = ({
  setValue,
  setIsAddingAlreadySeen,
}: AlreadySeenAddFormComponentParams) => {
  const [selectedValue, setSelectedValue] = useState<string | null>(null);

  const [previousTitle, setPreviousTitle] = useState<string | null>(null);
  const [selectedTitle, setSelectedTitle] = useState<string | null>(null);
  const [selectedReleaseGroup, setSelectedReleaseGroup] = useState<
    string | null
  >(null);
  const [selectedResolution, setSelectedResolution] = useState<string | null>(
    null
  );

  const seenTitles = useQuery("seenTitles", async () =>
    fetchDistinctSeenReleases("title")
  );
  const seenGroups = useQuery(["seenGroups", selectedTitle], async () =>
    fetchDistinctSeenReleases("release_group", { title: selectedTitle })
  );
  const seenResolutions = useQuery(
    ["seenResolutions", selectedTitle, selectedReleaseGroup],
    async () =>
      fetchDistinctSeenReleases("resolution", {
        title: selectedTitle,
        release_group: selectedReleaseGroup,
      })
  );

  const seenReleases = useQuery(
    ["seenReleases", selectedTitle, selectedReleaseGroup, selectedResolution],
    async () =>
      fetchFilteredSeenReleases({
        title: selectedTitle,
        release_group: selectedReleaseGroup,
        resolution: selectedResolution,
      })
  );

  if (
    !seenTitles.isFetched ||
    !seenGroups.isFetched ||
    !seenResolutions.isFetched ||
    !seenReleases.isFetched
  ) {
    return (
      <div
        className="select is-multiple is-fullwidth"
        style={{ height: "33vh" }}
      >
        <select size={8} style={{ height: "100%" }}></select>
      </div>
    );
  }

  const setSelection = (e: ChangeEvent<HTMLSelectElement>) => {
    setSelectedValue(e.target.value);
  };

  const finalize = () => {
    setValue("title", selectedTitle);
    setValue("preferred_release_group", selectedReleaseGroup);
    setValue("preferred_resolution", selectedResolution);

    setIsAddingAlreadySeen(false);
  };

  const next = () => {
    if (!selectedValue) return;

    if (!selectedTitle) {
      setSelectedTitle(selectedValue);
      setPreviousTitle(selectedValue);
    } else if (!selectedReleaseGroup) setSelectedReleaseGroup(selectedValue);
    else if (!selectedResolution) setSelectedResolution(selectedValue);

    setSelectedValue(null);
  };

  const back = () => {
    if (!selectedTitle) return;
    else if (!selectedReleaseGroup) {
      setSelectedTitle(null);
      setSelectedValue(previousTitle);
      return;
    } else if (!selectedResolution) setSelectedReleaseGroup(null);
    else if (selectedResolution) setSelectedResolution(null);

    setSelectedValue(null);
  };

  const currentStage = (): string => {
    if (!selectedTitle) return "title";
    else if (!selectedReleaseGroup) return "release-group";
    else if (!selectedResolution) return "resolution";
    else return "result";
  };

  const canGoNext = (): boolean => {
    return selectedValue && selectedResolution === null;
  };

  const canGoBack = (): boolean => {
    return currentStage() !== "title";
  };

  if (currentStage() == "result") {
    let seenEpisodes = seenReleases.data.map((release) => release.episode);

    return (
      <>
        <h4 className="is-size-4 has-text-centered">
          [{selectedReleaseGroup}] {selectedTitle} - {selectedResolution}
        </h4>

        <p className="mt-1 has-text-centered">
          {_("add-form-discover-mode-result-amount", {
            releaseCount: seenReleases.data.length,
          })}
        </p>

        <h5 className="is-size-5 has-text-centered mt-2">
          {_("add-form-discover-mode-seen-episodes")}
        </h5>
        <p className="has-text-centered">{seenEpisodes.join(", ")}</p>

        <div className="is-flex mt-5">
          <button
            onClick={back}
            disabled={!canGoBack()}
            className="button is-danger is-flex-grow-1 mr-1"
          >
            Back
          </button>
          <button
            onClick={finalize}
            className="button is-success is-flex-grow-1 ml-1"
          >
            Next
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <h5 className="is-size-5 has-text-centered mb-1">
        {selectedReleaseGroup !== null ? `[${selectedReleaseGroup}] ` : ""}
        {selectedTitle !== null ? selectedTitle : ""}
        {selectedResolution !== null ? ` - ${selectedResolution}` : ""}
      </h5>

      {currentStage() == "title" && (
        <p className="mb-1">{_("add-form-discover-select-title")}</p>
      )}
      {currentStage() == "release-group" && (
        <p className="mb-1">{_("add-form-discover-select-release-group")}</p>
      )}
      {currentStage() == "resolution" && (
        <p className="mb-1">{_("add-form-discover-select-resolution")}</p>
      )}

      <div
        className="select is-multiple is-fullwidth"
        style={{ height: "33vh" }}
      >
        <select
          value={selectedValue ? selectedValue : undefined}
          onChange={setSelection}
          size={8}
          style={{ height: "100%" }}
        >
          {currentStage() === "title" &&
            seenTitles.data.map((title, i) => (
              <option key={i} value={title}>
                {title}
              </option>
            ))}
          {currentStage() === "release-group" &&
            seenGroups.data.map((group, i) => (
              <option key={i} value={group}>
                {group}
              </option>
            ))}
          {currentStage() === "resolution" &&
            seenResolutions.data.map((resolution, i) => (
              <option key={i} value={resolution}>
                {resolution}
              </option>
            ))}
        </select>
      </div>

      <div className="is-flex mt-2">
        <button
          onClick={back}
          disabled={!canGoBack()}
          className="button is-danger is-flex-grow-1 mr-1"
        >
          Back
        </button>
        <button
          onClick={next}
          disabled={!canGoNext()}
          className="button is-success is-flex-grow-1 ml-1"
        >
          Next
        </button>
      </div>
    </>
  );
};
