import { hydrate } from "preact";
import { useState, useEffect } from "preact/hooks";

import { AddShowCard, Card } from "./card";
import { AddModal } from "./add_modal";
import { EditModal } from "./edit_modal";
import { DeleteModal } from "./delete_modal";
import { Show } from "../interfaces";
import { getInjector } from "../fluent";


import "bulma-dashboard/dist/bulma-dashboard.min.css";


let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


const IndexApp = () => {

    let storedFilters = localStorage.getItem("showFilters");

    const [shows, setShows] = useState<Show[]>([]);
    const [activeShow, setActiveShow] = useState<Show | null>(null);
    const [currentModal, setCurrentModal] = useState<string | null>(null);
    const [filters, setFilters] = useState<string[]>(JSON.parse(storedFilters) || []);

    const fetchShows = () => {
        let request = {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        };

        fetch("/api/v1/shows", request)
            .then((res) => {
                if (res.ok)
                    return res.json();
            })
            .then((res: any) => {
                setShows(res.result);
            });
    }

    const addShow = (show: Show) => {
        let newShows: Show[] = [show, ...shows].sort((a, b) => {
            return a.title > b.title ? 1 : -1;
        });

        setShows(newShows);
    }

    const updateShow = (show: Show) => {
        let newShows = [...shows];
        let toReplace = newShows.findIndex((existing) => existing.id_ === show.id_);
        if (toReplace !== -1)
            newShows[toReplace] = show;

        setShows(newShows);
    }

    const removeShow = (show: Show) => {
        let newShows: Show[] = [];
        for (const existing of shows) {
            if (existing.id_ !== show.id_)
                newShows.push(existing);
        }

        setShows(newShows);
    }

    useEffect(() => {
        fetchShows();
    }, []);

    useEffect(() => {
        localStorage.setItem("showFilters", JSON.stringify(filters));
    }, [filters])

    useEffect(() => {
        if (currentModal)
            document.body.classList.add("is-clipped");
        else
            document.body.classList.remove("is-clipped");
    }, [currentModal]);

    const isFilter = (status: string) => {
        return (filters.length === 0 || filters.includes(status));
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

            <div class="container mb-3">
                <h1 class="title">{_("shows-page-title")}</h1>
                <h2 class="subtitle">{_("shows-page-subtitle")}</h2>
                <span class={"noselect tag mr-1 is-clickable " + (isFilter("current") ? "is-success" : "")} onClick={filterAiring}>{_('status-airing')}</span>
                <span class={"noselect tag mr-1 is-clickable " + (isFilter("finished") ? "is-danger" : "")} onClick={filterFinished}>{_('status-finished')}</span>
                <span class={"noselect tag mr-1 is-clickable " + (isFilter("tba") ? "is-warning" : "")} onClick={filterTba}>{_('status-tba')}</span>
                <span class={"noselect tag mr-1 is-clickable " + (isFilter("unreleased") ? "is-info" : "")} onClick={filterUnreleased}>{_('status-unreleased')}</span>
                <span class={"noselect tag mr-1 is-clickable " + (isFilter("upcoming") ? "is-primary" : "")} onClick={filterUpcoming}>{_('status-upcoming')}</span>
            </div>

            <div id="show-card-container" class="container">
                <div class="columns is-multiline">
                    {
                        shows.map((show: Show) => (
                            <Card
                                filters={filters}
                                key={show.id_}
                                show={show}
                                setCurrentModal={setCurrentModal}
                                setActiveShow={setActiveShow}
                            />
                        ))
                    }

                    <AddShowCard setCurrentModal={setCurrentModal} />

                </div>
            </div>
        </>
    )
}

hydrate(<IndexApp />, document.getElementById("index-main"));
