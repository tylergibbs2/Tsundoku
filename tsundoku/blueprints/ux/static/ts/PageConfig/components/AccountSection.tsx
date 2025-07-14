import { useState } from "react";
import { APITokenComponent } from "./apitoken";
import { IonIcon } from "../../icon";
import { toast } from "bulma-toast";
import { getInjector } from "../../fluent";

const _ = getInjector();

const AccountSection = () => {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast({
        message: _("change-password-all-fields"),
        type: "is-danger",
        duration: 4000,
        position: "bottom-right",
      });
      return;
    }
    if (newPassword !== confirmPassword) {
      toast({
        message: _("change-password-mismatch"),
        type: "is-danger",
        duration: 4000,
        position: "bottom-right",
      });
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch("/api/v1/account/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      if (resp.ok) {
        toast({
          message: _("change-password-success"),
          type: "is-success",
          duration: 4000,
          position: "bottom-right",
        });
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      } else {
        const data = await resp.json();
        toast({
          message: data.error || _("change-password-failed"),
          type: "is-danger",
          duration: 4000,
          position: "bottom-right",
        });
      }
    } catch (err) {
      toast({
        message: _("change-password-failed"),
        type: "is-danger",
        duration: 4000,
        position: "bottom-right",
      });
    }
    setLoading(false);
  };

  return (
    <section className="section">
      <h1 className="title is-4">{_("section-account-title")}</h1>
      <h2 className="subtitle is-6">{_("section-account-subtitle")}</h2>
      <div className="box">
        <h3 className="title is-6 mb-2">{_("config-api-title")}</h3>
        <APITokenComponent />
        <a
          href="https://tsundoku.moe/docs"
          className="button is-info mt-2 mb-4"
        >
          {_("config-api-documentation")}
        </a>
        <hr />
        <h3 className="title is-6 mb-2">{_("change-password-title")}</h3>
        <form onSubmit={handleChangePassword} autoComplete="off">
          <div className="field">
            <label className="label">{_("current-password")}</label>
            <div className="control">
              <input
                className="input"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>
          <div className="field">
            <label className="label">{_("new-password")}</label>
            <div className="control">
              <input
                className="input"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          </div>
          <div className="field">
            <label className="label">{_("confirm-password")}</label>
            <div className="control">
              <input
                className="input"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          </div>
          <div className="field mt-4">
            <button
              className={"button is-primary " + (loading ? "is-loading" : "")}
              type="submit"
              disabled={loading}
            >
              <span style={{ marginRight: 6, display: "inline-block" }}>
                <IonIcon name="key-outline" />
              </span>
              {_("change-password-button")}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
};

export default AccountSection;
