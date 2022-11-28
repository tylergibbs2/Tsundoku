import { StateUpdater } from "preact/hooks";
import ReactHtmlParser from "react-html-parser";
import { getInjector } from "../../fluent";
import * as humanizeDuration from "humanize-duration";

import { Entry, Show } from "../../interfaces";
import { IonIcon } from "../../icon";


let resources = [
    "index"
];

const _ = getInjector(resources);


const sortByDate = (a: Entry, b: Entry): number => {
    let dateA = new Date(a.last_update);
    let dateB = new Date(b.last_update);

    return dateB > dateA ? 1 : -1;
}


interface ListItemParams {
    textFilter: string;
    filters: string[];
    show: Show;
    setCurrentModal: StateUpdater<string | null>;
    setActiveShow: StateUpdater<Show | null>;
}


export const ListItem = ({ textFilter, filters, show, setCurrentModal, setActiveShow }: ListItemParams) => {
    let title: any;
    if (show.metadata.link)
        title = <a class="ml-1" title={show.title} href={show.metadata.link}><b>{show.title}</b></a>
    else
        title = <b class="ml-1" title={show.title}>{show.title}</b>

    let shouldShow: boolean = true;
    if (show.metadata.kitsu_id !== null) {
        if (filters.length !== 0)
            shouldShow = filters.includes(show.metadata.status);

        if (shouldShow)
            shouldShow = show.title.toLowerCase().includes(textFilter.toLowerCase());
    }

    let timeDisplay: any;
    if (show.entries.length !== 0) {
        let sorted = [...show.entries].sort(sortByDate);
        let entry = sorted[0];
        let timeString = entry.last_update + "Z";

        const lastUpdate = new Date(timeString);
        const diff = lastUpdate.getTime() - Date.now();

        const localized = humanizeDuration(diff, {
            language: window["LOCALE"],
            fallbacks: ["en"],
            round: true,
            largest: 2
        })
        const localizedTitle = new Intl.DateTimeFormat(window["LOCALE"], {
            // @ts-ignore
            dateStyle: 'full',
            timeStyle: 'medium'
        }).format(lastUpdate)
        timeDisplay = <span title={localizedTitle}>{_("edit-entries-last-update", { time: localized })}</span>
    } else
        timeDisplay = ""

    const openEditModal = () => {
        setActiveShow(show);
        setCurrentModal("edit");
    }

    const openDeleteModal = () => {
        setActiveShow(show);
        setCurrentModal("delete");
    }

    return (
        <tr class={shouldShow ? "" : "is-hidden"}>
            <td class="is-vcentered">
                <a href={show.metadata.link}>
                    <figure class="image is-3by4">
                        <img src={show.metadata.poster} loading="lazy" />
                    </figure>
                </a>
            </td>
            <td class="is-vcentered" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {show.metadata.html_status && ReactHtmlParser(show.metadata.html_status)} {title}
            </td>
            <td class="is-vcentered">{timeDisplay}</td>
            <td class="is-vcentered">
                <a class="button is-info mr-1" onClick={openEditModal} title={_("show-edit-link")}>
                    <span class="icon"><IonIcon name="pencil-sharp" /></span>
                </a>
                <a class="button is-danger" onClick={openDeleteModal} title={_("show-delete-link")}>
                    <span class="icon"><IonIcon name="trash" /></span>
                </a>
            </td>
        </tr>
    )
}

interface AddShowLIParams {
    setCurrentModal: StateUpdater<string>;
}

export const AddShowLI = ({ setCurrentModal }: AddShowLIParams) => {
    const openModal = () => {
        setCurrentModal("add");
    }

    return (
        <tr>
            <td colSpan={4}>
                <button onClick={openModal} style={{ height: "100%" }} class="button is-outlined is-success is-large is-fullwidth">
                    <span class="icon">
                        <IonIcon name="add-circle" />
                    </span>
                </button>
            </td>
        </tr>
    )
}