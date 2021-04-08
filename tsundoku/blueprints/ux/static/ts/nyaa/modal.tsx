import { NyaaIndividualResult, Show } from "../interfaces";

import { toast } from "bulma-toast";
import { useState, useEffect, StateUpdater } from "preact/hooks";
import { useForm } from "react-hook-form";
import { getInjector } from "../fluent";


let resources = [
    "nyaa_search"
];

const _ = getInjector(resources);


interface NyaaShowModalParams {
    shows: Show[];
    setChoice: StateUpdater<NyaaIndividualResult>;
    choice?: NyaaIndividualResult;
}

export const NyaaShowModal = ({ setChoice, choice, shows }: NyaaShowModalParams) => {

    let addingDefaultState = false;
    if (shows.length)
        addingDefaultState = true;

    const [submitting, setSubmitting] = useState<boolean>(false);
    const [addingToExisting, setAddingToExisting] = useState<boolean>(addingDefaultState);
    const [showId, setShowId] = useState<number>(null);
    const [doOverwrite, setDoOverwrite] = useState<boolean>(false);

    const addToExisting = () => {
        setAddingToExisting(true);
    }

    const addNewShow = () => {
        setAddingToExisting(false);
    }

    useEffect(() => {
        if (showId === null)
            return;

        let request = {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ "show_id": showId, "torrent_link": choice.torrent_link, "overwrite": doOverwrite })
        }

        fetch("/api/v1/nyaa", request)
            .then((res: any) => {
                if (res.ok)
                    return res.json();
                else
                    setSubmitting(false);
            })
            .then((res: any) => {
                let addedCount: number = res.result.length;
                setSubmitting(false);
                setChoice(null);
                setAddingToExisting(true);
                setShowId(null);
                toast({
                    message: _("entry-add-success", { "count": addedCount }),
                    duration: 5000,
                    position: "bottom-right",
                    type: "is-success",
                    dismissible: true,
                    animate: { in: "fadeIn", out: "fadeOut" }
                })
            });

    }, [showId]);

    const returnCallback = (data: any) => {
        if ("overwrite" in data)
            setDoOverwrite(data.overwrite);
        if ("showId" in data)
            setShowId(data.showId);
    }

    const closeModal = () => {
        setChoice(null);
    }

    return (
        <div id="upsert-show-modal" class={"modal modal-fx-fadeInScale " + (choice ? "is-active" : "")}>
            <div class="modal-background" onClick={submitting ? null : closeModal}></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">{_("modal-title")}</p>
                    <button onClick={submitting ? null : closeModal} class="delete" aria-label="close"></button>
                </header>

                <section class="modal-card-body">
                    <div class="tabs is-centered is-toggle is-toggle-rounded">
                        <ul>
                            <li class={addingToExisting ? "" : "is-active"}><a onClick={addNewShow}>
                                <span class="icon is-small"><i class="fas fa-plus-circle"></i></span>
                                <span>{_("modal-tab-new")}</span>
                            </a></li>
                            <li class={addingToExisting ? "is-active" : ""}>
                                <a
                                    onClick={shows.length ? addToExisting : null}
                                    style={shows.length ? {} : { cursor: "auto" }}
                                    class={shows.length ? "" : "has-text-grey-light"}
                                >
                                    <span class="icon is-small"><i class="fas fa-pen-square"></i></span>
                                    <span>{_("modal-tab-existing")}</span>
                                </a>
                            </li>
                        </ul>
                    </div>
                    <ModalForm addingToExisting={addingToExisting} setSubmitting={setSubmitting} returnCallback={returnCallback} shows={shows} />
                </section>

                <footer class="modal-card-foot is-size-7">
                    <button class={"button is-success " + (submitting ? "is-loading" : "")} type="submit" form="nyaa-result-form">{_("add-button")}</button>
                    <button onClick={submitting ? null : closeModal} class="button">{_("cancel-button")}</button>
                </footer>
            </div>
        </div>
    )
}


