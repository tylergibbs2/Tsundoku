import { getInjector } from "../../fluent";
import { useState, Dispatch, SetStateAction, JSX } from "react";
import { useForm } from "react-hook-form";
import { Show, Entry, EntryEncodeInfo } from "../../interfaces";
import {
  localizePythonTimeAbsolute,
  localizePythonTimeRelative,
  formatBytes,
} from "../../utils";

const _ = getInjector();

interface EditShowEntriesParams {
  tab: string;
  show: Show;
  setEntriesToAdd: Dispatch<SetStateAction<Entry[]>>;
  setEntriesToDelete: Dispatch<SetStateAction<Entry[]>>;
  entriesToAdd: Entry[];
  entriesToDelete: Entry[];
  highlightNewEntryId: number | null;
}

export const EditShowEntries = ({
  tab,
  show,
  setEntriesToAdd,
  setEntriesToDelete,
  entriesToAdd,
  entriesToDelete,
  highlightNewEntryId,
}: EditShowEntriesParams) => {
  const [fakeId, setFakeId] = useState<number>(-1);
  const { register, handleSubmit, reset } = useForm();

  if (show === null) return <></>;

  // Compute deleted IDs for filtering
  const deletedIds = new Set(entriesToDelete.map((e) => e.id));
  // Combine show.entries and entriesToAdd, removing duplicates by id, and filter out deleted
  const allEntries = [...(show.entries || []), ...(entriesToAdd || [])]
    .filter(
      (entry, index, self) => index === self.findIndex((e) => e.id === entry.id)
    )
    .filter((entry) => !deletedIds.has(entry.id))
    .sort((a, b) => a.episode - b.episode);

  const bufferAddEntry = (data: any) => {
    let newEpNum = parseInt(data.episode);
    if (newEpNum < 0) {
      reset();
      return;
    }

    let entry = {
      id: fakeId,
      episode: newEpNum,
      version: "v0",
      show_id: show.id_,
      state: "buffered",
      magnet: data.magnet,
      created_manually: true,
      last_update: new Date().toISOString(),
      encode: null,
    };

    let exists = allEntries.findIndex(
      (existing: Entry) => existing.episode === newEpNum
    );
    if (exists !== -1) {
      reset();
      return;
    }

    setFakeId(fakeId - 1);
    setEntriesToAdd([entry, ...entriesToAdd]);
    reset();
  };

  const bufferRemoveEntry = (entry: Entry) => {
    // Remove from entriesToAdd if present
    setEntriesToAdd(entriesToAdd.filter((e) => e.id !== entry.id));
    // If entry has a positive id (exists in backend), add to entriesToDelete
    if (entry.id > 0) {
      setEntriesToDelete([entry, ...entriesToDelete]);
    }
  };

  return (
    <div className={tab !== "entries" ? "is-hidden" : ""}>
      {allEntries.length > 0 && (
        <table className="table is-fullwidth is-hoverable">
          <thead>
            <tr>
              <th>{_("edit-entries-th-episode")}</th>
              <th>{_("edit-entries-th-status")}</th>
              <th>{_("edit-entries-th-encode-status")}</th>
              <th>{_("edit-entries-th-last-update")}</th>
            </tr>
          </thead>
          <tbody>
            {allEntries.map((entry: Entry) => (
              <EntryRow
                key={entry.id}
                entry={entry}
                bufferRemoveEntry={bufferRemoveEntry}
                highlightNewEntryId={highlightNewEntryId}
              />
            ))}
          </tbody>
        </table>
      )}
      {allEntries.length === 0 && (
        <div className="container has-text-centered mb-5">
          <h2 className="subtitle">{_("edit-entries-is-empty")}</h2>
        </div>
      )}
      <form onSubmit={handleSubmit(bufferAddEntry)}>
        <div className="field is-horizontal">
          <div className="field-body">
            <div className="field-label is-normal">
              <label className="label">{_("edit-entries-form-episode")}</label>
            </div>
            <div className="field">
              <input
                {...register("episode")}
                min="0"
                className="input"
                type="number"
                defaultValue="0"
                required
              />
              <p className="help is-danger is-hidden">
                {_("edit-entries-form-exists")}
              </p>
            </div>
            <div className="field">
              <input
                {...register("magnet")}
                className="input"
                type="text"
                placeholder={_("edit-entries-form-magnet")}
              />
            </div>
            <input
              className="button is-success"
              type="submit"
              value={_("edit-entries-form-add-button")}
            />
          </div>
        </div>
      </form>
    </div>
  );
};

