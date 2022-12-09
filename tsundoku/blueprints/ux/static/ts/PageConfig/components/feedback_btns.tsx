import { getInjector } from "../../fluent";

let resources = ["config"];

const _ = getInjector(resources);

export const FeedbackBtns = () => {
  const featureRequest = async () => {
    let request = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        issue_type: "feature",
      }),
    };
    let resp = await fetch("/issue", request);
    if (resp.ok) {
      let data = await resp.json();
      window.open(data.result, "_blank");
    }
  };

  const bugReport = async () => {
    let request = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        issue_type: "bug",
        user_agent: navigator.userAgent,
      }),
    };
    let resp = await fetch("/issue", request);
    if (resp.ok) {
      let data = await resp.json();
      window.open(data.result, "_blank");
    }
  };

  return (
    <div className="columns">
      <button
        className="button is-link is-fullwidth mx-3"
        onClick={featureRequest}
      >
        {_("feedback-request")}
      </button>
      <button
        className="button is-danger is-fullwidth mx-3"
        onClick={bugReport}
      >
        {_("feedback-bug")}
      </button>
    </div>
  );
};
