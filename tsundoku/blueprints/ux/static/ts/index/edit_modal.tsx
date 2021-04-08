import { getInjector } from "../fluent";
import { useState, StateUpdater, useEffect } from "preact/hooks";
import { useForm } from "react-hook-form";
import { Show, Entry, Webhook } from "../interfaces";
import * as humanizeDuration from "humanize-duration";


let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


interface EditModalParams {
    activeShow?: Show;
    setActiveShow: StateUpdater<Show | null>;
    currentModal?: string;
    setCurrentModal: StateUpdater<string | null>;
    updateShow: any;
}


export const EditModal = ({ activeShow, setActiveShow, currentModal, setCurrentModal, updateShow }: EditModalParams) => {

    const [submitting, setSubmitting] = useState<boolean>(false);
    const [tab, setTab] = useState<string>("info");
    const [fixMatch, setFixMatch] = useState<boolean>(false);

    const [entriesToAdd, setEntriesToAdd] = useState<Entry[]>([]);
    const [entriesToDelete, setEntriesToDelete] = useState<Entry[]>([]);
    const [webhooksToUpdate, setWebhooksToUpdate] = useState<Webhook[]>([]);

    const { register, reset, trigger, getValues } = useForm();

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
        const result = await trigger();
        if (result)
            await submitHandler(getValues());
    }

    const clearCache = async () => {
        let request = {
            method: "DELETE"
        };

        let resp = await fetch(`/api/v1/shows/${activeShow.id_}/cache`, request);
        let resp_json: any;
        if (resp.ok)
            resp_json = await resp.json();
        else
            return;

        updateShow(resp_json.result);
    }

    const fixMatchDropdown = () => {
        setFixMatch(!fixMatch);
    }

    return (
        <div class={"modal modal-fx-fadeInScale " + (activeShow && currentModal === "edit" ? "is-active" : "")}>
            <div class="modal-background" onClick={cancel}></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">{_("edit-modal-header")}</p>
                    <div class="buttons">
                        <button class="button is-warning has-text-white" onClick={clearCache}>{_("edit-clear-cache")}</button>
                        <div class={"dropdown is-right " + (fixMatch ? "is-active" : "")}>
                            <div class="dropdown-trigger">
                                <button class="button is-link" onClick={fixMatchDropdown}>
                                    {_("edit-fix-match")}
                                </button>
                            </div>
                            <div class="dropdown-menu">
                                <div class="dropdown-content">
                                    <div class="dropdown-item">
                                        <p><strong>{_("edit-kitsu-id")}</strong></p>
                                    </div>
                                    <div class="dropdown-item">
                                        <input ref={register} name="kitsu_id" type="number" min="0" class="input" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>

                <section class="modal-card-body">
                    <div class="tabs">
                        <ul>
                            <li class={tab === "info" ? "is-active" : ""}><a onClick={tabInfo}>{_("edit-tab-info")}</a></li>
                            <li class={tab === "entries" ? "is-active" : ""}><a onClick={tabEntries}>{_("edit-tab-entries")}</a></li>
                            <li class={tab === "webhooks" ? "is-active" : ""}><a onClick={tabWebhooks}>{_("edit-tab-webhooks")}</a></li>
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

                <footer class="modal-card-foot">
                    <progress class="progress is-primary is-small mt-2 is-hidden" max="100"></progress>
                    <button class={"button is-success " + (submitting ? "is-loading" : "")} onClick={triggerForm}>{_("edit-form-save-button")}</button>
                    <button class="button closes-modals" onClick={cancel}>{_('edit-form-cancel-button')}</button>
                </footer>
            </div>
        </div>
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
        <form class={tab !== "info" ? "is-hidden" : ""}>
            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("edit-form-name-tt")}>{_("edit-form-name-field")}</span>
                </label>
                <div class="control">
                    <input name="title" ref={register({ required: true })} class="input" type="text"
                        placeholder={_("edit-form-name-placeholder")} />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("edit-form-desired-format-tt")}>{_("edit-form-desired-format-field")}</span>
                </label>
                <div class="control">
                    <input name="desired_format" ref={register} class="input" type="text" placeholder="{n} - {s00e00}" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("edit-form-desired-folder-tt")}>{_("edit-form-desired-folder-field")}</span>
                </label>
                <div class="control">
                    <input name="desired_folder" ref={register} class="input" type="text" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("edit-form-season-tt")}>{_("edit-form-season-field")}</span>
                </label>
                <div class="control">
                    <input name="season" ref={register({ required: true })} class="input" type="number" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("edit-form-episode-offset-tt")}>{_("edit-form-episode-offset-field")}</span>
                </label>
                <div class="control">
                    <input name="episode_offset" ref={register({ required: true })} class="input" type="number" />
                </div>
            </div>
        </form>
    )
}


interface EditShowEntriesParams {
    tab: string;
    show: Show;
    setEntriesToAdd: StateUpdater<Entry[]>;
    setEntriesToDelete: StateUpdater<Entry[]>;
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
        if (data.episode < 0) {
            reset();
            return;
        }

        let entry = {
            id: fakeId,
            episode: data.episode,
            show_id: show.id_,
            state: "buffered",
            magnet: data.magnet,
            last_update: ""
        }
        let temp = [entry, ...entries];

