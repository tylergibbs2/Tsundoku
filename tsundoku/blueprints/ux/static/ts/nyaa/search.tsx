import { Fragment } from "preact";
import { useState, StateUpdater } from "preact/hooks";

import { NyaaSearchResult, NyaaIndividualResult } from "../interfaces";


const NyaaSearchURL = "/api/v1/nyaa";

interface SearchBoxParams {
    setResults: StateUpdater<NyaaIndividualResult[]>;
}

export const SearchBox = ({setResults}: SearchBoxParams) => {
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

    const updateQuery = (e: Event) => {
        query = (e.target as HTMLInputElement).value;

        setSearchingState(false);
        window.clearTimeout(queryTimer);
        queryTimer = window.setTimeout(updateResults, waitInterval);
    }

    return (
        <div class={"control has-icons-left " + (isSearching ? "is-loading" : "")}>
            <input class="input" type="text" placeholder="Attack on Titan" onInput={updateQuery} disabled={isSearching}></input>
            <span class="icon is-small is-left">
                <i class="fas fa-search"></i>
            </span>
        </div>
    )
}

export const SpaceHolder = () => {
    return (
        <div class="container has-text-centered my-6">
            <h3 class="title is-3">Nothing to see here!</h3>
            <h4 class="subtitle is-5">Start searching to see some results.</h4>
        </div>
    )
}

interface SearchTableParams {
    results: NyaaIndividualResult[];
}

export const SearchTable = ({results}: SearchTableParams) => {
    return (
        <div class="container">
            <table class="table is-hoverable is-fullwidth">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Size</th>
                        <th>Date</th>
                        <th title="Seeders"><span class="icon"><i class="fas fa-arrow-up"></i></span></th>
                        <th title="Leechers"><span class="icon"><i class="fas fa-arrow-down"></i></span></th>
                        <th title="Link to Post"><span class="icon"><i class="fas fa-link"></i></span></th>
                    </tr>
                </thead>
                <tbody>
                    {
                        results.map((show: NyaaIndividualResult) => (
                            <Fragment key={show.torrent_link}>
                                <tr>
                                    <td style={{width: "60%"}}>{show.title}</td>
                                    <td>{show.size}</td>
                                    <td>{show.published}</td>
                                    <td class="has-text-success">{show.seeders}</td>
                                    <td class="has-text-danger">{show.leechers}</td>
                                    <td><a href={show.post_link}>Link</a></td>
                                </tr>
                            </Fragment>
                        ))
                    }
                </tbody>
            </table>
        </div>
    )
}
