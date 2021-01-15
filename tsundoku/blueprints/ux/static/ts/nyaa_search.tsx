import { Fragment, hydrate } from "preact";
import { useState } from "preact/hooks";

import { NyaaSearchResult } from "./interfaces";

const NyaaSearchURL = "/api/v1/nyaa";


const NyaaSearchApp = () => {
    const [results, setResults] = useState([]);

    return (
        <div>
            <div class="columns is-vcentered">
                <div class="column is-4">
                    <div class="container">
                        <h1 class="title">Nyaa Search</h1>
                        <h2 class="subtitle">Search for anime releases</h2>
                    </div>
                </div>
                <div class="column is-4 is-offset-4">
                    <SearchBox setResults={setResults} />
                </div>
            </div>

            <div id="search-container" class="container">
                {results.length ? <SearchTable results={results} /> : <SpaceHolder />}
            </div>
        </div>
    )
}

const SearchBox = ({setResults}) => {
    const [isSearching, setSearchingState] = useState(false);

    const waitInterval: number = 2250;

    let query: string = "";
    let queryTimer: number = 0;

    const updateResults = () => {
        setSearchingState(true);

        fetch(`${NyaaSearchURL}?` + new URLSearchParams({
            query: query
        }))
            .then(res => res.json())
            .then(data => setResults(data.result || []))
            .then(() => setSearchingState(false));

    };

    const updateQuery = (e: any) => {
        query = e.target.value;

        setSearchingState(false);
        window.clearTimeout(queryTimer);
        queryTimer = window.setTimeout(updateResults, waitInterval);
    }

    return (
        <div class={"control has-icons-left " + (isSearching ? "is-loading" : "")}>
            <input class="input" type="text" placeholder="Attack on Titan" onInput={updateQuery}></input>
            <span class="icon is-small is-left">
                <i class="fas fa-search"></i>
            </span>
        </div>
    )
}

const SpaceHolder = () => {
    return (
        <div class="container has-text-centered my-6">
            <h3 class="title is-3">Nothing to see here!</h3>
            <h4 class="subtitle is-5">Start searching to see some results.</h4>
        </div>
    )
}

interface SearchTable {
    results: [];
}

const SearchTable = ({results}) => {
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
                        results.map(show => (
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

hydrate(<NyaaSearchApp />, document.getElementById("nyaa-main"));