        let exists = entries.findIndex((existing: Entry) => existing.episode === data.episode);
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
        <div class={tab !== "entries" ? "is-hidden" : ""}>
            {entries.length > 0 &&
                <table class="table is-fullwidth is-hoverable">
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
                <div class="container has-text-centered mb-5">
                    <h2 class="subtitle">{_("edit-entries-is-empty")}</h2>
                </div>
            }
            <form onSubmit={handleSubmit(bufferAddEntry)}>
                <div class="field is-horizontal">
                    <div class="field-body">
                        <div class="field-label is-normal">
                            <label class="label">{_('edit-entries-form-episode')}</label>
                        </div>
                        <div class="field">
                            <input name="episode" class="input" ref={register} type="number" value="0" required />
                            <p class="help is-danger is-hidden">{_("edit-entries-form-exists")}</p>
                        </div>
                        <div class="field">
                            <input name="magnet" class="input" ref={register} type="text" placeholder={_('edit-entries-form-magnet')} />
                        </div>
                        <input class="button is-success" type="submit" value={_('edit-entries-form-add-button')} />
                    </div>
                </div>
            </form>
        </div>
    )
}


interface EntryRowParams {
    entry: Entry;
    bufferRemoveEntry: any;
}


const EntryRow = ({ entry, bufferRemoveEntry }: EntryRowParams) => {
    const bufferDelete = () => {
        bufferRemoveEntry(entry);
    }

    const lastUpdate = new Date(`${entry.last_update}Z`);
    const diff = lastUpdate.getTime() - Date.now();

    const localized = humanizeDuration(diff, {
        language: window["LOCALE"],
        fallbacks: ["en"],
        round: true,
        largest: 2
    })

    return (
        <tr>
            <td>{entry.episode}</td>
            <td>{_(`entry-status-${entry.state}`)}</td>
            <td>{_("edit-entries-last-update", {time: localized})}</td>
            <td>
                <button class="delete" onClick={bufferDelete}></button>
            </td>
        </tr>
    )
}


interface EditShowWebhooksParams {
    tab: string;
    show: Show;
    webhooksToUpdate: Webhook[];
    setWebhooksToUpdate: StateUpdater<Webhook[]>;
}


const EditShowWebhooks = ({ tab, show, webhooksToUpdate, setWebhooksToUpdate }: EditShowWebhooksParams) => {
    if (show === null)
        return (<></>)

    return (
        <div class={tab !== "webhooks" ? "is-hidden" : ""}>
            {show.webhooks.length !== 0 &&
                <table class="table is-fullwidth is-hoverable">
                    <thead>
                        <tr class="has-text-centered">
                            <th>{_("edit-webhooks-th-webhook")}</th>
                            <td>
                                <span class="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-downloading')}>
                                    <i class="fas fa-download"></i>
                                </span>
                            </td>
                            <td>
                                <span class="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-downloaded')}>
                                    <i class="fas fa-save"></i>
                                </span>
                            </td>
                            <td>
                                <span class="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-renamed')}>
                                    <i class="fas fa-pencil-alt"></i>
                                </span>
                            </td>
                            <td>
                                <span class="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-moved')}>
                                    <i class="fas fa-file-export"></i>
                                </span>
                            </td>
                            <td>
                                <span class="icon has-tooltip-arrow has-tooltip-up"
                                    data-tooltip={_('edit-webhooks-th-completed')}>
                                    <i class="fas fa-check-circle"></i>
                                </span>
                            </td>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            show.webhooks.map((webhook) => (
                                <EditWebhookTableRow
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
                <div class="container has-text-centered mb-5">
                    <h2 class="subtitle">{_("edit-webhooks-is-empty")}</h2>
                </div>
            }
        </div>
    )
}


interface EditWebhookTableRowParams {
    webhook: Webhook;
    webhooksToUpdate: Webhook[];
    setWebhooksToUpdate: StateUpdater<Webhook[]>;
}


const EditWebhookTableRow = ({ webhook, webhooksToUpdate, setWebhooksToUpdate }: EditWebhookTableRowParams) => {
    const { register, reset, getValues } = useForm();

    useEffect(() => {
        reset({
            downloading: webhook.triggers.includes("downloading"),
            downloaded: webhook.triggers.includes("downloaded"),
            renamed: webhook.triggers.includes("renamed"),
            moved: webhook.triggers.includes("moved"),
            completed: webhook.triggers.includes("completed")
        });
    }, [webhook]);

    const update = () => {
        let data = getValues();
        let triggers: string[] = [];
        for (const trigger in data) {
            if (data[trigger])
                triggers.push(trigger);
        }

        let newWh: Webhook = JSON.parse(JSON.stringify(webhook));
        newWh.triggers = triggers;

        let idx = webhooksToUpdate.findIndex((toFind) => toFind.base.base_id === newWh.base.base_id);
        if (idx === -1)
            setWebhooksToUpdate([newWh, ...webhooksToUpdate]);
        else {
            let temp = [...webhooksToUpdate];
            temp[idx] = newWh;
            setWebhooksToUpdate(temp);
        }
    }

    return (
        <tr class="has-text-centered">
            <td class="is-vcentered">{webhook.base.name}</td>
            <td class="is-vcentered">
                <input type="checkbox" ref={register} onChange={update} name="downloading"></input>
            </td>
            <td class="is-vcentered">
                <input type="checkbox" ref={register} onChange={update} name="downloaded"></input>
            </td>
            <td class="is-vcentered">
                <input type="checkbox" ref={register} onChange={update} name="renamed"></input>
            </td>
            <td class="is-vcentered">
                <input type="checkbox" ref={register} onChange={update} name="moved"></input>
            </td>
            <td class="is-vcentered">
                <input type="checkbox" ref={register} onChange={update} name="completed"></input>
            </td>
        </tr>
    )
}
