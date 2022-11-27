import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import useWebSocket, { ReadyState } from "react-use-websocket";

import { getInjector } from "../fluent";
import ReactHtmlParser from "react-html-parser";
import { Entry, Show } from "../interfaces";

import "../../css/logs.css";

let resources = [
    "logs"
];

const _ = getInjector(resources);


const codeRe = /`[^`]+`/g;
const contextRe = /<[es]\d+>/g;


export const LogsApp = () => {
    document.getElementById("navLogs").classList.add("is-active");

    let ws_host = location.hostname + (location.port ? `:${location.port}` : "");
    let protocol = location.protocol === "https:" ? "wss:" : "ws:";

    let showAccessCache: Map<number, Show> = new Map();
    let entryAccessCache: Map<number, Entry> = new Map();
    let ignoreList: number[] = [];

    let [shows, setShows] = useState<Show[] | null>(null);

    const getShows = async () => {
        let resp = await fetch("/api/v1/shows");
        if (resp.ok) {
            let data = await resp.json();
            setShows(data.result);
        } else
            setShows([]);
    }

    useEffect(() => {
        getShows();
    }, []);

    let ws_url = `${protocol}//${ws_host}/ws/logs`;

    const { readyState, lastMessage } = useWebSocket(ws_url);
    const messageHistory = useRef([]);

    messageHistory.current = useMemo(() =>
        messageHistory.current.concat(lastMessage), [lastMessage]
    );

    return (
        <>
            <div class="columns" style={{
                height: "12%"
            }}>
                <div class="column is-full">
                    <h1 class="title is-inline">{_("logs-page-title")}</h1>
                    <ConnectionTag readyState={readyState} />
                    <h2 class="subtitle">{_("logs-page-subtitle")}</h2>
                </div>
            </div>
            <div class="box mb-0" style={{
                display: "flex",
                overflow: "hidden",
                height: "83%"
            }}>
                <div class="logrow-container">
                    {messageHistory.current.map((msg, idx) => (
                        <LogRow
                            key={idx}
                            row={msg}
                            shows={shows}
                            showAccessCache={showAccessCache}
                            entryAccessCache={entryAccessCache}
                            ignoreList={ignoreList}
                        />
                    ))}
                </div>
            </div>
            <div class="columns is-vcentered" style={{
                height: "15%"
            }}>
                <div class="column is-full">
                    <a class="button is-info is-fullwidth" href="/logs?dl=1">{_("logs-download")}</a>
                </div>
            </div>
        </>
    )
}

interface LogRowParams {
    row?: MessageEvent;
    shows: Show[];
    showAccessCache: Map<number, Show>;
    entryAccessCache: Map<number, Entry>;
    ignoreList: number[];
}

const LogRow = ({ row, shows, showAccessCache, entryAccessCache, ignoreList }: LogRowParams) => {
    if (!row || row.data === "ACCEPT")
        return (<></>);

    let match = /(?<time>.+) (?<level>\[\w+\]) (?<name>[^:]+): (?<content>.+)/g.exec(row.data);

    let logLevel: JSX.Element;
    switch (match.groups.level) {
        case "[INFO]":
            logLevel = <span class="tag is-info">{_("log-level-info")}</span>
            break;
        case "[WARNING]":
            logLevel = <span class="tag is-warning">{_("log-level-warning")}</span>
            break;
        case "[ERROR]":
            logLevel = <span class="tag is-danger">{_("log-level-error")}</span>
            break;
        case "[DEBUG]":
            logLevel = <span class="tag is-primary">{_("log-level-debug")}</span>
            break;
    }

    let time = match.groups.time.slice(0, -4);
    let dt = new Date(time);
    let localized = new Intl.DateTimeFormat(window["LOCALE"], {
        dateStyle: "long",
        timeStyle: "long"
    }).format(dt);

    return (
        <>
            <div></div>
            <div class="is-size-5">
                {localized} {logLevel} <b>{match.groups.name}</b>: <Content
                    raw_content={match.groups.content}
                    shows={shows}
                    showAccessCache={showAccessCache}
                    entryAccessCache={entryAccessCache}
                    ignoreList={ignoreList}
                />
            </div>
        </>
    );
}


interface ContentParams {
    raw_content: string;
    shows: Show[];
    showAccessCache: Map<number, Show>;
    entryAccessCache: Map<number, Entry>;
    ignoreList: number[];
}

