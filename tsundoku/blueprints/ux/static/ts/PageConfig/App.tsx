import { APITokenComponent } from "./components/apitoken";
import { GeneralConfigApp } from "./components/generalconfig";
import { LibraryConfigApp } from "./components/libraryconfig";
import { FeedbackBtns } from "./components/feedback_btns";
import { TorrentConfig } from "./components/torrentclient";
import { getInjector } from "../fluent";
import { PostProcessing } from "./components/postprocessing";
import { FeedsConfig } from "./components/feedsconfig";
import { useRef, useState, useEffect } from "react";
import { toast } from "bulma-toast";
import { IonIcon } from "../icon";
import "../../css/config.css";

const _ = getInjector();

export const ConfigApp = () => {
  document.getElementById("navConfig").classList.add("is-active");

  const generalRef = useRef<any>(null);
  const libraryRef = useRef<any>(null);
  const feedsRef = useRef<any>(null);
  const torrentRef = useRef<any>(null);
  const encodeRef = useRef<any>(null);

  const [dirty, setDirty] = useState({
    general: false,
    library: false,
    feeds: false,
    torrent: false,
    encode: false,
  });

  const anyDirty = Object.values(dirty).some(Boolean);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (anyDirty) {
        e.preventDefault();
        e.returnValue =
          "You have unsaved changes. Are you sure you want to leave?";
        return e.returnValue;
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [anyDirty]);

  const handleDirtyChange = (section: string, isDirty: boolean) => {
    setDirty((prev) => ({ ...prev, [section]: isDirty }));
  };

  const handleSave = async () => {
    if (dirty.general && generalRef.current) await generalRef.current.save();
    if (dirty.library && libraryRef.current) await libraryRef.current.save();
    if (dirty.feeds && feedsRef.current) await feedsRef.current.save();
    if (dirty.torrent && torrentRef.current) await torrentRef.current.save();
    if (dirty.encode && encodeRef.current) await encodeRef.current.save();
    toast({
      message: _("config-save-success"),
      duration: 4000,
      position: "bottom-right",
      type: "is-success",
      dismissible: true,
      animate: { in: "fadeIn", out: "fadeOut" },
    });
  };

  return (
    <>
      <div className="columns">
        <div className="column is-full">
          <h1 className="title">{_("config-page-title")}</h1>
          <h2 className="subtitle">{_("config-page-subtitle")}</h2>
        </div>
      </div>
      <FeedbackBtns />
      <section className="section">
        <h1 className="title is-4">{_("section-general-title")}</h1>
        <h2 className="subtitle is-6">{_("section-general-subtitle")}</h2>
        <GeneralConfigApp
          ref={generalRef}
          onDirtyChange={(d) => handleDirtyChange("general", d)}
        />
      </section>
      <section className="section">
        <h1 className="title is-4">{_("section-libraries-title")}</h1>
        <h2 className="subtitle is-6">{_("section-libraries-subtitle")}</h2>
        <LibraryConfigApp
          ref={libraryRef}
          onDirtyChange={(d) => handleDirtyChange("library", d)}
        />
      </section>
      <section className="section">
        <h1 className="title is-4">{_("section-feeds-title")}</h1>
        <h2 className="subtitle is-6">{_("section-feeds-subtitle")}</h2>
        <FeedsConfig
          ref={feedsRef}
          onDirtyChange={(d) => handleDirtyChange("feeds", d)}
        />
      </section>
      <section className="section">
        <h1 className="title is-4">{_("section-torrent-title")}</h1>
        <h2 className="subtitle is-6">{_("section-torrent-subtitle")}</h2>
        <TorrentConfig
          ref={torrentRef}
          onDirtyChange={(d) => handleDirtyChange("torrent", d)}
        />
      </section>
      <section className="section">
        <h1 className="title is-4">{_("section-api-title")}</h1>
        <h2 className="subtitle is-6">{_("section-api-subtitle")}</h2>
        <div className="box" style={{ width: "50%" }}>
          <APITokenComponent />
          <a href="https://tsundoku.moe/docs" className="button is-info mt-2">
            {_("config-api-documentation")}
          </a>
        </div>
      </section>
      <section className="section">
        <h1 className="title is-4">{_("section-encode-title")}</h1>
        <h2 className="subtitle is-6">{_("section-encode-subtitle")}</h2>
        <PostProcessing
          ref={encodeRef}
          onDirtyChange={(d) => handleDirtyChange("encode", d)}
        />
      </section>
      {anyDirty && (
        <button
          className="button is-primary is-large floating-save-btn"
          style={{
            position: "fixed",
            bottom: "2rem",
            right: "2rem",
            zIndex: 1000,
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
          }}
          onClick={handleSave}
        >
          <span className="icon">
            <IonIcon name="save" />
          </span>
          <span>{_("config-save-button")}</span>
        </button>
      )}
    </>
  );
};
