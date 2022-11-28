import { getInjector } from "../fluent";
import { useState, Dispatch, SetStateAction } from "react";
import { Show } from "../interfaces";
import ReactHtmlParser from "react-html-parser";


let resources = [
    "index"
];

const _ = getInjector(resources);


interface DeleteModalParams {
    show?: Show;
    setActiveShow: Dispatch<SetStateAction<Show | null>>;
    currentModal?: string;
    setCurrentModal: Dispatch<SetStateAction<string | null>>;
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
        <div className={"modal modal-fx-fadeInScale " + (show && currentModal === "delete" ? "is-active" : "")}>
            <div className="modal-background" onClick={cancel}></div>
            <div className="modal-card">
                <header className="modal-card-head">
                    <p className="modal-card-title">{_("delete-modal-header")}</p>
                    <button className="delete" onClick={cancel} aria-label="close"></button>
                </header>

                <section className="modal-card-body">
                    <p>{show && ReactHtmlParser(_("delete-confirm-text", { "name": show.title }))}</p>
                </section>

                <footer className="modal-card-foot">
                    <button className="button is-danger" onClick={performDelete}>{_("delete-confirm-button")}</button>
                    <button className="button" onClick={cancel}>{_("delete-cancel")}</button>
                </footer>
            </div>
        </div>
    )
}
