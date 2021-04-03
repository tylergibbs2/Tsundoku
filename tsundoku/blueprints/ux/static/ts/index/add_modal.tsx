import { useState, StateUpdater } from "preact/hooks";
import { useForm } from "react-hook-form";
import { getInjector } from "../fluent";
import { Show } from "../interfaces";


let resources = [
    "index"
];

const _ = getInjector(resources);


interface DeleteModalParams {
    currentModal?: string;
    setCurrentModal: StateUpdater<string | null>;
    addShow: any;
}


export const AddModal = ({ currentModal, setCurrentModal, addShow }: DeleteModalParams) => {
    const [submitting, setSubmitting] = useState<boolean>(false);

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
        <div class={"modal modal-fx-fadeInScale " + (currentModal === "add" ? "is-active" : "")}>
            <div class="modal-background" onClick={cancel}></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">{_("add-modal-header")}</p>
                    <button class="delete" onClick={cancel} aria-label="close"></button>
                </header>

                <section class="modal-card-body">

                    <AddShowForm
                        setSubmitting={setSubmitting}
                        returnCallback={finalize}
                    />

                </section>

                <footer class="modal-card-foot">
                    <progress class="progress is-primary is-small mt-2 is-hidden" max="100"></progress>
                    <input class="button is-success" type="submit" form="add-show-form"
                        value={_("add-form-add-button")}></input>
                    <button class="button closes-modals" onClick={cancel}>{_("add-form-cancel-button")}</button>
                </footer>
            </div>
        </div>
    )
}

interface AddShowFormParams {
    setSubmitting: StateUpdater<boolean>;
    returnCallback: any;
}

const AddShowForm = ({ setSubmitting, returnCallback }: AddShowFormParams) => {

    const { register, handleSubmit } = useForm({
        defaultValues: {
            "season": 1,
            "episode_offset": 0
        }
    });

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
                if (typeof returnCallback !== 'undefined')
                    returnCallback(res.result);
                else
                    setSubmitting(false);
            })

    }

    return (
        <form id="add-show-form" onSubmit={handleSubmit(submitHandler)}>
            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("add-form-name-tt")}>{_("add-form-name-field")}</span>
                </label>
                <div class="control">
                    <input name="title" ref={register({ required: true })} class="input" type="text"
                        placeholder={_("add-form-name-placeholder")} />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("add-form-desired-format-tt")}>{_("add-form-desired-format-field")}</span>
                </label>
                <div class="control">
                    <input name="desired_format" ref={register} class="input" type="text" placeholder="{n} - {s00e00}" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("add-form-desired-folder-tt")}>{_("add-form-desired-folder-field")}</span>
                </label>
                <div class="control">
                    <input name="desired_folder" ref={register} class="input" type="text" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("add-form-season-tt")}>{_("add-form-season-field")}</span>
                </label>
                <div class="control">
                    <input name="season" ref={register({ required: true })} class="input" type="number" />
                </div>
            </div>

            <div class="field">
                <label class="label">
                    <span class="has-tooltip-arrow has-tooltip-multiline has-tooltip-right"
                        data-tooltip={_("add-form-episode-offset-tt")}>{_("add-form-episode-offset-field")}</span>
                </label>
                <div class="control">
                    <input name="episode_offset" ref={register({ required: true })} class="input" type="number" />
                </div>
            </div>
        </form>
    )
}
