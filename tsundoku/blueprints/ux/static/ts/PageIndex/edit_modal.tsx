import { getInjector } from "../fluent";
import {
  useState,
  useEffect,
  Dispatch,
  SetStateAction,
  ChangeEvent,
} from "react";
import { useForm } from "react-hook-form";

import { ShowToggleButton } from "./components/show_toggle_button";
import { Show, Entry, Webhook, APIResponse } from "../interfaces";
import { IonIcon } from "../icon";
import { useMutation, useQueryClient } from "react-query";
import { updateShowById } from "../queries";
import { toast } from "bulma-toast";
import { NyaaSearchPanel } from "./NyaaSearchPanel";
import { EditShowForm } from "./components/EditShowForm";
import { EditShowEntries } from "./components/EditShowEntries";
import { EditShowWebhooks } from "./components/EditShowWebhooks";

const _ = getInjector();

interface EditModalParams {
  activeShow?: Show;
  setActiveShow: Dispatch<SetStateAction<Show | null>>;
  currentModal?: string;
  setCurrentModal: Dispatch<SetStateAction<string | null>>;
}

export const EditModal = ({
  activeShow,
  setActiveShow,
  currentModal,
  setCurrentModal,
}: EditModalParams) => {
  const [tab, setTab] = useState<string>("info");
  const [fixMatch, setFixMatch] = useState<boolean>(false);

  const [entriesToAdd, setEntriesToAdd] = useState<Entry[]>([]);
  const [entriesToDelete, setEntriesToDelete] = useState<Entry[]>([]);
  const [webhooksToUpdate, setWebhooksToUpdate] = useState<Webhook[]>([]);

  const [highlightNewEntryId, setHighlightNewEntryId] = useState<number | null>(
    null
  );

  const { register, reset, trigger, getValues, setValue } = useForm();

  const queryClient = useQueryClient();

  const showMutation = useMutation(updateShowById, {
    onSuccess: async (updatedShow) => {
      updatedShow = await finalizeEntries(updatedShow);
      updatedShow = await finalizeWebhooks(updatedShow);

      // Instead of manually updating the cache, just refetch the paginated shows queries
      queryClient.invalidateQueries(["shows"]);

      // Reset local state after save
      setEntriesToAdd([]);
      setEntriesToDelete([]);
      setHighlightNewEntryId(null);

      toast({
        message: _("show-update-success"),
        duration: 5000,
        position: "bottom-right",
        type: "is-success",
        dismissible: true,
        animate: { in: "fadeIn", out: "fadeOut" },
      });

      setCurrentModal(null);
      setActiveShow(null);
    },
  });

  register("watch", { required: true });

  useEffect(() => {
    if (activeShow) {
      setFixMatch(false);
      setTab("info");
      reset({
        title: activeShow.title,
        library_id: activeShow.library_id,
        title_local: activeShow.title_local,
        desired_format: activeShow.desired_format,
        season: activeShow.season,
        episode_offset: activeShow.episode_offset,
        watch: activeShow.watch,
        kitsu_id: activeShow.metadata.kitsu_id,
        preferred_resolution: activeShow.preferred_resolution ?? "0",
        preferred_release_group: activeShow.preferred_release_group,
      });
    }
  }, [activeShow]);

  const finalizeEntries = async (show: Show) => {
    let addedEntries: Entry[] = [];
    let removedEntries: Entry[] = [];

    let request: Object;
    if (entriesToAdd.length > 0) {
      request = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify([
          ...entriesToAdd.filter(
            (entry) =>
              entriesToDelete.findIndex(
                (toRemove: Entry) => toRemove.id === entry.id
              ) === -1
          ),
        ]),
      };

      let response = await fetch(
        `/api/v1/shows/${activeShow.id_}/entries`,
        request
      );
      if (response.ok) {
        let data: APIResponse<Entry[]> = await response.json();
        addedEntries = data.result;
      }
    }

    request = {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    };

    for (const entry of entriesToDelete) {
      if (entry.id < 0) continue;
      let response = await fetch(
        `/api/v1/shows/${activeShow.id_}/entries/${entry.id}`,
        request
      );
      if (response.ok) removedEntries.push(entry);
    }

    setEntriesToAdd([]);
    setEntriesToDelete([]);

    let newShow: Show = JSON.parse(JSON.stringify(show));
    for (const entry of addedEntries) newShow.entries.push(entry);

    for (const entry of removedEntries) {
      let idx = newShow.entries.findIndex(
        (toRemove) => toRemove.id === entry.id
      );
      if (idx !== -1) newShow.entries.splice(idx, 1);
    }

    newShow.entries.sort((a, b) => {
      return a.episode > b.episode ? 1 : -1;
    });

    return newShow;
  };

  const finalizeWebhooks = async (show: Show) => {
    let updatedWebhooks: Webhook[] = [];

    for (const wh of webhooksToUpdate) {
      let request = {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          triggers: wh.triggers.join(","),
        }),
      };

      let resp = await fetch(
        `/api/v1/shows/${show.id_}/webhooks/${wh.base.base_id}`,
        request
      );
      let resp_json: any;
      if (resp.ok) resp_json = await resp.json();
      else continue;

      updatedWebhooks.push(resp_json.result);
    }

    let newShow: Show = JSON.parse(JSON.stringify(show));

    for (const wh of updatedWebhooks) {
      let idx = newShow.webhooks.findIndex(
        (toReplace) => toReplace.base.base_id === wh.base.base_id
      );
      if (idx === -1) continue;

      newShow.webhooks[idx] = wh;
    }

    return newShow;
  };

  const anyMutationIsLoading = (): boolean => {
    return showMutation.isLoading;
  };

  const cancel = () => {
    if (anyMutationIsLoading()) return;

    setActiveShow(null);
    setCurrentModal(null);
  };

  const submitHandler = (data: any) => {
    showMutation.mutate({ id_: activeShow.id_, ...data });
  };

  const triggerForm = async () => {
    await trigger();
    submitHandler(getValues());
  };

  return (
    <div
      className={
        "modal modal-fx-fadeInScale " +
        (activeShow && currentModal === "edit" ? "is-active" : "")
      }
    >
      <div className="modal-background" onClick={cancel}></div>
      <div
        className={"modal-card" + (tab === "entries" ? " is-wide" : "")}
        style={{
          maxWidth: tab === "entries" ? "90vw" : undefined,
          width: tab === "entries" ? "1200px" : undefined,
          height: "80vh",
          maxHeight: "80vh",
          transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)",
          overflow: "hidden",
        }}
      >
        <header className="modal-card-head">
          <p className="modal-card-title">{_("edit-modal-header")}</p>
          <div className="buttons">
            <ShowToggleButton
              show={activeShow}
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
            <div
              className={"dropdown is-right " + (fixMatch ? "is-active" : "")}
            >
              <div className="dropdown-trigger">
                <button
                  className="button is-link"
                  onClick={() => setFixMatch(!fixMatch)}
                >
                  {_("edit-fix-match")}
                </button>
              </div>
              <div className="dropdown-menu" style={{ minWidth: "20rem" }}>
                <div className="dropdown-content">
                  <FixMatchDropdown
                    show={activeShow}
                    register={register}
                    setValue={setValue}
                  />
                </div>
              </div>
            </div>
          </div>
        </header>

        <section className="modal-card-body">
          <div className="tabs">
            <ul>
              <li className={tab === "info" ? "is-active" : ""}>
                <a onClick={() => setTab("info")}>{_("edit-tab-info")}</a>
              </li>
              <li className={tab === "entries" ? "is-active" : ""}>
                <a onClick={() => setTab("entries")}>{_("edit-tab-entries")}</a>
              </li>
              <li className={tab === "webhooks" ? "is-active" : ""}>
                <a onClick={() => setTab("webhooks")}>
                  {_("edit-tab-webhooks")}
                </a>
              </li>
            </ul>
          </div>

          <EditShowForm tab={tab} show={activeShow} register={register} />
          {/* Entries Tab: show both entries list and Nyaa search panel */}
          {tab === "entries" && activeShow && (
            <div>
              <EditShowEntries
                tab={tab}
                show={activeShow}
                setEntriesToAdd={setEntriesToAdd}
                setEntriesToDelete={setEntriesToDelete}
                entriesToAdd={entriesToAdd}
                entriesToDelete={entriesToDelete}
                highlightNewEntryId={highlightNewEntryId}
              />
              <hr style={{ margin: "2rem 0" }} />
              <h3 className="title is-5" style={{ marginBottom: "1rem" }}>
                {_("edit-entries-add-from-nyaa")}
              </h3>
              <NyaaSearchPanel
                initialQuery={activeShow.title}
                showId={activeShow.id_}
                existingEpisodes={getAllEpisodes(activeShow, entriesToAdd)}
                onEntryAdd={async (entry, overwrite) => {
                  const request = {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      show_id: activeShow.id_,
                      torrent_link: entry.torrent_link,
                      overwrite: overwrite,
                    }),
                  };
                  try {
                    const response = await fetch("/api/v1/nyaa", request);
                    if (response.ok) {
                      const data = await response.json();
                      if (data.result && Array.isArray(data.result)) {
                        setEntriesToAdd((prev) => [...data.result, ...prev]);
                        setHighlightNewEntryId(data.result[0]?.id ?? null); // highlight the first new entry
                        toast({
                          message: _("entry-add-success", {
                            count: data.result.length,
                          }),
                          duration: 4000,
                          position: "bottom-right",
                          type: "is-success",
                          dismissible: true,
                          animate: { in: "fadeIn", out: "fadeOut" },
                        });
                      }
                    } else {
                      toast({
                        message: _("entry-add-failed"),
                        duration: 4000,
                        position: "bottom-right",
                        type: "is-danger",
                        dismissible: true,
                        animate: { in: "fadeIn", out: "fadeOut" },
                      });
                    }
                  } catch (e) {
                    toast({
                      message: _("entry-add-failed"),
                      duration: 4000,
                      position: "bottom-right",
                      type: "is-danger",
                      dismissible: true,
                      animate: { in: "fadeIn", out: "fadeOut" },
                    });
                  }
                }}
              />
            </div>
          )}
          <EditShowWebhooks
            tab={tab}
            show={activeShow}
            webhooksToUpdate={webhooksToUpdate}
            setWebhooksToUpdate={setWebhooksToUpdate}
          />
        </section>

        <footer className="modal-card-foot">
          <button
            className={
              "button is-success " +
              (anyMutationIsLoading() ? "is-loading" : "")
            }
            onClick={triggerForm}
          >
            {_("edit-form-save-button")}
          </button>
          <button className="button" onClick={cancel}>
            {_("edit-form-cancel-button")}
          </button>
        </footer>
      </div>
    </div>
  );
};

