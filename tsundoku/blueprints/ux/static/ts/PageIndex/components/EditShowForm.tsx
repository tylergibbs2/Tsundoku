import { getInjector } from "../../fluent";
import { Show } from "../../interfaces";
import { ShowForm } from "./ShowForm";

const _ = getInjector();

interface EditShowFormParams {
  tab: string;
  show: Show;
  register: any;
}

export const EditShowForm = ({ tab, show, register }: EditShowFormParams) => {
  return <ShowForm mode="edit" show={show} register={register} tab={tab} />;
};