interface ModalFormParams {
    addingToExisting: boolean;
    shows: Show[];
    setSubmitting: StateUpdater<boolean>;
    returnCallback?: any;
}


const ModalForm = ({ addingToExisting, shows, setSubmitting, returnCallback }: ModalFormParams) => {
    if (addingToExisting && shows.length)
        return (<AddToExistingShowForm setSubmitting={setSubmitting} returnCallback={returnCallback} shows={shows} />);
    else
        return (<AddShowForm setSubmitting={setSubmitting} returnCallback={returnCallback} />);
}


interface ExistingShowSelectInputs {
    register: any;
    name: string;
    shows: Show[];
}


const ExistingShowSelect = ({ register, name, shows }: ExistingShowSelectInputs) => {
    return (
        <select ref={register} name={name} required>
            {shows.map(show => (
                <option value={show.id_}>{show.title}</option>
            ))}
        </select>
    )
}


interface AddToExistingShowFormParams {
    shows: Show[];
    setSubmitting: StateUpdater<boolean>;
    returnCallback?: any;
}


interface AddToExistingShowFormInputs {
    existingShow: number;
    overwrite: boolean;
}



const AddToExistingShowForm = ({ setSubmitting, returnCallback, shows }: AddToExistingShowFormParams) => {
    const { register, handleSubmit } = useForm();

    const submitHandler = (data: AddToExistingShowFormInputs) => {
        setSubmitting(true);

        returnCallback({
            showId: data.existingShow,
            overwrite: data.overwrite
        });
    }

    return (
        <form onSubmit={handleSubmit(submitHandler)} id="nyaa-result-form" class="has-text-centered">
            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("existing-show-tt")}>{_("existing-show-field")}</span>
                </label>
                <div class="select is-fullwidth">
                    <ExistingShowSelect register={register} name="existingShow" shows={shows} />
                </div>
            </div>
            <label class="checkbox">
                <input ref={register} name="overwrite" type="checkbox" />
                <span class="ml-1">Overwrite existing entries?</span>
            </label>
        </form>
    )
}


interface AddShowFormInputs {
    title: string;
    desired_format: string;
    desired_folder: string;
    season: string;
    episode_offset: string;
}

interface AddShowFormParams {
    setSubmitting: StateUpdater<boolean>;
    returnCallback?: any;
}

const AddShowForm = ({ setSubmitting, returnCallback }: AddShowFormParams) => {
    const { register, handleSubmit } = useForm({
        defaultValues: {
            "season": "1",
            "episode_offset": 0
        }
    });

    const submitHandler = (data: AddShowFormInputs) => {
        setSubmitting(true);

        let request = {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        };

        fetch("/api/v1/shows", request)
            .then((res) => {
                if (res.ok)
                    return res.json();
                else
                    setSubmitting(false);
            })
            .then((res: any) => {
                if (typeof returnCallback !== 'undefined')
                    returnCallback({
                        showId: res.result.id_
                    });
                else
                    setSubmitting(false);
            })

    }

    return (
        <form onSubmit={handleSubmit(submitHandler)} id="nyaa-result-form">
            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("name-tt")}>{_("name-field")}</span>
                </label>
                <div class="control">
                    <input name="title" ref={register({ required: true })} class="input" type="text"
                        placeholder={_("name-placeholder")} />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("desired-format-tt")}>{_("desired-format-field")}</span>
                </label>
                <div class="control">
                    <input name="desired_format" ref={register} class="input" type="text" placeholder="{n} - {s00e00}" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("desired-folder-tt")}>{_("desired-folder-field")}</span>
                </label>
                <div class="control">
                    <input name="desired_folder" ref={register} class="input" type="text" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("season-tt")}>{_("season-field")}</span>
                </label>
                <div class="control">
                    <input name="season" ref={register({ required: true })} class="input" type="number" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("episode-offset-tt")}>{_("episode-offset-field")}</span>
                </label>
                <div class="control">
                    <input name="episode_offset" ref={register({ required: true })} class="input" type="number" />
                </div>
            </div>
        </form>
    )
}
