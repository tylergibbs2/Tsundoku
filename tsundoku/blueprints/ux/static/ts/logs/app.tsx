import { hydrate } from "preact";
import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import useWebSocket, { ReadyState } from "react-use-websocket";

import "bulma-dashboard/dist/bulma-dashboard.min.css";
import { getInjector } from "../fluent";
import ReactHtmlParser from "react-html-parser";
import { Entry, Show } from "../interfaces";

let resources = [
    "logs"
];

const _ = getInjector(resources);

const LogsApp = () => {
    let ws_host = location.hostname + (location.port ? `:${location.port}` : "");
    let protocol = location.protocol === "https:" ? "wss:" : "ws:";

    let [shows, setShows] = useState<Show[]>([]);

    const getShows = async () => {
        let resp = await fetch("/api/v1/shows");
        if (resp.ok) {
            let data = await resp.json();
            setShows(data.result);
        }
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
                height: "10%"
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
                height: "85%"
            }}>
                <div style={{
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "flex-end",
                    overflowAnchor: "none",
                    alignItems: "stretch"
                }}>
                    {messageHistory.current.map((msg, idx) => (
                        <LogRow
                            key={idx}
                            row={msg}
                            shows={shows}
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
}

const LogRow = ({ row, shows }: LogRowParams) => {
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
        <div class="is-size-5" style={{
            position: "relative",
            flex: "0 0 auto"
        }}>
            {localized} {logLevel} <b>{match.groups.name}</b>: <Content raw_content={match.groups.content} shows={shows} />
        </div>
    );
}


interface ContentParams {
    raw_content: string;
    shows: Show[];
}

const Content = ({ raw_content, shows }: ContentParams) => {
    let toJoin: any = [];

    const showFromId = (id: number): Show => {
        return shows.find(show => show.id_ === id);
    }

    const entryFromId = (id: number): Entry => {
        let entries: Entry[] = [];
        for (const show of shows)
            entries = entries.concat(show.entries);

        return entries.find(entry => entry.id === id);
    }

    let codeRe = /`[^`]+`/g;
    let formatted = raw_content.replace(codeRe, (match, _) => {
        return `<code>${match.substring(1, match.length - 1)}</code>`;
    });

    let contextRe = /<[es]\d+>/g;
    let matches = formatted.matchAll(contextRe);

    for (const match of matches) {
        let data = match[0];

        let [front, end] = formatted.split(data);

        let type = data.charAt(1);
        let id = parseInt(data.substring(2, data.length - 1));

        let res: any;
        switch (type) {
            case "s":
                let show = showFromId(id);
                if (show) {
                    res = <Context show={show} />
                    break;
                }
            case "e":
                let entry = entryFromId(id);
                if (entry) {
                    let show = showFromId(entry.show_id);
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

        toJoin = toJoin.concat([
            front,
            res,
            end
        ]);
    };

    if (toJoin.length === 0)
        toJoin.push(formatted);

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
    return (
        <div class="dropdown is-hoverable is-up">
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
            <div class="dropdown-menu">
                <div class="dropdown-content">
                    <div class="dropdown-item has-text-centered">
                        <b>{show.title}</b>
                    </div>
                    <div class="dropdown-item has-text-centered">
                        {ReactHtmlParser(show.metadata.html_status)}
                    </div>
                    <div class="dropdown-item has-text-centered">
                        <figure class="image is-3by4">
                            <img loading="lazy" src={show.metadata.poster} />
                        </figure>
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


hydrate(<LogsApp />, document.getElementById("logs-main"));
