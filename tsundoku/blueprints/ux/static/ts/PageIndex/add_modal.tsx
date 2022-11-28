import { useState, useEffect, Dispatch, SetStateAction } from "react";
import { useForm } from "react-hook-form";
import { getInjector } from "../fluent";
import { Show, GeneralConfig } from "../interfaces";
import { ShowToggleButton } from "./components/show_toggle_button";


let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


interface AddModalParams {
    currentModal?: string;
    setCurrentModal: Dispatch<SetStateAction<string | null>>;
    addShow: any;
    generalConfig: GeneralConfig;
}


export const AddModal = ({ currentModal, setCurrentModal, addShow, generalConfig }: AddModalParams) => {
    const [submitting, setSubmitting] = useState<boolean>(false);

    let defaultValues = {
        "title": "",
        "desired_format": generalConfig?.default_desired_format,
        "desired_folder": generalConfig?.default_desired_folder,
        "season": 1,
        "episode_offset": 0,
        "watch": true,
        "post_process": true
    }

    const { register, handleSubmit, reset, setValue } = useForm({
        defaultValues: defaultValues
    });

    useEffect(() => {
        reset(defaultValues);
    }, [currentModal]);

    const finalize = (show: Show) => {
        addShow(show);
        setSubmitting(false);
        setCurrentModal(null);
    }

    const cancel = () => {
        if (submitting)
            return;

        setCurrentModal(null);
    }

    return (
        <div className={"modal modal-fx-fadeInScale " + (currentModal === "add" ? "is-active" : "")}>
            <div className="modal-background" onClick={cancel}></div>
            <div className="modal-card">
                <header className="modal-card-head">
                    <p className="modal-card-title">{_("add-modal-header")}</p>
                    <div className="buttons">
                        <ShowToggleButton
                            setValue={setValue}
                            attribute="post_process"
                            onIcon="color-wand"
                            offIcon="color-wand-outline"
                            onTooltip={_("unprocess-button-title")}
                            offTooltip={_("process-button-title")}
                            additionalClasses="is-primary"
                        />
                        <ShowToggleButton
                                setValue={setValue}
                                attribute="watch"
                                onIcon="bookmark"
                                offIcon="bookmark-outline"
                                onTooltip={_("unwatch-button-title")}
                                offTooltip={_("watch-button-title")}
                                additionalClasses="is-primary"
                        />
                    </div>
                </header>

                <section className="modal-card-body">

                    <AddShowForm
                        setSubmitting={setSubmitting}
                        returnCallback={finalize}
                        register={register}
                        handleSubmit={handleSubmit}
                        reset={reset}
                    />

                </section>

                <footer className="modal-card-foot">
                    <progress className="progress is-primary is-small mt-2 is-hidden" max="100"></progress>
                    <button className={"button is-success " + (submitting ? "is-loading" : "")} type="submit" form="add-show-form">{_("add-form-add-button")}</button>
                    <button className="button closes-modals" onClick={cancel}>{_("add-form-cancel-button")}</button>
                </footer>
            </div>
        </div>
    )
}

interface AddShowFormParams {
    setSubmitting: Dispatch<SetStateAction<boolean>>;
    returnCallback: any;
    register: any;
    handleSubmit: any;
    reset: any;
}

const AddShowForm = ({ setSubmitting, returnCallback, register, handleSubmit, reset }: AddShowFormParams) => {

    const submitHandler = (data: any) => {
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
                if (typeof returnCallback !== 'undefined') {
                    returnCallback(res.result);
                    reset();
                }
                else
                    setSubmitting(false);
            })

    }

    return (
        <form id="add-show-form" onSubmit={handleSubmit(submitHandler)}>
            <div className="form-columns columns is-multiline">
                <div className="column is-full">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("add-form-name-tt")}>{_("add-form-name-field")}</span>
                        </label>
                        <div className="control">
                            <input {...register("title", { required: true })} className="input" type="text"
                                placeholder={_("add-form-name-placeholder")} />
                        </div>
                    </div>
                </div>

                <div className="column is-full">
                    <div className="field">
                        <label className="label">
                            <span className="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                                data-tooltip={_("add-form-desired-format-tt")}>{_("add-form-desired-format-field")}</span>
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
                                data-tooltip={_("add-form-desired-folder-tt")}>{_("add-form-desired-folder-field")}</span>
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
                                data-tooltip={_("add-form-season-tt")}>{_("add-form-season-field")}</span>
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
                                data-tooltip={_("add-form-episode-offset-tt")}>{_("add-form-episode-offset-field")}</span>
                        </label>
                        <div className="control">
                            <input{...register("episode_offset", { required: true })} className="input" type="number" />
                        </div>
                    </div>
                </div>
            </div>
        </form>
    );
}
