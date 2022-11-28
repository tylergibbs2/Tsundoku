import { getInjector } from "../fluent";
import { useState, useEffect, Dispatch, SetStateAction, ChangeEvent } from "react";
import { useForm } from "react-hook-form";

import humanizeDuration from "humanize-duration";

import { ShowToggleButton } from "./components/show_toggle_button";
import { Show, Entry, Webhook } from "../interfaces";
import { IonIcon } from "../icon";

let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


interface EditModalParams {
    activeShow?: Show;
    setActiveShow: Dispatch<SetStateAction<Show | null>>;
    currentModal?: string;
    setCurrentModal: Dispatch<SetStateAction<string | null>>;
    updateShow: any;
}


export const EditModal = ({ activeShow, setActiveShow, currentModal, setCurrentModal, updateShow }: EditModalParams) => {

    const [submitting, setSubmitting] = useState<boolean>(false);
    const [tab, setTab] = useState<string>("info");
    const [fixMatch, setFixMatch] = useState<boolean>(false);

    const [entriesToAdd, setEntriesToAdd] = useState<Entry[]>([]);
    const [entriesToDelete, setEntriesToDelete] = useState<Entry[]>([]);
    const [webhooksToUpdate, setWebhooksToUpdate] = useState<Webhook[]>([]);

    const { register, reset, trigger, getValues, setValue } = useForm();

    register("watch", { required: true });

    useEffect(() => {
        if (activeShow) {
            setFixMatch(false);
            setTab("info");
            reset({
                "title": activeShow.title,
                "desired_format": activeShow.desired_format,
                "desired_folder": activeShow.desired_folder,
                "season": activeShow.season,
                "episode_offset": activeShow.episode_offset,
                "watch": activeShow.watch,
                "kitsu_id": activeShow.metadata.kitsu_id
            })
        }
    }, [activeShow])

    const finalizeEntries = async (show: Show) => {
        let addedEntries: Entry[] = [];
        let removedEntries: Entry[] = [];

        let request: Object;
        for (const entry of entriesToAdd) {
            request = {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(entry)
            };

            let idx = entriesToDelete.findIndex((toRemove: Entry) => toRemove.id === entry.id);
            if (idx !== -1)
                continue;

            let resp = await fetch(`/api/v1/shows/${activeShow.id_}/entries`, request);
            let resp_json: any;
            if (resp.ok) {
                resp_json = await resp.json();
                addedEntries.push(resp_json.result);
            }
        }

        request = {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        };

        for (const entry of entriesToDelete) {
            if (entry.id < 0)
                continue;
            let resp = await fetch(`/api/v1/shows/${activeShow.id_}/entries/${entry.id}`, request);
            if (resp.ok) {
                removedEntries.push(entry);
            }
        }

        setEntriesToAdd([]);
        setEntriesToDelete([]);

        let newShow: Show = JSON.parse(JSON.stringify(show));
        for (const entry of addedEntries)
            newShow.entries.push(entry);

        for (const entry of removedEntries) {
            let idx = newShow.entries.findIndex((toRemove) => toRemove.id === entry.id)
            if (idx !== -1)
                newShow.entries.splice(idx, 1);
        }

        newShow.entries.sort((a, b) => {
            return a.episode > b.episode ? 1 : -1;
        });

        return newShow;
    }

    const finalizeWebhooks = async (show: Show) => {
        let updatedWebhooks: Webhook[] = [];

        for (const wh of webhooksToUpdate) {
            let request = {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    triggers: wh.triggers.join(",")
                })
            }

            let resp = await fetch(`/api/v1/shows/${show.id_}/webhooks/${wh.base.base_id}`, request);
            let resp_json: any;
            if (resp.ok)
                resp_json = await resp.json();
            else
                continue;

            updatedWebhooks.push(resp_json.result);
        }

        let newShow: Show = JSON.parse(JSON.stringify(show));

        for (const wh of updatedWebhooks) {
            let idx = newShow.webhooks.findIndex((toReplace) => toReplace.base.base_id === wh.base.base_id);
            if (idx === -1)
                continue;

            newShow.webhooks[idx] = wh;
        }

        return newShow;
    }

    const cancel = () => {
        if (submitting)
            return;

        setActiveShow(null);
        setCurrentModal(null);
    }

    const tabInfo = () => {
        setTab("info");
    }

    const tabEntries = () => {
        setTab("entries");
    }

    const tabWebhooks = () => {
        setTab("webhooks");
    }

    const submitHandler = async (data: any) => {
        setSubmitting(true);

        let newShow: Show;
        if (Object.keys(data).length !== 0) {
            let request = {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            };

            const resp = await fetch(`/api/v1/shows/${activeShow.id_}`, request);
            let resp_json: any;
            if (resp.ok)
                resp_json = await resp.json();
            else {
                setSubmitting(false);
                return;
            }

            newShow = resp_json.result;
        } else
            newShow = JSON.parse(JSON.stringify(activeShow));

        newShow = await finalizeWebhooks(newShow);
        newShow = await finalizeEntries(newShow);

        updateShow(newShow);

        setSubmitting(false);
        setActiveShow(null);
        setCurrentModal(null);
        setSubmitting(false);
    }

    const triggerForm = async () => {
        await trigger();
        await submitHandler(getValues());
    }

    const fixMatchDropdown = () => {
        setFixMatch(!fixMatch);
    }

    return (
        <div className={"modal modal-fx-fadeInScale " + (activeShow && currentModal === "edit" ? "is-active" : "")}>
            <div className="modal-background" onClick={cancel}></div>
            <div className="modal-card">
                <header className="modal-card-head">
                    <p className="modal-card-title">{_("edit-modal-header")}</p>
                    <div className="buttons">
                        <ShowToggleButton
                            show={activeShow}
                            setValue={setValue}
                            attribute="post_process"
                            onIcon="color-wand"
                            offIcon="color-wand-outline"
                            onTooltip={_("unprocess-button-title")}
                            offTooltip={_("process-button-title")}
                            additionalClasses="is-primary"
                        />
                        <ShowToggleButton
                            show={activeShow}
                            setValue={setValue}
                            attribute="watch"
                            onIcon="bookmark"
                            offIcon="bookmark-outline"
                            onTooltip={_("unwatch-button-title")}
                            offTooltip={_("watch-button-title")}
                            additionalClasses="is-primary"
                        />
                        <div className={"dropdown is-right " + (fixMatch ? "is-active" : "")}>
                            <div className="dropdown-trigger">
                                <button className="button is-link" onClick={fixMatchDropdown}>
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
                            <li className={tab === "info" ? "is-active" : ""}><a onClick={tabInfo}>{_("edit-tab-info")}</a></li>
                            <li className={tab === "entries" ? "is-active" : ""}><a onClick={tabEntries}>{_("edit-tab-entries")}</a></li>
                            <li className={tab === "webhooks" ? "is-active" : ""}><a onClick={tabWebhooks}>{_("edit-tab-webhooks")}</a></li>
                        </ul>
                    </div>

                    <EditShowForm
                        tab={tab}
                        show={activeShow}
                        register={register}
                    />
                    <EditShowEntries
                        tab={tab}
                        show={activeShow}
                        setEntriesToAdd={setEntriesToAdd}
                        setEntriesToDelete={setEntriesToDelete}
                        entriesToAdd={entriesToAdd}
                        entriesToDelete={entriesToDelete}
                    />
                    <EditShowWebhooks
                        tab={tab}
                        show={activeShow}
                        webhooksToUpdate={webhooksToUpdate}
                        setWebhooksToUpdate={setWebhooksToUpdate}
                    />

                </section>

                <footer className="modal-card-foot">
                    <button className={"button is-success " + (submitting ? "is-loading" : "")} onClick={triggerForm}>{_("edit-form-save-button")}</button>
                    <button className="button closes-modals" onClick={cancel}>{_('edit-form-cancel-button')}</button>
                </footer>
            </div>
        </div>
    )
}


