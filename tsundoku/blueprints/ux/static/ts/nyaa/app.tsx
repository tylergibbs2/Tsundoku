import { hydrate } from "preact";
import { useState } from "preact/hooks";

import { NyaaIndividualResult } from "../interfaces";
import { SearchBox, SearchTable, SpaceHolder } from "./search";


const NyaaSearchApp = () => {
    const [results, setResults] = useState<NyaaIndividualResult[]>([]);

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

interface NyaaSearchModalParams {
    isShowing: boolean;
}

const NyaaShowModal = ({isShowing}: NyaaSearchModalParams) => {

}

hydrate(<NyaaSearchApp />, document.getElementById("nyaa-main"));