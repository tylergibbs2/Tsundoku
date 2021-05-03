import { toast } from "bulma-toast";
import { hydrate } from "preact";
import { useState, useEffect } from "preact/hooks";

import { AddModal } from "./add_modal";
import { EditModal } from "./edit_modal";
import { DeleteModal } from "./delete_modal";
import { Entry, Show } from "../interfaces";
import { getInjector } from "../fluent";
import { Filters } from "./components/filters";
import { Shows } from "./components/shows";


import "bulma-dashboard/dist/bulma-dashboard.min.css";


let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


const IndexApp = () => {

    let storedFilters = localStorage.getItem("showFilters");
    let storedViewType = localStorage.getItem("viewType");

    let storedSortDirection = localStorage.getItem("sortDirection");
    let storedSortKey = localStorage.getItem("sortKey");

    const [shows, setShows] = useState<Show[]>([]);
    const [activeShow, setActiveShow] = useState<Show | null>(null);
    const [currentModal, setCurrentModal] = useState<string | null>(null);
    const [filters, setFilters] = useState<string[]>(JSON.parse(storedFilters) || ["current", "finished", "tba", "unreleased", "upcoming"]);
    const [viewType, setViewType] = useState<string>(storedViewType || "cards");
    const [textFilter, setTextFilter] = useState<string>("");
    const [sortDirection, setSortDirection] = useState<string>(storedSortDirection || "+");
    const [sortKey, setSortKey] = useState<string>(storedSortKey || "title");

    const fetchShows = async () => {
        let request = {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        };

        let resp = await fetch("/api/v1/shows", request);
        let resp_json: any;
        if (resp.ok)
            resp_json = await resp.json();
        else
            return;

        setShows(getSortedShows(resp_json.result));
    }

    const addShow = (show: Show) => {
        let newShows: Show[] = [show, ...shows].sort((a, b) => {
            return a.title > b.title ? 1 : -1;
        });

        setShows(getSortedShows(newShows));
        toast({
            message: _("show-add-success"),
            duration: 5000,
            position: "bottom-right",
            type: "is-success",
            dismissible: true,
            animate: { in: "fadeIn", out: "fadeOut" }
        })
    }

    const updateShow = (show: Show) => {
        let newShows = [...shows];
        let toReplace = newShows.findIndex((existing) => existing.id_ === show.id_);
        if (toReplace !== -1)
            newShows[toReplace] = show;

        setShows(getSortedShows(newShows));
        toast({
            message: _("show-update-success"),
            duration: 5000,
            position: "bottom-right",
            type: "is-success",
            dismissible: true,
            animate: { in: "fadeIn", out: "fadeOut" }
        })
    }

    const removeShow = (show: Show) => {
        let newShows: Show[] = [];
        for (const existing of shows) {
            if (existing.id_ !== show.id_)
                newShows.push(existing);
        }

        setShows(getSortedShows(newShows));
        toast({
            message: _("show-delete-success"),
            duration: 5000,
            position: "bottom-right",
            type: "is-success",
            dismissible: true,
            animate: { in: "fadeIn", out: "fadeOut" }
        })
    }

    const getSortedShows = (toSort: Show[]) => {
        let first = 1;
        let second = -1;
        if (sortDirection === "-") {
            first = -1;
            second = 1;
        }

        let newShows = [...toSort];
        let sortFunc: any;
        switch (sortKey) {
            case "title":
                sortFunc = (a: Show, b: Show) => {
                    return a.title > b.title ? first : second;
                }
                newShows.sort(sortFunc);
                break;
            case "update":
                let entrySortFunc = (a: Entry, b: Entry) => {
                    let dateA = new Date(a.last_update);
                    let dateB = new Date(b.last_update);
                    return dateB > dateA ? 1 : -1;
                }
                sortFunc = (a: Show, b: Show) => {
                    let aEntries = [...a.entries].sort(entrySortFunc);
                    let bEntries = [...b.entries].sort(entrySortFunc);
                    let dateA, dateB;
                    try {
                        dateA = new Date(aEntries[0].last_update);
                    } catch {
                        dateA = new Date(null);
                    }
                    try {
                        dateB = new Date(bEntries[0].last_update);
                    } catch {
                        dateB = new Date(null);
                    }
                    return dateA > dateB ? first : second;
                }
                newShows.sort(sortFunc);
                break;
            case "dateAdded":
                sortFunc = (a: Show, b: Show) => {
                    let dateA = new Date(a.created_at);
                    let dateB = new Date(b.created_at);
                    return dateA > dateB ? first : second;
                }
                newShows.sort(sortFunc);
                break;
        }

        return newShows;
    }

    useEffect(() => {
        fetchShows();
    }, []);

    useEffect(() => {
        localStorage.setItem("showFilters", JSON.stringify(filters));
    }, [filters]);

    useEffect(() => {
        localStorage.setItem("viewType", viewType);
    }, [viewType]);

    useEffect(() => {
        localStorage.setItem("sortDirection", sortDirection);
        localStorage.setItem("sortKey", sortKey);

        setShows(getSortedShows(shows));
    }, [sortDirection, sortKey]);


    useEffect(() => {
        if (currentModal)
            document.body.classList.add("is-clipped");
        else
            document.body.classList.remove("is-clipped");
    }, [currentModal]);

    return (
        <>
            <AddModal
                currentModal={currentModal}
                setCurrentModal={setCurrentModal}
                addShow={addShow}
            />

            <DeleteModal
                show={activeShow}
                setActiveShow={setActiveShow}
                currentModal={currentModal}
                setCurrentModal={setCurrentModal}
                removeShow={removeShow}
            />

            <EditModal
                activeShow={activeShow}
                setActiveShow={setActiveShow}
                currentModal={currentModal}
                setCurrentModal={setCurrentModal}
                updateShow={updateShow}
            />

            <div class="columns">
                <div class="column is-full">
                    <h1 class="title">{_("shows-page-title")}</h1>
                    <h2 class="subtitle">{_("shows-page-subtitle")}</h2>
                </div>
            </div>
            <Filters
                filters={filters}
                setFilters={setFilters}
                setTextFilter={setTextFilter}
                viewType={viewType}
                setViewType={setViewType}
                sortKey={sortKey}
                setSortKey={setSortKey}
                sortDirection={sortDirection}
                setSortDirection={setSortDirection}
            />
            <Shows
                shows={shows}
                setActiveShow={setActiveShow}
                filters={filters}
                textFilter={textFilter}
                setCurrentModal={setCurrentModal}
                viewType={viewType}
            />
        </>
    )
}

hydrate(<IndexApp />, document.getElementById("index-main"));