interface FixMatchDropdownParams {
    show: Show;
    register: any;
    setValue: any;
}


interface KitsuAPIResultItem {
    id: string;
    type: string;
    attributes: any
}


interface KitsuAPIResult {
    data: KitsuAPIResultItem[];
}


interface FixMatchRowParams {
    result: KitsuAPIResultItem;
    selectedId: string;
    setSelectedId: Dispatch<SetStateAction<string>>;
}


const FixMatchRow = ({ result, selectedId, setSelectedId }: FixMatchRowParams) => {
    const setSelf = () => {
        if (selectedId === result.id)
            setSelectedId("");
        else
            setSelectedId(result.id);
    }

    return (
        <tr onClick={setSelf} className={"is-clickable " + (result.id === selectedId ? "is-selected" : "")}>
            <td>{result.attributes.titles["en_jp"]}</td>
        </tr>
    )
}


const FixMatchDropdown = ({ show, register, setValue }: FixMatchDropdownParams) => {
    const [isSearching, setSearchingState] = useState<boolean>(false);
    const [results, setResults] = useState<KitsuAPIResultItem[]>([]);
    const [selectedId, setSelectedId] = useState<string>("");

    const waitInterval: number = 2250;

    let query: string = "";
    let queryTimer: number = 0;

    useEffect(() => {
        if (selectedId)
            setValue("kitsu_id", selectedId);
        else if (show && selectedId === "") {
            setValue("kitsu_id", show.metadata.kitsu_id);
        }
    }, [selectedId])

    useEffect(() => {
        query = "";
        setSelectedId("");
        setResults([]);
    }, [show])

    const updateResults = async () => {
        if (query === "") {
            setResults([]);
            return;
        }

        setSearchingState(true);

        let requestUrl = "https://kitsu.io/api/edge/anime?fields[anime]=id,titles";
        if (/^\d+$/.test(query))
            requestUrl += `&filter[id]=${query}`;
        else
            requestUrl += `&filter[text]=${encodeURIComponent(query)}`;

        const resp = await fetch(requestUrl);
        let resp_json: KitsuAPIResult;
        if (resp.ok)
            resp_json = await resp.json();
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
    }

    return (
        <>
            <input type="hidden" {...register("kitsu_id")} />
            <div className="dropdown-item">
                <div className={"control has-icons-left " + (isSearching ? "is-loading" : "")}>
                    <input type="text" className="input is-small" onInput={updateQuery} placeholder="Attack on Titan" disabled={isSearching} />
                    <span className="icon is-small is-left">
                        <IonIcon name="search" />
                    </span>
                </div>
            </div>
            {results.length !== 0 &&
                <div className="dropdown-item">
                    <table className="table is-fullwidth is-hoverable">
                        <tbody>
                            {
                                results.slice(0, 5).map((result) => (
                                    <FixMatchRow
                                        key={result.id}
                                        result={result}
                                        selectedId={selectedId}
                                        setSelectedId={setSelectedId}
                                    />
                                ))
                            }
                        </tbody>
                    </table>
                </div>
            }
        </>
    )
}


