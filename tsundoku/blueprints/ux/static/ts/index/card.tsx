import { getInjector } from "../fluent";
import { StateUpdater } from "preact/hooks";
import { Show } from "../interfaces";
import ReactHtmlParser from "react-html-parser";


interface CardParams {
    filters: string[];
    show: Show;
    setCurrentModal: StateUpdater<string | null>;
    setActiveShow: StateUpdater<Show | null>;
}


export const Card = ({ filters, show, setCurrentModal, setActiveShow }: CardParams) => {
    let resources = [
        "index"
    ];

    const _ = getInjector(resources);

    let title: any;
    if (show.metadata.link)
        title = <a href={show.metadata.link}><b>{show.title}</b></a>
    else
        title = <b>{show.title}</b>

    let shouldShow: boolean = true;
    if (filters.length !== 0)
        shouldShow = filters.includes(show.metadata.status);

    const openEditModal = () => {
        setActiveShow(show);
        setCurrentModal("edit");
    }

    const openDeleteModal = () => {
        setActiveShow(show);
        setCurrentModal("delete");
    }

    return (
        <div class={"column is-2 " + (shouldShow ? "" : "is-hidden")}>
            <div class="card">
                {show.metadata.poster &&
                    <div class="card-image">
                        {show.metadata.html_status && ReactHtmlParser(show.metadata.html_status)}
                        <a href={show.metadata.link}>
                            <figure class="image is-3by4">
                                <img src={show.metadata.poster} />
                            </figure>
                        </a>
                    </div>
                }
                <div class="card-content">
                    <p class="subtitle has-tooltip-arrow has-tooltip-multiline has-tooltip-up"
                        data-tooltip={show.title}>
                        <span>
                            {title}
                        </span>
                    </p>
                </div>
                <footer class="card-footer">
                    <p class="card-footer-item">
                        <a onClick={openEditModal}>{_("show-edit-link")}</a>
                    </p>
                    <p class="card-footer-item">
                        <a onClick={openDeleteModal}>{_("show-delete-link")}</a>
                    </p>
                </footer>
            </div>
        </div>
    )
}


interface AddShowCardParams {
    setCurrentModal: any;
}

export const AddShowCard = ({ setCurrentModal }: AddShowCardParams) => {

    const openModal = () => {
        setCurrentModal("add");
    }

    return (
        <div class="column is-2">
            <button onClick={openModal} style={{height: "100%"}} class="button is-outlined is-success is-large is-fullwidth">
                <span class="icon">
                    <i class="fa fa-plus"></i>
                </span>
            </button>
        </div>
    )
}
