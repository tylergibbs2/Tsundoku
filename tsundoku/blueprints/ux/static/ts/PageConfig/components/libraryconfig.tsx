import { ChangeEvent } from "react";
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

export const LibraryConfigApp = () => {
  const queryClient = useQueryClient();

  const libraries = useQuery(["libraries"], async () => {
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

  if (libraries.isLoading) return <GlobalLoading heightTranslation="none" />;

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
          {libraries.data.map((l) => (
            <LibraryTableRow
              key={l.id_}
              library={l}
              updateLibraryMutation={updateLibraryMutation}
              deleteLibraryMutation={deleteLibraryMutation}
            />
          ))}

          <AddLibraryLI addLibraryMutation={addLibraryMutation} />
        </tbody>
      </table>
    </div>
  );
};

type AddLibraryLIParams = {
  addLibraryMutation: UseMutationResult<Library>;
};

export const AddLibraryLI = ({ addLibraryMutation }: AddLibraryLIParams) => {
  const addEmptyLibrary = () => {
    addLibraryMutation.mutate({ folder: "/", is_default: false });
  };

  return (
    <tr>
      <td colSpan={4}>
        <button
          onClick={addEmptyLibrary}
          style={{ height: "100%" }}
          className="button is-outlined is-success is-large is-fullwidth"
        >
          <span className="icon">
            <IonIcon name="add-circle" />
          </span>
        </button>
      </td>
    </tr>
  );
};

type LibraryTableRowParams = {
  library: Library;
  updateLibraryMutation: UseMutationResult<Library>;
  deleteLibraryMutation: UseMutationResult<Library>;
};

const LibraryTableRow = ({
  library,
  updateLibraryMutation,
  deleteLibraryMutation,
}: LibraryTableRowParams) => {
  const setDefault = () => {
    updateLibraryMutation.mutate({
      id_: library.id_,
      folder: library.folder,
      is_default: true,
    });
  };

  const setNewLibraryFolder = (newFolder: string) => {
    updateLibraryMutation.mutate({ id_: library.id_, folder: newFolder });
  };

  const deleteThisLibrary = () => {
    deleteLibraryMutation.mutate(library.id_);
  };

  let defaultButton;
  if (library.is_default)
    defaultButton = (
      <button className="button is-primary mr-3" disabled>
        {_("libraries-td-default")}
      </button>
    );
  else
    defaultButton = (
      <button className="button is-primary mr-3" onClick={setDefault}>
        {_("libraries-td-set-default")}
      </button>
    );

  return (
    <tr>
      <td>
        <DirectorySelect
          defaultValue={library.folder}
          onChange={setNewLibraryFolder}
        />
      </td>
      <td>
        {defaultButton}
        <a className="button is-danger" onClick={deleteThisLibrary}>
          <span className="icon">
            <IonIcon name="trash" />
          </span>
        </a>
      </td>
    </tr>
  );
};