interface FixMatchDropdownParams {
  show: Show;
  register: any;
  setValue: any;
}

interface KitsuAPIResultItem {
  id: string;
  type: string;
  attributes: any;
}

interface KitsuAPIResult {
  data: KitsuAPIResultItem[];
}

interface FixMatchRowParams {
  result: KitsuAPIResultItem;
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

const FixMatchRow = ({
  result,
  selectedId,
  setSelectedId,
}: FixMatchRowParams) => {
  const setSelf = () => {
    if (selectedId === result.id) setSelectedId("");
    else setSelectedId(result.id);
  };

  return (
    <tr
      onClick={setSelf}
      className={
        "is-clickable " + (result.id === selectedId ? "is-selected" : "")
      }
    >
      <td>{result.attributes.titles["en_jp"]}</td>
    </tr>
  );
};

const FixMatchDropdown = ({
  show,
  register,
  setValue,
}: FixMatchDropdownParams) => {
  const [isSearching, setSearchingState] = useState<boolean>(false);
  const [results, setResults] = useState<KitsuAPIResultItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");

  const waitInterval: number = 2250;

  let query: string = "";
  let queryTimer: number = 0;

  useEffect(() => {
    if (selectedId) setValue("kitsu_id", selectedId);
    else if (show && selectedId === "") {
      setValue("kitsu_id", show.metadata.kitsu_id);
    }
  }, [selectedId]);

  useEffect(() => {
    query = "";
    setSelectedId("");
    setResults([]);
  }, [show]);

  const updateResults = async () => {
    if (query === "") {
      setResults([]);
      return;
    }

    setSearchingState(true);

    let requestUrl = "https://kitsu.io/api/edge/anime?fields[anime]=id,titles";
    if (/^\d+$/.test(query)) requestUrl += `&filter[id]=${query}`;
    else requestUrl += `&filter[text]=${encodeURIComponent(query)}`;

    const resp = await fetch(requestUrl);
    let resp_json: KitsuAPIResult;
    if (resp.ok) resp_json = await resp.json();
    else {
      setSearchingState(false);
      return;
    }
    setResults(resp_json.data);

    setSearchingState(false);
  };

  const updateQuery = (e: ChangeEvent<HTMLInputElement>) => {
    query = e.target.value;

    setSearchingState(false);
    window.clearTimeout(queryTimer);
    queryTimer = window.setTimeout(updateResults, waitInterval);
  };

  return (
    <>
      <input type="hidden" {...register("kitsu_id")} />
      <div className="dropdown-item">
        <div
          className={
            "control has-icons-left " + (isSearching ? "is-loading" : "")
          }
        >
          <input
            type="text"
            className="input is-small"
            onInput={updateQuery}
            placeholder="Attack on Titan"
            disabled={isSearching}
          />
          <span className="icon is-small is-left">
            <IonIcon name="search" />
          </span>
        </div>
      </div>
      {results.length !== 0 && (
        <div className="dropdown-item">
          <table className="table is-fullwidth is-hoverable">
            <tbody>
              {results.slice(0, 5).map((result) => (
                <FixMatchRow
                  key={result.id}
                  result={result}
                  selectedId={selectedId}
                  setSelectedId={setSelectedId}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

// Helper to get all episode numbers from show.entries and entriesToAdd
function getAllEpisodes(show: Show, entriesToAdd: Entry[]): number[] {
  const all = new Set<number>();
  (show.entries || []).forEach((e: Entry) => all.add(e.episode));
  (entriesToAdd || []).forEach((e: Entry) => all.add(e.episode));
  return Array.from(all);
}
