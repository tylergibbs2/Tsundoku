import { StateUpdater } from "preact/hooks";
import { AddShowCard, Card } from "./card";
import { ListItem, AddShowLI } from "./li";
import { getInjector } from "../../fluent";

import { Show } from "../../interfaces";


let resources = [
    "index"
];

const _ = getInjector(resources);

interface ShowsParams {
    shows: Show[];
    setActiveShow: StateUpdater<Show>;
    filters: string[];
    textFilter: string;
    setCurrentModal: StateUpdater<string>;
    viewType: string;
}

export const Shows = ({ shows, setActiveShow, filters, textFilter, setCurrentModal, viewType }: ShowsParams) => {
    if (viewType === "cards") {
        return (
            <CardView
                shows={shows}
                setActiveShow={setActiveShow}
                filters={filters}
                textFilter={textFilter}
                setCurrentModal={setCurrentModal}
            />
        )
    } else {
        return (
            <ListView
                shows={shows}
                setActiveShow={setActiveShow}
                filters={filters}
                textFilter={textFilter}
                setCurrentModal={setCurrentModal}
            />
        )
    }
}

interface ViewTypeParams {
    shows: Show[];
    setActiveShow: StateUpdater<Show>;
    filters: string[];
    textFilter: string;
    setCurrentModal: StateUpdater<string>;
}

const CardView = ({ shows, setActiveShow, filters, textFilter, setCurrentModal }: ViewTypeParams) => {
    return (
        <div class="columns is-multiline">
            {
                shows.map((show: Show) => (
                    <Card
                        textFilter={textFilter}
                        filters={filters}
                        show={show}
                        setCurrentModal={setCurrentModal}
                        setActiveShow={setActiveShow}
                    />
                ))
            }

            <AddShowCard setCurrentModal={setCurrentModal} />

        </div>
    )
}

const ListView = ({ shows, setActiveShow, filters, textFilter, setCurrentModal }: ViewTypeParams) => {
    return (
        <table class="table is-fullwidth is-striped is-hoverable" style={{tableLayout: "fixed"}}>
            <thead>
                <tr>
                    <th style={{width: "5%" }}></th>
                    <th style={{width: "70%"}}>{_("add-form-name-field")}</th>
                    <th style={{width: "15%"}}>{_("list-view-entry-update-header")}</th>
                    <th style={{width: "10%"}}>{_("list-view-actions-header")}</th>
                </tr>
            </thead>
            <tbody>
                {
                    shows.map((show: Show) => (
                        <ListItem
                        textFilter={textFilter}
                        filters={filters}
                        show={show}
                        setCurrentModal={setCurrentModal}
                        setActiveShow={setActiveShow}
                    />
                    ))
                }

                <AddShowLI
                    setCurrentModal={setCurrentModal}
                />
            </tbody>
        </table>
    )
}