interface EditShowFormParams {
    tab: string;
    show: Show;
    register: any;
}

const EditShowForm = ({ tab, show, register }: EditShowFormParams) => {

    if (show === null)
        return (<></>)

    return (
        <form className={tab !== "info" ? "is-hidden" : ""} style={{
            overflow: "hidden auto"
        }}>
            <div className="form-columns columns is-multiline">
                <div className="column is-full">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("edit-form-name-tt")}>{_("edit-form-name-field")}</span>
                        </label>
                        <div className="control">
                            <input {...register("title", { required: true })} className="input" type="text"
                                placeholder={_("edit-form-name-placeholder")} />
                        </div>
                    </div>
                </div>

                <div className="column is-full">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("edit-form-desired-format-tt")}>{_("edit-form-desired-format-field")}</span>
                        </label>
                        <div className="control">
                            <input {...register("desired_format")} className="input" type="text" placeholder="{n} - {s00e00}" />
                        </div>
                    </div>
                </div>

                <div className="column is-full">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("edit-form-desired-folder-tt")}>{_("edit-form-desired-folder-field")}</span>
                        </label>
                        <div className="control">
                            <input {...register("desired_folder")} className="input" type="text" />
                        </div>
                    </div>
                </div>

                <div className="column is-half">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("edit-form-season-tt")}>{_("edit-form-season-field")}</span>
                        </label>
                        <div className="control">
                            <input {...register("season", { required: true })} className="input" type="number" />
                        </div>
                    </div>
                </div>

                <div className="column is-half">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-top"
                                data-tooltip={_("edit-form-episode-offset-tt")}>{_("edit-form-episode-offset-field")}</span>
                        </label>
                        <div className="control">
                            <input{...register("episode_offset", { required: true })} className="input" type="number" />
                        </div>
                    </div>
                </div>
            </div>
        </form>
    )
}


interface EditShowEntriesParams {
    tab: string;
    show: Show;
    setEntriesToAdd: Dispatch<SetStateAction<Entry[]>>;
    setEntriesToDelete: Dispatch<SetStateAction<Entry[]>>;
    entriesToAdd: Entry[];
    entriesToDelete: Entry[];
}


