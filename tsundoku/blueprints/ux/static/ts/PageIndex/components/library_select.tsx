import { useQuery } from "react-query";
import { fetchLibraries } from "../../queries";
import { UseFormRegister } from "react-hook-form";
import { AddShowFormValues } from "../add_modal";

type LibrarySelectParams = {
  register: UseFormRegister<AddShowFormValues>;
};

export const LibrarySelect = ({ register }: LibrarySelectParams) => {
  const libraries = useQuery(["libraries"], async () => {
    return await fetchLibraries();
  });

  if (libraries.isLoading)
    return (
      <div className="select is-loading is-fullwidth">
        <select disabled></select>
      </div>
    );

  return (
    <div className="select is-fullwidth">
      <select {...register("library_id", { required: true })}>
        {libraries.data.map((l) => (
          <option key={l.id_} value={l.id_}>
            {l.folder}
          </option>
        ))}
      </select>
    </div>
  );
};