interface EntryRowParams {
  entry: Entry;
  bufferRemoveEntry: any;
  highlightNewEntryId: number | null;
}

const EntryRow = ({
  entry,
  bufferRemoveEntry,
  highlightNewEntryId,
}: EntryRowParams) => {
  const bufferDelete = () => {
    bufferRemoveEntry(entry);
  };

  const localized = localizePythonTimeRelative(entry.last_update);
  const localizedTitle = localizePythonTimeAbsolute(entry.last_update);

  const getEncodeStatusTd = (): JSX.Element => {
    let content = getEncodeStatusDropdownContent(entry?.encode);
    let trigger = getEncodeStatusDropdownTrigger(
      entry?.encode,
      content !== null
    );

    if (content === null) return trigger;

    return (
      <div className="dropdown is-hoverable">
        <div className="dropdown-trigger">{trigger}</div>
        <div className="dropdown-menu">{content}</div>
      </div>
    );
  };

  const getEncodeStatusDropdownTrigger = (
    encode: EntryEncodeInfo,
    withUnderline: boolean
  ): JSX.Element => {
    let style = withUnderline ? { borderBottom: "1px dashed #dbdbdb" } : {};

    if (!encode?.queued_at)
      return (
        <span style={style}>{_("edit-entries-encode-status-notqueued")}</span>
      );
    else if (encode?.ended_at)
      return (
        <span style={style}>{_("edit-entries-encode-status-finished")}</span>
      );
    else if (encode?.started_at)
      return (
        <span style={style}>{_("edit-entries-encode-status-encoding")}</span>
      );
    else if (encode?.queued_at)
      return (
        <span style={style}>{_("edit-entries-encode-status-queued")}</span>
      );

    return <span style={style}>{_("edit-entries-encode-status-unknown")}</span>;
  };

  const getEncodeStatusDropdownContent = (
    encode: EntryEncodeInfo
  ): JSX.Element | null => {
    if (!encode?.queued_at) return null;
    else if (encode?.ended_at) {
      return (
        <div className="dropdown-content">
          <div className="dropdown-item">
            <p>
              Finished at{" "}
              {localizePythonTimeAbsolute(encode.ended_at, "short", "short")}
            </p>
          </div>
          <div className="dropdown-item">
            <p>
              {formatBytes(encode.initial_size)} {" -> "}{" "}
              {formatBytes(encode.final_size)}
            </p>
          </div>
        </div>
      );
    } else if (encode?.started_at) {
      return (
        <div className="dropdown-content">
          <div className="dropdown-item">
            <p>
              Started at{" "}
              {localizePythonTimeAbsolute(encode.started_at, "short", "short")}
            </p>
          </div>
        </div>
      );
    } else if (encode?.queued_at) {
      return (
        <div className="dropdown-content">
          <div className="dropdown-item">
            <p>
              Queued at{" "}
              {localizePythonTimeAbsolute(encode.queued_at, "short", "short")}
            </p>
          </div>
        </div>
      );
    }
  };

  return (
    <tr className={highlightNewEntryId === entry.id ? "is-highlighted" : ""}>
      <td>
        {entry.episode}
        {entry.version}
      </td>
      <td>{_(`entry-status-${entry.state}`)}</td>
      <td>{getEncodeStatusTd()}</td>
      <td title={localizedTitle}>
        {_("edit-entries-last-update", { time: localized })}
      </td>
      <td>
        <button className="delete" onClick={bufferDelete}></button>
      </td>
    </tr>
  );
};
