import { toast } from "bulma-toast";
import { useState, useEffect, Dispatch, SetStateAction } from "react";
import { SubmitHandler, useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "react-query";
import { getInjector } from "../fluent";
import { Show, GeneralConfig } from "../interfaces";
import { addNewShow } from "../queries";
import { ShowToggleButton } from "./components/show_toggle_button";


let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


interface AddModalParams {
    currentModal?: string;
    setCurrentModal: Dispatch<SetStateAction<string | null>>;
    generalConfig: GeneralConfig;
}


type AddShowFormValues = {
    title: string;
    desired_format: string;
    desired_folder: string;
    season: number;
    episode_offset: number;
    watch: boolean;
    post_process: boolean;
};


export const AddModal = ({ currentModal, setCurrentModal, generalConfig }: AddModalParams) => {
    const queryClient = useQueryClient();

    const mutation = useMutation(addNewShow,
        {
            onSuccess: (newShow) => {
                queryClient.setQueryData(["shows"], (oldShows: Show[]) => [...oldShows, newShow]);
                toast({
                    message: _("show-add-success"),
                    duration: 5000,
                    position: "bottom-right",
                    type: "is-success",
                    dismissible: true,
                    animate: { in: "fadeIn", out: "fadeOut" }
                });

                setCurrentModal(null);
             }
        }
    );

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

    const submitHandler: SubmitHandler<AddShowFormValues> = (formData: AddShowFormValues) => {
        mutation.mutate(formData);
    }

    const cancel = () => {
        if (mutation.isLoading)
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

                </section>

                <footer className="modal-card-foot">
                    <progress className="progress is-primary is-small mt-2 is-hidden" max="100"></progress>
                    <button className={"button is-success " + (mutation.isLoading ? "is-loading" : "")} type="submit" form="add-show-form">{_("add-form-add-button")}</button>
                    <button className="button closes-modals" onClick={cancel}>{_("add-form-cancel-button")}</button>
                </footer>
            </div>
        </div>
    )
}