const EditShowEntries = ({ tab, show, setEntriesToAdd, setEntriesToDelete, entriesToAdd, entriesToDelete }: EditShowEntriesParams) => {
    if (show === null)
        return (<></>)

    const [entries, setEntries] = useState<any[]>(show.entries);
    const [fakeId, setFakeId] = useState<number>(-1);

    const { register, handleSubmit, reset } = useForm();

    useEffect(() => {
        setEntries(show.entries);
    }, [show]);

    const bufferAddEntry = (data: any) => {
        let newEpNum = parseInt(data.episode);
        if (newEpNum < 0) {
            reset();
            return;
        }

        let entry = {
            id: fakeId,
            episode: newEpNum,
            show_id: show.id_,
            state: "buffered",
            magnet: data.magnet,
            last_update: new Date().toISOString()
        }
        let temp = [entry, ...entries];

        let exists = entries.findIndex((existing: Entry) => existing.episode === newEpNum);
        if (exists !== -1) {
            reset();
            return;
        }

        setFakeId(fakeId - 1);

        temp.sort((a, b) => {
            return a.episode > b.episode ? 1 : -1;
        });

        setEntriesToAdd([entry, ...entriesToAdd]);
        setEntries(temp);

        reset();
    }

    const bufferRemoveEntry = (entry: Entry) => {
        let temp = [...entries];
        let idx = temp.findIndex((toRemove: Entry) => toRemove.id === entry.id);
        if (idx !== -1)
            temp.splice(idx, 1);

        setEntriesToDelete([entry, ...entriesToDelete]);
        setEntries(temp);
    }

    return (
        <div className={tab !== "entries" ? "is-hidden" : ""}>
            {entries.length > 0 &&
                <table className="table is-fullwidth is-hoverable">
                    <thead>
                        <tr>
                            <th>{_("edit-entries-th-episode")}</th>
                            <th>{_("edit-entries-th-status")}</th>
                            <th>{_("edit-entries-th-last-update")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            entries.map((entry: Entry) => (
                                <EntryRow
                                    key={entry.id}
                                    entry={entry}
                                    bufferRemoveEntry={bufferRemoveEntry}
                                />
                            ))
                        }
                    </tbody>
                </table>
            }
            {entries.length === 0 &&
                <div className="container has-text-centered mb-5">
                    <h2 className="subtitle">{_("edit-entries-is-empty")}</h2>
                </div>
            }
            {/*@ts-ignore */}
            <form onSubmit={handleSubmit(bufferAddEntry)}>
                <div className="field is-horizontal">
                    <div className="field-body">
                        <div className="field-label is-normal">
                            <label className="label">{_('edit-entries-form-episode')}</label>
                        </div>
                        <div className="field">
                            <input {...register('episode')} min="0" className="input" type="number" value="0" required />
                            <p className="help is-danger is-hidden">{_("edit-entries-form-exists")}</p>
                        </div>
                        <div className="field">
                            <input
                                {...register('magnet')}
                                className="input"
                                type="text"
                                placeholder={_('edit-entries-form-magnet')} />
                        </div>
                        <input className="button is-success" type="submit" value={_('edit-entries-form-add-button')} />
                    </div>
                </div>
            </form>
        </div>
    );
}


interface EntryRowParams {
    entry: Entry;
    bufferRemoveEntry: any;
}


const EntryRow = ({ entry, bufferRemoveEntry }: EntryRowParams) => {
    const bufferDelete = () => {
        bufferRemoveEntry(entry);
    }

    let timeString = entry.last_update + (entry.last_update.endsWith("Z") ? "" : "Z")

    const lastUpdate = new Date(timeString);
    const diff = lastUpdate.getTime() - Date.now();

    const localized = humanizeDuration(diff, {
        language: window["LOCALE"],
        fallbacks: ["en"],
        round: true,
        largest: 2
    })
    const localizedTitle = new Intl.DateTimeFormat(window["LOCALE"], {
        // @ts-ignore
        dateStyle: 'full',
        timeStyle: 'medium'
    }).format(lastUpdate)

    return (
        <tr>
            <td>{entry.episode}</td>
            <td>{_(`entry-status-${entry.state}`)}</td>
            <td title={localizedTitle}>{_("edit-entries-last-update", { time: localized })}</td>
            <td>
                <button className="delete" onClick={bufferDelete}></button>
            </td>
        </tr>
    )
}


