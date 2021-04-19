import { StateUpdater } from "preact/hooks";
import { getInjector } from "../../fluent";

let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


interface FiltersParams {
    filters: string[];
    setFilters: StateUpdater<string[]>;
    setTextFilter: StateUpdater<string>;
    viewType: string;
    setViewType: StateUpdater<string>;
    sortDirection: string;
    setSortDirection: StateUpdater<string>;
    sortKey: string;
    setSortKey: StateUpdater<string>;
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

    const filterSearch = (e: Event) => {
        let query = (e.target as HTMLInputElement).value;
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
        <div class="columns pb-3" style={{
            position: "sticky",
            top: "0",
            zIndex: "5",
            backgroundImage: "linear-gradient(rgba(255, 255, 255, 1) 80%, rgba(255, 255, 255, 0) 100%)"
        }}>
            <div class="column is-7">
                <div class="tags are-medium">
                    <span class={"noselect tag mr-1 is-clickable " + (isFilter("current") ? "is-success" : "")} onClick={filterAiring}>{_('status-airing')}</span>
                    <span class={"noselect tag mr-1 is-clickable " + (isFilter("finished") ? "is-danger" : "")} onClick={filterFinished}>{_('status-finished')}</span>
                    <span class={"noselect tag mr-1 is-clickable " + (isFilter("tba") ? "is-warning" : "")} onClick={filterTba}>{_('status-tba')}</span>
                    <span class={"noselect tag mr-1 is-clickable " + (isFilter("unreleased") ? "is-info" : "")} onClick={filterUnreleased}>{_('status-unreleased')}</span>
                    <span class={"noselect tag is-clickable " + (isFilter("upcoming") ? "is-primary" : "")} onClick={filterUpcoming}>{_('status-upcoming')}</span>
                </div>
            </div>
            <div class="column is-5 is-offset-">
                <div class="field is-horizontal">
                    <div class="field-body">
                        <div class="field is-narrow">
                            <SortDropdown
                                sortKey={sortKey}
                                setSortKey={setSortKey}
                                sortDirection={sortDirection}
                                setSortDirection={setSortDirection}
                            />
                        </div>
                        <div class="field has-addons is-narrow">
                            <div class="control">
                                <a class={"button " + (viewType === "cards" ? "is-info" : "")} onClick={cardView}>
                                    <span class="icon"><i class="fas fa-portrait"></i></span>
                                </a>
                            </div>
                            <div class="control">
                                <a class={"button " + (viewType === "list" ? "is-info" : "")} onClick={listView}>
                                    <span class="icon"><i class="fas fa-list"></i></span>
                                </a>
                            </div>
                        </div>
                        <div class="field">
                            <div class="control has-icons-left">
                                <input type="text" class="input is-pulled-right" onInput={filterSearch} placeholder="Attack on Titan"></input>
                                <span class="icon is-small is-left">
                                    <i class="fas fa-search"></i>
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
    setSortDirection: StateUpdater<string>;
    sortKey: string;
    setSortKey: StateUpdater<string>;
}

const SortDropdown = ({sortDirection, setSortDirection, sortKey, setSortKey}: SortDropdownParams) => {

    const sortKeyTitle = () => {
        if (sortKey !== "title")
            setSortKey("title");
    }

    const sortKeyUpdate = () => {
        if (sortKey !== "update")
            setSortKey("update");
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
    }

    let sortDisplayArrow: any;
    if (sortDirection === "+")
        sortDisplayArrow = <span class="icon"><i class="fas fa-arrow-up"></i></span>
    else
        sortDisplayArrow = <span class="icon"><i class="fas fa-arrow-down"></i></span>

    return (
        <div class="dropdown is-hoverable">
            <div class="dropdown-trigger">
                <button class="button">
                    {sortDisplayText}
                    {sortDisplayArrow}
                    <span class="icon is-small">
                        <i class="fas fa-angle-down"></i>
                    </span>
                </button>
            </div>
            <div class="dropdown-menu">
                <div class="dropdown-content">
                    <div class="dropdown-item has-text-centered">
                        <b>{_("sort-by-header")}</b>
                    </div>
                    <hr class="dropdown-divider"></hr>
                    <a onClick={sortKeyTitle} class={"dropdown-item " + (sortKey === "title" ? "is-active" : "")}>
                        {_("sort-key-title")}
                    </a>
                    <a onClick={sortKeyUpdate} class={"dropdown-item " + (sortKey === "update" ? "is-active" : "")}>
                        {_("sort-key-update")}
                    </a>
                    <hr class="dropdown-divider"></hr>
                    <a onClick={sortDirAsc} class={"dropdown-item has-text-centered " + (sortDirection === "+" ? "is-active" : "")}>
                        <div class="columns">
                            <div class="column is-2">
                                {_("sort-dir-asc")}
                            </div>
                            <div class="column is-2 is-offset-8">
                                <span class="icon is-small">
                                    <i class="fas fa-arrow-up"></i>
                                </span>
                            </div>
                        </div>
                    </a>
                    <a onClick={sortDirDesc} class={"dropdown-item has-text-centered " + (sortDirection === "-" ? "is-active" : "")}>
                        <div class="columns">
                            <div class="column is-2">
                                {_("sort-dir-desc")}
                            </div>
                            <div class="column is-2 is-offset-8">
                                <span class="icon is-small">
                                    <i class="fas fa-arrow-down"></i>
                                </span>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    )
}