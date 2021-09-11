import { NyaaIndividualResult, Show } from "../interfaces";

import { toast } from "bulma-toast";
import { useState, useEffect, StateUpdater } from "preact/hooks";
import { useForm } from "react-hook-form";
import { getInjector } from "../fluent";
import { IonIcon } from "../icon";
import { ShowToggleButton } from "../index/components/show_toggle_button";


let resources = [
    "base",
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
    const [watch, setWatch] = useState<boolean>(false);
    const [postProcess, setPostProcess] = useState<boolean>(false);

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

    const receiveWatch = (_: any, state: boolean) => {
        setWatch(state);
    }

    const receivePostProcess = (_: any, state: boolean) => {
        setPostProcess(state);
    }

    return (
        <div id="upsert-show-modal" class={"modal modal-fx-fadeInScale " + (choice ? "is-active" : "")}>
            <div class="modal-background" onClick={submitting ? null : closeModal}></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">{_("modal-title")}</p>
                    <div class="buttons">
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

                <section class="modal-card-body">
                    <div class="tabs is-centered is-toggle is-toggle-rounded">
                        <ul>
                            <li class={addingToExisting ? "" : "is-active"}><a onClick={addNewShow}>
                                <span class="icon is-small"><IonIcon name="add-circle" /></span>
                                <span>{_("modal-tab-new")}</span>
                            </a></li>
                            <li class={addingToExisting ? "is-active" : ""}>
                                <a
                                    onClick={shows.length ? addToExisting : null}
                                    style={shows.length ? {} : { cursor: "auto" }}
                                    class={shows.length ? "" : "has-text-grey-light"}
                                >
                                    <span class="icon is-small"><IonIcon name="pencil-sharp" /></span>
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
                    />
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
    watch: boolean;
    postProcess: boolean;
}


const ModalForm = ({ addingToExisting, shows, setSubmitting, returnCallback, watch, postProcess }: ModalFormParams) => {
    if (addingToExisting && shows.length)
        return (<AddToExistingShowForm setSubmitting={setSubmitting} returnCallback={returnCallback} shows={shows} />);
    else
        return (<AddShowForm setSubmitting={setSubmitting} returnCallback={returnCallback} watch={watch} postProcess={postProcess} />);
}


interface ExistingShowSelectInputs {
    register: any;
    name: string;
    shows: Show[];
}


const ExistingShowSelect = ({ register, name, shows }: ExistingShowSelectInputs) => {
    return (
        <select {...register(name, { required: true })} required>
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
        // @ts-ignore
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
                <input {...register('overwrite')} type="checkbox" />
                <span class="ml-1">Overwrite existing entries?</span>
            </label>
        </form>
    );
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
    watch: boolean;
    postProcess: boolean;
}

const AddShowForm = ({ setSubmitting, returnCallback, watch, postProcess }: AddShowFormParams) => {
    const { register, handleSubmit, setValue } = useForm({
        defaultValues: {
            "title": "",
            "desired_format": "",
            "desired_folder": "",
            "season": 1,
            "episode_offset": 0,
            "watch": true,
            "post_process": true
        }
    });

    useEffect(() => {
        setValue("watch", watch);
        setValue("post_process", postProcess)
    }, [watch, postProcess])

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
        // @ts-ignore
        <form onSubmit={handleSubmit(submitHandler)} id="nyaa-result-form">
            <div class="form-columns columns is-multiline">
                <div class="column is-full">
                    <div class="field">
                        <label class="label">
                            <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("name-tt")}>{_("name-field")}</span>
                        </label>
                        <div class="control">
                            <input {...register("title", { required: true })} class="input" type="text"
                                placeholder={_("name-placeholder")} />
                        </div>
                    </div>
                </div>

                <div class="column is-full">
                    <div class="field">
                        <label class="label">
                            <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("desired-format-tt")}>{_("desired-format-field")}</span>
                        </label>
                        <div class="control">
                            <input {...register("desired_format")} class="input" type="text" placeholder="{n} - {s00e00}" />
                        </div>
                    </div>
                </div>

                <div class="column is-full">
                    <div class="field">
                        <label class="label">
                            <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("desired-folder-tt")}>{_("desired-folder-field")}</span>
                        </label>
                        <div class="control">
                            <input {...register("desired_folder")} class="input" type="text" />
                        </div>
                    </div>
                </div>

                <div class="column is-half">
                    <div class="field">
                        <label class="label">
                            <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("season-tt")}>{_("season-field")}</span>
                        </label>
                        <div class="control">
                            <input {...register("season", { required: true })} class="input" type="number" />
                        </div>
                    </div>
                </div>

                <div class="column is-half">
                    <div class="field">
                        <label class="label">
                            <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-top"
                                data-tooltip={_("episode-offset-tt")}>{_("episode-offset-field")}</span>
                        </label>
                        <div class="control">
                            <input{...register("episode_offset", { required: true })} class="input" type="number" />
                        </div>
                    </div>
                </div>
            </div>
        </form>
    );
}
