import {
  ChangeEvent,
  useEffect,
  useImperativeHandle,
  forwardRef,
  useState,
} from "react";
import { Library } from "../../interfaces";
import { getInjector } from "../../fluent";
import {
  useMutation,
  useQuery,
  useQueryClient,
  UseMutationResult,
} from "react-query";
import {
  addNewLibrary,
  deleteLibraryById,
  fetchLibraries,
  updateLibraryById,
} from "../../queries";
import { GlobalLoading } from "../../Components/GlobalLoading";
import { DirectorySelect } from "../../Components/DirectorySelect";
import { toast } from "bulma-toast";
import { IonIcon } from "../../icon";

const _ = getInjector();

interface LibraryConfigAppProps {
  onDirtyChange: (dirty: boolean) => void;
}

export const LibraryConfigApp = forwardRef(
  ({ onDirtyChange }: LibraryConfigAppProps, ref) => {
    const queryClient = useQueryClient();

    const librariesQuery = useQuery(["libraries"], async () => {
      return await fetchLibraries();
    });

    const addLibraryMutation = useMutation(addNewLibrary, {
      onSuccess: (newLibrary) => {
        queryClient.setQueryData(["libraries"], (oldLibraries: Library[]) => [
          ...oldLibraries,
          newLibrary,
        ]);
      },
    });

    const deleteLibraryMutation = useMutation(deleteLibraryById, {
      onSuccess: (oldLibrary: Library) => {
        queryClient.setQueryData(["libraries"], (oldLibraries: Library[]) =>
          oldLibraries.filter((l) => l.id_ !== oldLibrary?.id_)
        );
        toast({
          message: _("libraries-delete-success"),
          duration: 5000,
          position: "bottom-right",
          type: "is-success",
          dismissible: true,
          animate: { in: "fadeIn", out: "fadeOut" },
        });
      },
    });

    const updateLibraryMutation = useMutation(updateLibraryById, {
      onSuccess: (updatedLibrary: Library) => {
        queryClient.setQueryData(["libraries"], (oldLibraries: Library[]) =>
          oldLibraries.map((l) => {
            if (updatedLibrary.is_default) l.is_default = false;
            if (l.id_ === updatedLibrary.id_) {
              l = updatedLibrary;
            }
            return l;
          })
        );
        toast({
          message: _("libraries-update-success"),
          duration: 5000,
          position: "bottom-right",
          type: "is-success",
          dismissible: true,
          animate: { in: "fadeIn", out: "fadeOut" },
        });
      },
    });

    const [localLibraries, setLocalLibraries] = useState<Library[]>([]);
    const [dirty, setDirty] = useState(false);
    const [added, setAdded] = useState<Library[]>([]);
    const [deleted, setDeleted] = useState<Library[]>([]);
    const [updated, setUpdated] = useState<Library[]>([]);

    useEffect(() => {
      if (librariesQuery.data) {
        setLocalLibraries([...librariesQuery.data]);
        setAdded([]);
        setDeleted([]);
        setUpdated([]);
        setDirty(false);
        onDirtyChange(false);
      }
    }, [librariesQuery.data]);

    useEffect(() => {
      // Dirty if any added, deleted, or updated
      const isDirty =
        added.length > 0 || deleted.length > 0 || updated.length > 0;
      setDirty(isDirty);
      onDirtyChange(isDirty);
    }, [added, deleted, updated]);

    useImperativeHandle(ref, () => ({
      async save() {
        // Save added
        for (const lib of added) {
          await addLibraryMutation.mutateAsync(lib);
        }
        // Save updated
        for (const lib of updated) {
          await updateLibraryMutation.mutateAsync(lib);
        }
        // Save deleted
        for (const lib of deleted) {
          await deleteLibraryMutation.mutateAsync(lib.id_);
        }
        setAdded([]);
        setDeleted([]);
        setUpdated([]);
        setDirty(false);
        onDirtyChange(false);
      },
    }));

    if (librariesQuery.isLoading)
      return <GlobalLoading heightTranslation="none" />;

    const setDefault = (id_: number) => {
      setLocalLibraries((libs) =>
        libs.map((l) => ({ ...l, is_default: l.id_ === id_ }))
      );
      setUpdated((prev) => [
        ...prev.filter((l) => l.id_ !== id_),
        { ...localLibraries.find((l) => l.id_ === id_), is_default: true },
      ]);
    };

    const setNewLibraryFolder = (id_: number, newFolder: string) => {
      setLocalLibraries((libs) =>
        libs.map((l) => (l.id_ === id_ ? { ...l, folder: newFolder } : l))
      );
      setUpdated((prev) => [
        ...prev.filter((l) => l.id_ !== id_),
        { ...localLibraries.find((l) => l.id_ === id_), folder: newFolder },
      ]);
    };

    const deleteThisLibrary = (id_: number) => {
      setLocalLibraries((libs) => libs.filter((l) => l.id_ !== id_));
      setDeleted((prev) => [
        ...prev,
        localLibraries.find((l) => l.id_ === id_),
      ]);
    };

    const addLibrary = (folder: string) => {
      const newLib: Library = {
        id_: Math.random(),
        folder,
        is_default: false,
      };
      setLocalLibraries((libs) => [...libs, newLib]);
      setAdded((prev) => [...prev, newLib]);
    };

    return (
      <div className="box">
        <table className="table is-fullwidth">
          <thead>
            <tr>
              <th>{_("libraries-th-directory")}</th>
              <th>{_("libraries-th-actions")}</th>
            </tr>
          </thead>
          <tbody>
            {localLibraries.map((l) => (
              <tr key={l.id_}>
                <td>
                  <DirectorySelect
                    defaultValue={l.folder}
                    onChange={(newFolder) =>
                      setNewLibraryFolder(l.id_, newFolder)
                    }
                  />
                </td>
                <td>
                  {l.is_default ? (
                    <button className="button is-primary mr-3" disabled>
                      {_("libraries-td-default")}
                    </button>
                  ) : (
                    <button
                      className="button is-primary mr-3"
                      onClick={() => setDefault(l.id_)}
                    >
                      {_("libraries-td-set-default")}
                    </button>
                  )}
                  <a
                    className="button is-danger"
                    onClick={() => deleteThisLibrary(l.id_)}
                  >
                    <span className="icon">
                      <IonIcon name="trash" />
                    </span>
                  </a>
                </td>
              </tr>
            ))}
            <tr>
              <td colSpan={2}>
                <button
                  className="button is-link is-fullwidth"
                  onClick={() => {
                    addLibrary("/");
                  }}
                >
                  {_("libraries-add-button")}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }
);
