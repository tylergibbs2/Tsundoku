import { ChangeEvent, Dispatch, SetStateAction } from "react";
import { getInjector } from "../../fluent";
import { IonIcon } from "../../icon";

let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


interface FiltersParams {
    filters: string[];
    setFilters: Dispatch<SetStateAction<string[]>>;
    setTextFilter: Dispatch<SetStateAction<string>>;
    viewType: string;
    setViewType: Dispatch<SetStateAction<string>>;
    sortDirection: string;
    setSortDirection: Dispatch<SetStateAction<string>>;
    sortKey: string;
    setSortKey: Dispatch<SetStateAction<string>>;
}

export const Filters = ({ filters, setFilters, setTextFilter, viewType, setViewType, sortDirection, setSortDirection, sortKey, setSortKey }: FiltersParams) => {
    const isFilter = (status: string) => {
        return filters.includes(status);
    }

    const filterAiring = () => {
        let idx = filters.indexOf("current");

        if (idx !== -1) {
            let copy = [...filters];
            copy.splice(idx, 1);
            setFilters(copy);
        } else
            setFilters(["current", ...filters]);
    }

    const filterFinished = () => {
        let idx = filters.indexOf("finished");

        if (idx !== -1) {
            let copy = [...filters];
            copy.splice(idx, 1);
            setFilters(copy);
        } else
            setFilters(["finished", ...filters]);
    }

    const filterTba = () => {
        let idx = filters.indexOf("tba");

        if (idx !== -1) {
            let copy = [...filters];
            copy.splice(idx, 1);
            setFilters(copy);
        } else
            setFilters(["tba", ...filters]);
    }

    const filterUnreleased = () => {
        let idx = filters.indexOf("unreleased");

        if (idx !== -1) {
            let copy = [...filters];
            copy.splice(idx, 1);
            setFilters(copy);
        } else
            setFilters(["unreleased", ...filters]);
    }

    const filterUpcoming = () => {
        let idx = filters.indexOf("upcoming");

        if (idx !== -1) {
            let copy = [...filters];
            copy.splice(idx, 1);
            setFilters(copy);
        } else
            setFilters(["upcoming", ...filters]);
    }

    const filterSearch = (e: ChangeEvent<HTMLInputElement>) => {
        let query = e.target.value;
        setTextFilter(query);
    }

    const cardView = () => {
        if (viewType !== "cards")
            setViewType("cards");
    }

    const listView = () => {
        if (viewType !== "list")
            setViewType("list");
    }

    return (
        <div className="columns pb-3" style={{
            position: "sticky",
            top: "0",
            zIndex: "5",
            backgroundImage: "linear-gradient(rgba(255, 255, 255, 1) 80%, rgba(255, 255, 255, 0) 100%)"
        }}>
            <div className="column is-7">
                <div className="tags are-medium">
                    <span className={"noselect tag mr-1 is-clickable " + (isFilter("current") ? "is-success" : "")} onClick={filterAiring}>{_('status-airing')}</span>
                    <span className={"noselect tag mr-1 is-clickable " + (isFilter("finished") ? "is-danger" : "")} onClick={filterFinished}>{_('status-finished')}</span>
                    <span className={"noselect tag mr-1 is-clickable " + (isFilter("tba") ? "is-warning" : "")} onClick={filterTba}>{_('status-tba')}</span>
                    <span className={"noselect tag mr-1 is-clickable " + (isFilter("unreleased") ? "is-info" : "")} onClick={filterUnreleased}>{_('status-unreleased')}</span>
                    <span className={"noselect tag is-clickable " + (isFilter("upcoming") ? "is-primary" : "")} onClick={filterUpcoming}>{_('status-upcoming')}</span>
                </div>
            </div>
            <div className="column is-5 is-offset-">
                <div className="field is-horizontal">
                    <div className="field-body">
                        <div className="field is-narrow">
                            <SortDropdown
                                sortKey={sortKey}
                                setSortKey={setSortKey}
                                sortDirection={sortDirection}
                                setSortDirection={setSortDirection}
                            />
                        </div>
                        <div className="field has-addons is-narrow">
                            <div className="control">
                                <a className={"button " + (viewType === "cards" ? "is-info" : "")} onClick={cardView}>
                                    <span className="icon"><IonIcon name="images" /></span>
                                </a>
                            </div>
                            <div className="control">
                                <a className={"button " + (viewType === "list" ? "is-info" : "")} onClick={listView}>
                                    <span className="icon"><IonIcon name="list" /></span>
                                </a>
                            </div>
                        </div>
                        <div className="field">
                            <div className="control has-icons-left">
                                <input type="text" className="input is-pulled-right" onInput={filterSearch} placeholder="Attack on Titan"></input>
                                <span className="icon is-small is-left">
                                    <IonIcon name="search" />
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

interface SortDropdownParams {
    sortDirection: string;
    setSortDirection: Dispatch<SetStateAction<string>>;
    sortKey: string;
    setSortKey: Dispatch<SetStateAction<string>>;
}

const SortDropdown = ({ sortDirection, setSortDirection, sortKey, setSortKey }: SortDropdownParams) => {

    const sortKeyTitle = () => {
        if (sortKey !== "title")
            setSortKey("title");
    }

    const sortKeyUpdate = () => {
        if (sortKey !== "update")
            setSortKey("update");
    }

    const sortKeyAdded = () => {
        if (sortKey !== "dateAdded")
            setSortKey("dateAdded");
    }

    const sortDirAsc = () => {
        if (sortDirection !== "+")
            setSortDirection("+");
    }

    const sortDirDesc = () => {
        if (sortDirection !== "-")
            setSortDirection("-");
    }

    let sortDisplayText: any;
    switch (sortKey) {
        case "title":
            sortDisplayText = <span>{_("sort-key-title")}</span>
            break;
        case "update":
            sortDisplayText = <span>{_("sort-key-update")}</span>
            break;
        case "dateAdded":
            sortDisplayText = <span>{_("sort-key-date-added")}</span>
    }

    let sortDisplayArrow: any;
    if (sortDirection === "+")
        sortDisplayArrow = <span className="icon"><IonIcon name="arrow-up" /></span>
    else
        sortDisplayArrow = <span className="icon"><IonIcon name="arrow-down" /></span>

    return (
        <div className="dropdown is-hoverable">
            <div className="dropdown-trigger">
                <button className="button">
                    {sortDisplayText}
                    {sortDisplayArrow}
                    <span className="icon is-small">
                        <IonIcon name="chevron-down" />
                    </span>
                </button>
            </div>
            <div className="dropdown-menu">
                <div className="dropdown-content">
                    <div className="dropdown-item has-text-centered">
                        <b>{_("sort-by-header")}</b>
                    </div>
                    <hr className="dropdown-divider"></hr>
                    <a onClick={sortKeyTitle} className={"dropdown-item " + (sortKey === "title" ? "is-active" : "")}>
                        {_("sort-key-title")}
                    </a>
                    <a onClick={sortKeyUpdate} className={"dropdown-item " + (sortKey === "update" ? "is-active" : "")}>
                        {_("sort-key-update")}
                    </a>
                    <a onClick={sortKeyAdded} className={"dropdown-item " + (sortKey === "dateAdded" ? "is-active" : "")}>
                        {_("sort-key-date-added")}
                    </a>
                    <hr className="dropdown-divider"></hr>
                    <a onClick={sortDirAsc} className={"dropdown-item has-text-centered " + (sortDirection === "+" ? "is-active" : "")}>
                        <div className="columns">
                            <div className="column is-2">
                                {_("sort-dir-asc")}
                            </div>
                            <div className="column is-2 is-offset-8">
                                <span className="icon is-small">
                                    <IonIcon name="arrow-up" />
                                </span>
                            </div>
                        </div>
                    </a>
                    <a onClick={sortDirDesc} className={"dropdown-item has-text-centered " + (sortDirection === "-" ? "is-active" : "")}>
                        <div className="columns">
                            <div className="column is-2">
                                {_("sort-dir-desc")}
                            </div>
                            <div className="column is-2 is-offset-8">
                                <span className="icon is-small">
                                    <IonIcon name="arrow-down" />
                                </span>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    )
}