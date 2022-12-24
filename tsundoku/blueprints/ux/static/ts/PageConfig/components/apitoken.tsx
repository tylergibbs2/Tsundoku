import { useEffect, useState } from "react";

import { getInjector } from "../../fluent";
import { IonIcon } from "../../icon";

const _ = getInjector();

export const APITokenComponent = () => {
  const [localToken, setLocalToken] = useState<string>("");
  const [isFetching, setIsFetching] = useState<boolean>(false);

  const getToken = async () => {
    setIsFetching(true);

    let request = {
      method: "GET",
    };

    let resp = await fetch("/api/v1/config/token", request);
    let resp_json: any;
    if (resp.ok) resp_json = await resp.json();
    else return;

    setLocalToken(resp_json.result);
    setIsFetching(false);
  };

  const setToken = async () => {
    setIsFetching(true);

    let request = {
      method: "POST",
    };

    let resp = await fetch("/api/v1/config/token", request);
    let resp_json: any;
    if (resp.ok) resp_json = await resp.json();
    else return;

    setLocalToken(resp_json.result);
    setIsFetching(false);
  };

  useEffect(() => {
    getToken();
  }, []);

  return (
    <div className="field has-addons">
      <div className="control is-expanded">
        <input
          className="input"
          type="text"
          readOnly={true}
          defaultValue={localToken}
        />
      </div>
      <div className="control">
        <button
          onClick={setToken}
          title={_("api-key-refresh")}
          className={"button is-danger " + (isFetching ? "is-loading" : "")}
        >
          <span className="icon">
            <IonIcon name="refresh" />
          </span>
        </button>
      </div>
    </div>
  );
};
