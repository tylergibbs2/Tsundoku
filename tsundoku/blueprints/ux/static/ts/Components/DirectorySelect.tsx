import { useEffect, useState } from "react";
import type { DirectoryTree } from "../api";
import { tree } from "../api";
import { IonIcon } from "../icon";

interface DirectorySelectParams {
  defaultValue: string;
  onChange: (newValue: string) => any;
}

export const DirectorySelect = ({
  defaultValue,
  onChange,
}: DirectorySelectParams) => {
  const [isActive, setIsActive] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const [currentState, setCurrentState] = useState<DirectoryTree | null>(null);

  const getNewState = async (dir: string, subdir: string | null = null) => {
    setIsLoading(true);

    const { data } = await tree({
      body: { dir, subdir },
      throwOnError: true,
    });
    setCurrentState(data.result);

    setIsLoading(false);
  };

  const toggleSelect = async () => {
    if (!isActive) setIsActive(true);
    else if (!isLoading) await cancel();
  };

  const save = () => {
    if (isLoading) return;

    if (onChange && currentState) onChange(currentState.current_path);
    setIsActive(false);
  };

  const cancel = async () => {
    if (isLoading) return;

    await getNewState(defaultValue);
    setIsActive(false);
  };

  const goToParentDirectory = async () => {
    if (currentState) await getNewState(currentState.current_path, "..");
  };

  const goToSubDirectory = async (subdir: string) => {
    if (currentState) await getNewState(currentState.current_path, subdir);
  };

  useEffect(() => {
    getNewState(defaultValue);
  }, []);

  if (currentState === null) return <div></div>;

  return (
    <div
      className={`dropdown ${isActive ? "is-active" : ""}`}
      style={{ minWidth: "100%" }}
    >
      <div className="field has-addons" style={{ width: "100%" }}>
        <div className="control is-expanded">
          <input
            onClick={toggleSelect}
            className="input"
            type="text"
            readOnly={true}
            value={currentState.current_path}
          />
        </div>
        <div className="control">
          <button
            onClick={toggleSelect}
            className="button is-primary"
            style={{
              borderTopRightRadius: "4px",
              borderBottomRightRadius: "4px",
            }}
          >
            <span className="icon">
              <IonIcon name="folder" />
            </span>
          </button>
        </div>
        <div className="dropdown-menu" style={{ width: "25vw" }}>
          <div className="dropdown-content p-2" style={{ height: "100%" }}>
            <div
              className="box is-flex is-flex-direction-column pb-0 mb-2"
              style={{ overflowY: "auto", height: "30vh", padding: "0.25rem" }}
            >
              <div className="is-flex-grow-0">
                {currentState.can_go_back && (
                  <div
                    onClick={goToParentDirectory}
                    className="is-clickable is-unselectable folder-item"
                  >
                    <span className="icon">
                      <IonIcon name="folder" />
                    </span>
                    <span>..</span>
                  </div>
                )}
                {currentState.children.map((folder) => {
                  return (
                    <div
                      key={folder}
                      onClick={() => goToSubDirectory(folder)}
                      className="is-clickable is-unselectable folder-item"
                    >
                      <span className="icon">
                        <IonIcon name="folder" />
                      </span>
                      <span>{folder}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <div
              className="mt-0 pt-0 is-block"
              style={{ clear: "both", width: "100%", overflow: "hidden" }}
            >
              <button
                className="button is-danger ml-2 is-pulled-left"
                disabled={isLoading}
                onClick={cancel}
              >
                Cancel
              </button>
              <button
                className="button is-primary mr-2 is-pulled-right"
                disabled={isLoading || !currentState.root_is_writable}
                onClick={save}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
