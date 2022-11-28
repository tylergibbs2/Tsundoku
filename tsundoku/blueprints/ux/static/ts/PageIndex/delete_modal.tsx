import { getInjector } from "../fluent";
import { Dispatch, SetStateAction } from "react";
import { Show } from "../interfaces";
import ReactHtmlParser from "react-html-parser";
import { useMutation, useQueryClient } from "react-query";
import { deleteShowById } from "../queries";
import { toast } from "bulma-toast";


let resources = [
    "index"
];

const _ = getInjector(resources);


interface DeleteModalParams {
    show?: Show;
    setActiveShow: Dispatch<SetStateAction<Show | null>>;
    currentModal?: string;
    setCurrentModal: Dispatch<SetStateAction<string | null>>;
}


export const DeleteModal = ({ show, setActiveShow, currentModal, setCurrentModal }: DeleteModalParams) => {
    const queryClient = useQueryClient();

    const mutation = useMutation(deleteShowById,
        {
            onSuccess: () => {
                queryClient.setQueryData(["shows"], (oldShows: Show[]) => oldShows.filter((s) => s.id_ !== show?.id_));
                toast({
                    message: _("show-delete-success"),
                    duration: 5000,
                    position: "bottom-right",
                    type: "is-success",
                    dismissible: true,
                    animate: { in: "fadeIn", out: "fadeOut" }
                })

                setCurrentModal(null);
                setActiveShow(null);
             }
        }
    );

    const performDelete = () => {
        mutation.mutate(show.id_);
    }

    const cancel = () => {
        if (mutation.isLoading)
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
