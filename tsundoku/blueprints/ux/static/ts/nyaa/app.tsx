import { Fragment, hydrate } from "preact";
import { useState, useEffect } from "preact/hooks";

import { NyaaIndividualResult } from "../interfaces";
import { NyaaShowModal } from "./modal";
import { SearchBox, SearchTable, SpaceHolder } from "./search";


const NyaaSearchApp = () => {
    const [results, setResults] = useState<NyaaIndividualResult[]>([]);
    const [choice, setChoice] = useState<NyaaIndividualResult>(null);

    return (
        <div class={choice ? "is-clipped" : ""}>
            <NyaaShowModal setChoice={setChoice} choice={choice}/>
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
                {results.length ? <SearchTable setChoice={setChoice} results={results} /> : <SpaceHolder />}
            </div>
        </div>
    )
}

hydrate(<NyaaSearchApp />, document.getElementById("nyaa-main"));