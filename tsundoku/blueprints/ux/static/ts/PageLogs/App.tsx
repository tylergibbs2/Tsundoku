import { useEffect, useRef, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { useQuery, UseQueryResult } from "react-query";

import { getInjector } from "../fluent";
import ReactHtmlParser from "react-html-parser";
import { fetchEntryById, fetchShowById, fetchShows } from "../queries";
import { GlobalLoading } from "../Components/GlobalLoading";

import "../../css/logs.css";

let resources = ["logs"];

const _ = getInjector(resources);

const codeRe = /`[^`]+`/g;
const contextRe = /<[es]\d+>/g;

export const LogsApp = () => {
  document.getElementById("navLogs").classList.add("is-active");
  document.getElementById("root").style.maxHeight = "100%";

  let ws_host = location.hostname + (location.port ? `:${location.port}` : "");
  let protocol = location.protocol === "https:" ? "wss:" : "ws:";

  const shows = useQuery(["shows"], fetchShows);

  let ws_url = `${protocol}//${ws_host}/ws/logs`;

  const { readyState, lastMessage } = useWebSocket(ws_url);
  const [messageHistory, setMessageHistory] = useState([]);

  useEffect(() => {
    if (lastMessage !== null)
      setMessageHistory((prev) => prev.concat(lastMessage));
  }, [lastMessage, setMessageHistory]);

  if (shows.isLoading) return <GlobalLoading withText={true} />;

  return (
    <>
      <div className="column is-full">
        <h1 className="title is-inline">{_("logs-page-title")}</h1>
        <ConnectionTag readyState={readyState} />
        <h2 className="subtitle">{_("logs-page-subtitle")}</h2>
      </div>
      <div
        className="box mb-0"
        style={{
          display: "flex",
          overflow: "hidden",
          height: "73vh",
        }}
      >
        <div className="logrow-container">
          <div></div>
          {messageHistory.map((msg, idx) => (
            <LogRow key={idx} row={msg} />
          ))}
        </div>
      </div>
      <div
        className="columns is-vcentered"
        style={{
          height: "15%",
        }}
      >
        <div className="column is-full">
          <a className="button is-info is-fullwidth" href="/logs?dl=1">
            {_("logs-download")}
          </a>
        </div>
      </div>
    </>
  );
};

interface LogRowParams {
  row?: MessageEvent;
}

const LogRow = ({ row }: LogRowParams) => {
  if (!row || row.data === "ACCEPT") return <></>;

  let match =
    /(?<time>.+) (?<level>\[\w+\]) (?<name>[^:]+): (?<content>.+)/g.exec(
      row.data
    );

  let logLevel: JSX.Element;
  switch (match.groups.level) {
    case "[INFO]":
      logLevel = <span className="tag is-info">{_("log-level-info")}</span>;
      break;
    case "[WARNING]":
      logLevel = (
        <span className="tag is-warning">{_("log-level-warning")}</span>
      );
      break;
    case "[ERROR]":
      logLevel = <span className="tag is-danger">{_("log-level-error")}</span>;
      break;
    case "[DEBUG]":
      logLevel = <span className="tag is-primary">{_("log-level-debug")}</span>;
      break;
  }

  let time = match.groups.time.slice(0, -4);
  let dt = new Date(time);
  let localized = new Intl.DateTimeFormat(window["LOCALE"], {
    dateStyle: "long",
    timeStyle: "long",
  }).format(dt);

  return (
    <div className="is-size-5">
      {localized} {logLevel} <b>{match.groups.name}</b>:{" "}
      <Content raw_content={match.groups.content} />
    </div>
  );
};

interface ContentParams {
  raw_content: string;
}

type ContentPart = JSX.Element | string;