interface EditShowWebhooksParams {
    tab: string;
    show: Show;
    webhooksToUpdate: Webhook[];
    setWebhooksToUpdate: Dispatch<SetStateAction<Webhook[]>>;
}


const EditShowWebhooks = ({ tab, show, webhooksToUpdate, setWebhooksToUpdate }: EditShowWebhooksParams) => {
    if (show === null)
        return (<></>)

    return (
        <div className={tab !== "webhooks" ? "is-hidden" : ""}>
            {show.webhooks.length !== 0 &&
                <table className="table is-fullwidth is-hoverable">
                    <thead>
                        <tr className="has-text-centered">
                            <th>{_("edit-webhooks-th-webhook")}</th>
                            <td>
                                <span className="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-downloading')}>
                                    <IonIcon name="download" />
                                </span>
                            </td>
                            <td>
                                <span className="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-downloaded')}>
                                    <IonIcon name="save" />
                                </span>
                            </td>
                            <td>
                                <span className="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-renamed')}>
                                    <IonIcon name="pencil-sharp" />
                                </span>
                            </td>
                            <td>
                                <span className="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-moved')}>
                                    <IonIcon name="arrow-forward-circle" />
                                </span>
                            </td>
                            <td>
                                <span className="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-completed')}>
                                    <IonIcon name="checkmark-circle" />
                                </span>
                            </td>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            show.webhooks.map((webhook) => (
                                <EditWebhookTableRow
                                    key={webhook.base.base_id}
                                    webhook={webhook}
                                    webhooksToUpdate={webhooksToUpdate}
                                    setWebhooksToUpdate={setWebhooksToUpdate}
                                />
                            ))
                        }
                    </tbody>
                </table>
            }
            {show.webhooks.length === 0 &&
                <div className="container has-text-centered mb-5">
                    <h2 className="subtitle">{_("edit-webhooks-is-empty")}</h2>
                </div>
            }
        </div>
    )
}


interface EditWebhookTableRowParams {
    webhook: Webhook;
    webhooksToUpdate: Webhook[];
    setWebhooksToUpdate: Dispatch<SetStateAction<Webhook[]>>;
}


const EditWebhookTableRow = ({ webhook, webhooksToUpdate, setWebhooksToUpdate }: EditWebhookTableRowParams) => {
    const [triggers, setTriggers] = useState(webhook.triggers);

    const { register } = useForm({
        defaultValues: {
            downloading: triggers.includes("downloading"),
            downloaded: triggers.includes("downloaded"),
            renamed: triggers.includes("renamed"),
            moved: triggers.includes("moved"),
            completed: triggers.includes("completed")
        }
    });

    const update = (e: any) => {
        let idx = triggers.findIndex(tr => tr === e.target.name);
        let newTrs: string[];
        if (idx === -1) {
            newTrs = [e.target.name, ...triggers];
            setTriggers(newTrs);
        } else {
            newTrs = [...triggers];
            newTrs.splice(idx, 1);
            setTriggers(newTrs);
        }

        let newWh: Webhook = JSON.parse(JSON.stringify(webhook));
        newWh.triggers = newTrs;

        idx = webhooksToUpdate.findIndex((toFind) => toFind.base.base_id === newWh.base.base_id);
        if (idx === -1)
            setWebhooksToUpdate([newWh, ...webhooksToUpdate]);
        else {
            let temp = [...webhooksToUpdate];
            temp[idx] = newWh;
            setWebhooksToUpdate(temp);
        }
    }

    return (
        <tr className="has-text-centered">
            <td className="is-vcentered">{webhook.base.name}</td>
            <td className="is-vcentered">
                <input type="checkbox" {...register('downloading')} onChange={update}></input>
            </td>
            <td className="is-vcentered">
                <input type="checkbox" {...register('downloaded')} onChange={update}></input>
            </td>
            <td className="is-vcentered">
                <input type="checkbox" {...register('renamed')} onChange={update}></input>
            </td>
            <td className="is-vcentered">
                <input type="checkbox" {...register('moved')} onChange={update}></input>
            </td>
            <td className="is-vcentered">
                <input type="checkbox" {...register('completed')} onChange={update}></input>
            </td>
        </tr>
    );
}
