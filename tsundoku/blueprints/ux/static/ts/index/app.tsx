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

    const [shows, setShows] = useState<Show[]>([]);
    const [activeShow, setActiveShow] = useState<Show | null>(null);
    const [currentModal, setCurrentModal] = useState<string | null>(null);

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

            <div class="container mb-3">
                <h1 class="title">{_("shows-page-title")}</h1>
                <h2 class="subtitle">{_("shows-page-subtitle")}</h2>
            </div>

            <div id="show-card-container" class="container">
                <div class="columns is-multiline">
                    {
                        shows.map((show: Show) => (
                            <div class="column is-2">
                                <Card
                                    key={show.id_}
                                    show={show}
                                    setCurrentModal={setCurrentModal}
                                    setActiveShow={setActiveShow}
                                />
                            </div>
                        ))
                    }

                    <div class="column is-2">
                        <AddShowCard setCurrentModal={setCurrentModal} />
                    </div>

                    {shows.length === 0 &&
                        <div class="container has-text-centered my-6">
                            <h3 class="title is-3">{_("empty-show-container")}</h3>
                            <h4 class="subtitle is-5">{_("empty-show-container-help")}</h4>
                        </div>
                    }
                </div>
            </div>
        </>
    )
}

hydrate(<IndexApp />, document.getElementById("index-main"));
