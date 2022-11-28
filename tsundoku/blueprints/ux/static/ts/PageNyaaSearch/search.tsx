import { useState, ChangeEvent, Dispatch, SetStateAction } from "react";

import { NyaaSearchResult, NyaaIndividualResult } from "../interfaces";
import { getInjector } from "../fluent";
import { IonIcon } from "../icon";


const NyaaSearchURL = "/api/v1/nyaa";

let resources = [
    "nyaa_search"
];

const _ = getInjector(resources);

interface SearchBoxParams {
    setResults: Dispatch<SetStateAction<NyaaIndividualResult[]>>;
}

export const SearchBox = ({ setResults }: SearchBoxParams) => {
    const [isSearching, setSearchingState] = useState<boolean>(false);

    const waitInterval: number = 2250;

    let query: string = "";
    let queryTimer: number = 0;

    const updateResults = () => {
        setSearchingState(true);

        fetch(`${NyaaSearchURL}?` + new URLSearchParams({
            query: query
        }))
            .then(res => res.json())
            .then((data: NyaaSearchResult) => setResults(data.result || []))
            .then(() => setSearchingState(false));

    };

    const updateQuery = (e: ChangeEvent<HTMLInputElement>) => {
        query = e.target.value;

        setSearchingState(false);
        window.clearTimeout(queryTimer);
        queryTimer = window.setTimeout(updateResults, waitInterval);
    }

    return (
        <div className={"control has-icons-left " + (isSearching ? "is-loading" : "")}>
            <input className="input" type="text" placeholder={_("search-placeholder")} onInput={updateQuery} disabled={isSearching}></input>
            <span className="icon is-small is-left">
                <IonIcon name="search" />
            </span>
        </div>
    )
}

export const SpaceHolder = () => {
    return (
        <div className="container has-text-centered my-6">
            <h3 className="title is-3">{_("search-empty-results")}</h3>
            <h4 className="subtitle is-5">{_("search-start-searching")}</h4>
        </div>
    )
}

interface SearchTableParams {
    setChoice: Dispatch<SetStateAction<NyaaIndividualResult>>;
    results: NyaaIndividualResult[];
}

export const SearchTable = ({ setChoice, results }: SearchTableParams) => {
    return (
        <div className="container">
            <table className="table is-hoverable is-fullwidth">
                <thead>
                    <tr>
                        <th>{_("search-th-name")}</th>
                        <th>{_("search-th-size")}</th>
                        <th>{_("search-th-date")}</th>
                        <th title={_("search-th-seeders")}><span className="icon"><IonIcon name="arrow-up" /></span></th>
                        <th title={_("search-th-leechers")}><span className="icon"><IonIcon name="arrow-down" /></span></th>
                        <th title={_("search-th-link")}><span className="icon"><IonIcon name="link" /></span></th>
                    </tr>
                </thead>
                <tbody>
                    {
                        results.map((show: NyaaIndividualResult) => (
                            <SearchTableRow
                            setChoice={setChoice}
                            show={show}
                            />
                        ))
                    }
                </tbody>
            </table>
        </div>
    )
}


interface SearchTableRowParams {
    setChoice: Dispatch<SetStateAction<NyaaIndividualResult>>;
    show: NyaaIndividualResult;
}

const SearchTableRow = ({ setChoice, show }: SearchTableRowParams) => {
    const updateChoice = () => {
        setChoice(show);
    }

    return (
        <tr onClick={updateChoice} style={{"cursor": "pointer"}}>
            <td style={{ width: "60%" }}>{show.title}</td>
            <td>{show.size}</td>
            <td>{show.published}</td>
            <td className="has-text-success">{show.seeders}</td>
            <td className="has-text-danger">{show.leechers}</td>
            <td><a href={show.post_link}>{_("search-item-link")}</a></td>
        </tr>
    )
}