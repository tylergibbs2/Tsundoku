import { useQuery } from "@tanstack/react-query";
import type { UseFormRegister } from "react-hook-form";
import type { AddShowFormValues } from "../add_modal";
import { librariesQuery } from "../queries";

type LibrarySelectParams = {
  register: UseFormRegister<AddShowFormValues>;
};

export const LibrarySelect = ({ register }: LibrarySelectParams) => {
  const libraries = useQuery(librariesQuery());

  if (libraries.isPending || !libraries.data)
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
