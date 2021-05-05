import { useRef, useState, useEffect } from "preact/hooks";

import { Show } from "../../interfaces";
import { IonIcon } from "../../icon";
import { getInjector } from "../../fluent";


let resources = [
    "base"
];

const _ = getInjector(resources);


interface WatchButtonParams {
    show?: Show;
    setValue: any;
    disabled?: boolean;
}


export const WatchButton = ({ show, setValue, disabled }: WatchButtonParams) => {
    const btn = useRef(null);

    let existingState: boolean;
    if (typeof show === "undefined" || show === null)
        existingState = true;
    else
        existingState = show.watch;

    const [watch, setWatch] = useState(existingState);

    useEffect(() => {
        if (show)
            setWatch(show.watch);
        else
            setWatch(true);
    }, [show]);

    const toBeWatched = () => {
        setWatch(true);
        setValue("watch", true);
        if (btn.current)
            btn.current.blur();
    }

    const toBeUnwatched = () => {
        setWatch(false);
        setValue("watch", false);
        if (btn.current)
            btn.current.blur();
    }

    if (watch) {
        return (
            <button ref={btn} class="button is-primary" title={_("unwatch-button-title")} onClick={toBeUnwatched} disabled={disabled}>
                <IonIcon name="bookmark" />
            </button>
        )
    } else {
        return (
            <button ref={btn} class="button is-primary is-outlined" title={_("watch-button-title")} onClick={toBeWatched} disabled={disabled}>
                <IonIcon name="bookmark-outline" />
            </button>
        )
    }
}