const Content = ({ raw_content }: ContentParams) => {
  const [toJoin, setToJoin] = useState<ContentPart[]>([]);

  const render = async () => {
    let temp: ContentPart[] = [];
    let formatted = raw_content.replace(codeRe, (match, _) => {
      return `<code>${match.substring(1, match.length - 1)}</code>`;
    });

    let matches = formatted.matchAll(contextRe);

    for (const match of matches) {
      let data = match[0];

      let [front, end] = formatted.split(data);

      let type = data.charAt(1);
      let id = parseInt(data.substring(2, data.length - 1));

      let res: ContentPart;
      switch (type) {
        case "s":
          res = <Context show_id={id} />;
          break;
        case "e":
          res = <Context entry_id={id} />;
          break;
        default:
          res = _("context-cache-failure", {
            type: type,
            id: id,
          });
      }

      temp = temp.concat([front, res, end]);
    }

    if (temp.length === 0) temp.push(formatted);

    setToJoin(temp);
  };

  useEffect(() => {
    render();
  }, []);

  return (
    <>
      {toJoin.map((data, i) => {
        if (typeof data === "string") return ReactHtmlParser(data);
        else return data;
      })}
    </>
  );
};

interface ContextParams {
  show_id?: number | null;
  entry_id?: number | null;
}

const Context = ({ show_id, entry_id }: ContextParams) => {
  const entry = useQuery(
    ["entries", { id: entry_id }],
    async () => {
      return await fetchEntryById(entry_id);
    },
    {
      enabled: !!entry_id,
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
    }
  );

  const entryShowId = !!entry_id ? entry.data?.show_id : show_id;
  const show = useQuery(
    ["shows", { id_: entryShowId }],
    async () => {
      return await fetchShowById(entryShowId);
    },
    {
      enabled: !entry_id || (!!entry_id && !!entryShowId),
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
    }
  );

  const [isUp, setIsUp] = useState<boolean>(true);
  let ref = useRef(null);

  const calcPos = () => {
    if (!ref.current) {
      setIsUp(true);
      return;
    }
    let elem = ref.current;
    let rect = elem.getBoundingClientRect();
    if (isUp) setIsUp(elem.clientHeight < rect.top);
  };

  const makeUp = () => {
    setIsUp(true);
  };

  if (entry.isLoading || show.isLoading || entry.isError || show.isError)
    return <div></div>;

  return (
    <div
      onMouseOver={calcPos}
      onMouseOut={makeUp}
      className={"dropdown is-hoverable is-right " + (isUp ? "is-up" : "")}
    >
      <div className="dropdown-trigger">
        <a>
          {!entry.data && <span>{show.data.title}</span>}
          {entry.data && (
            <span>
              {_("title-with-episode", {
                title: show.data.title,
                episode: entry.data.episode,
              })}
            </span>
          )}
        </a>
      </div>
      <div
        ref={ref}
        className="dropdown-menu"
        style={{
          width: "20rem",
        }}
      >
        <div className="dropdown-content">
          <div className="dropdown-item has-text-centered">
            <div className="columns is-vcentered">
              <div className="column is-4">
                <figure className="image is-3by4">
                  <img loading="lazy" src={show.data.metadata.poster} />
                </figure>
              </div>
              <div className="column is-8">
                <b>{show.data.title}</b>
              </div>
            </div>
          </div>
          <div className="dropdown-item has-text-centered">
            {ReactHtmlParser(show.data.metadata.html_status)}
          </div>

          {entry.data && (
            <div className="dropdown-item has-text-centered">
              <b>
                {_("episode-prefix-state", {
                  episode: entry.data.episode,
                  state: entry.data.state,
                })}
              </b>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface ConnectionTagParams {
  readyState: ReadyState;
}

const ConnectionTag = ({ readyState }: ConnectionTagParams) => {
  if (readyState === ReadyState.CONNECTING)
    return (
      <span className="ml-3 tag is-link is-medium">
        {_("websocket-state-connecting")}
      </span>
    );
  else if (readyState === ReadyState.OPEN)
    return (
      <span className="ml-3 tag is-success is-medium">
        {_("websocket-state-connected")}
      </span>
    );
  else
    return (
      <span className="ml-3 tag is-danger is-medium">
        {_("websocket-state-disconnected")}
      </span>
    );
};
