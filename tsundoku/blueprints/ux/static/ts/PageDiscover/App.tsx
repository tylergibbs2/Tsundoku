import { getInjector } from "../fluent";

import "../../css/index.css";


let resources = [
    "base",
    "index"
];

const _ = getInjector(resources);


export const DiscoverApp = () => {
    document.getElementById("navDiscover").classList.add("is-active");

    return (
        <div>Test</div>
    )
}