const Content = ({ raw_content, shows, showAccessCache, entryAccessCache, ignoreList }: ContentParams) => {
    const [toJoin, setToJoin] = useState<any>([]);

    const fetchShow = async (id: number): Promise<Show> | null => {
        let resp = await fetch(`/api/v1/shows/${id}`);
        if (resp.ok) {
            return (await resp.json()).result;
        }
    }

    const showFromId = async (id: number): Promise<Show> | null => {
        let exists = showAccessCache.get(id);
        if (exists)
            return exists;

        while (shows === null)
            await new Promise(resolve => setTimeout(resolve, 1000));

        let found = shows.find(show => show.id_ === id);
        if (found) {
            showAccessCache.set(id, found);
            return found;
        } else {
            if (ignoreList.includes(id)) return;
            found = await fetchShow(id);
            if (found) {
                showAccessCache.set(id, found);
                return found
            }
            ignoreList.push(id);
        }
    }

    const entryFromId = async (id: number): Promise<Entry> | null => {
        let exists = entryAccessCache.get(id);
        if (exists)
            return exists;

        let entries: Entry[] = [];
        for (const show of shows)
            entries = entries.concat(show.entries);

        let found = entries.find(entry => entry.id === id);
        if (found) {
            entryAccessCache.set(id, found);
            return found;
        }
    }

    const render = async () => {
        let temp: any = [];
        let formatted = raw_content.replace(codeRe, (match, _) => {
            return `<code>${match.substring(1, match.length - 1)}</code>`;
        });

        let matches = formatted.matchAll(contextRe);

        for (const match of matches) {
            let data = match[0];

            let [front, end] = formatted.split(data);

            let type = data.charAt(1);
            let id = parseInt(data.substring(2, data.length - 1));

            let res: any;
            switch (type) {
                case "s":
                    let show = await showFromId(id);
                    if (show) {
                        res = <Context show={show} />
                        break;
                    }
                case "e":
                    let entry = await entryFromId(id);
                    if (entry) {
                        let show = await showFromId(entry.show_id);
                        if (show) {
                            res = <Context show={show} entry={entry} />
                            break;
                        }
                    }
                default:
                    res = _("context-cache-failure", {
                        type: type,
                        id: id
                    });
            }

            temp = temp.concat([
                front,
                res,
                end
            ]);
        };

        if (temp.length === 0)
            temp.push(formatted);

        setToJoin(temp);
    }

    useEffect(() => {
        render();
    }, [])

    return (
        <>
            {toJoin.map(data => {
                if (typeof data === "string")
                    return ReactHtmlParser(data);
                else
                    return data;
            })}
        </>
    );
}


interface ContextParams {
    show: Show;
    entry?: Entry;
}

const Context = ({ show, entry }: ContextParams) => {
    const [isUp, setIsUp] = useState<boolean>(true);
    let ref = useRef(null);

    const calcPos = () => {
        if (!ref.current) {
            setIsUp(true);
            return;
        }
        let elem = ref.current;
        let rect = elem.getBoundingClientRect();
        if (isUp)
            setIsUp(elem.clientHeight < rect.top);
    }

    const makeUp = () => {
        setIsUp(true);
    }

    return (
        <div onMouseOver={calcPos} onMouseOut={makeUp} class={"dropdown is-hoverable is-right " + (isUp ? "is-up" : "")}>
            <div class="dropdown-trigger">
                <a>
                    {!entry &&
                        <span>{show.title}</span>
                    }
                    {entry &&
                        <span>{_("title-with-episode", {
                            title: show.title,
                            episode: entry.episode
                        })}</span>
                    }
                </a>
            </div>
            <div ref={ref} class="dropdown-menu" style={{
                width: "20rem"
            }}>
                <div class="dropdown-content">
                    <div class="dropdown-item has-text-centered">
                        <div class="columns is-vcentered">
                            <div class="column is-4">
                                <figure class="image is-3by4">
                                    <img loading="lazy" src={show.metadata.poster} />
                                </figure>
                            </div>
                            <div class="column is-8">
                                <b>{show.title}</b>
                            </div>
                        </div>
                    </div>
                    <div class="dropdown-item has-text-centered">
                        {ReactHtmlParser(show.metadata.html_status)}
                    </div>

                    {entry &&
                        <div class="dropdown-item has-text-centered">
                            <b>{_("episode-prefix-state", {
                                episode: entry.episode,
                                state: entry.state
                            })}</b>
                        </div>
                    }
                </div>
            </div>
        </div>
    )
}


interface ConnectionTagParams {
    readyState: ReadyState;
}

const ConnectionTag = ({ readyState }: ConnectionTagParams) => {
    if (readyState === ReadyState.CONNECTING)
        return (<span class="ml-3 tag is-link is-medium">{_("websocket-state-connecting")}</span>);
    else if (readyState === ReadyState.OPEN)
        return (<span class="ml-3 tag is-success is-medium">{_("websocket-state-connected")}</span>);
    else
        return (<span class="ml-3 tag is-danger is-medium">{_("websocket-state-disconnected")}</span>);
}
