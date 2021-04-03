import { getInjector } from "../fluent";
import { useState, StateUpdater } from "preact/hooks";
import { Show } from "../interfaces";
import ReactHtmlParser from "react-html-parser";


let resources = [
    "index"
];

const _ = getInjector(resources);


interface DeleteModalParams {
    show?: Show;
    setActiveShow: StateUpdater<Show | null>;
    currentModal?: string;
    setCurrentModal: StateUpdater<string | null>;
    removeShow: any;
}


export const DeleteModal = ({ show, setActiveShow, currentModal, setCurrentModal, removeShow }: DeleteModalParams) => {

    const [submitting, setSubmitting] = useState<boolean>(false);

    const performDelete = () => {
        setSubmitting(true);

        let request = {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        };

        fetch(`/api/v1/shows/${show.id_}`, request)
            .then((res) => {
                if (res.ok) {
                    removeShow(show);
                    setSubmitting(false);
                    setActiveShow(null);
                    setCurrentModal(null);
                }
            })
    }

    const cancel = () => {
        if (submitting)
            return;

        setActiveShow(null);
        setCurrentModal(null);
    }

    return (
        <div class={"modal modal-fx-fadeInScale " + (show && currentModal === "delete" ? "is-active" : "")}>
            <div class="modal-background" onClick={cancel}></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">{_("delete-modal-header")}</p>
                    <button class="delete" onClick={cancel} aria-label="close"></button>
                </header>

                <section class="modal-card-body">
                    <p>{show && ReactHtmlParser(_("delete-confirm-text", { "name": show.title }))}</p>
                </section>

                <footer class="modal-card-foot">
                    <button class="button is-danger" onClick={performDelete}>{_("delete-confirm-button")}</button>
                    <button class="button" onClick={cancel}>{_("delete-cancel")}</button>
                </footer>
            </div>
        </div>
    )
}
