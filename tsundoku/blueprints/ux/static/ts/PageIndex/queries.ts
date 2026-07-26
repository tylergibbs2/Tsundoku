import { queryOptions } from "@tanstack/react-query";
import type { Show, ShowCreate } from "../api";
import {
  createShow,
  deleteShow,
  distinctSeenReleases,
  filterSeenReleases,
  getGeneralConfig,
  getLibraries,
  getShows,
  updateShow,
} from "../api";

// Keys and options for the shows index. Add to this as call sites here need
// it, rather than mirroring the whole API surface up front.
export const indexKeys = {
  shows: (query: ShowsQuery) => ["shows", query] as const,
  libraries: ["libraries"] as const,
  generalConfig: ["config", "general"] as const,
  distinctReleases: (field: string, filters: SeenReleaseFilters) =>
    ["seen-releases", "distinct", field, filters] as const,
  filteredReleases: (filters: SeenReleaseFilters) =>
    ["seen-releases", "filter", filters] as const,
};

export type ShowsQuery = {
  page?: number;
  limit?: number;
  filters?: string;
  text_filter?: string;
  sort_key?: string;
  sort_direction?: string;
};

export type SeenReleaseFilters = {
  title?: string;
  release_group?: string;
  resolution?: string;
  episode?: number;
};

export const showsQuery = (query: ShowsQuery) =>
  queryOptions({
    queryKey: indexKeys.shows(query),
    queryFn: async () =>
      (await getShows({ query, throwOnError: true })).data.result,
  });

export const librariesQuery = () =>
  queryOptions({
    queryKey: indexKeys.libraries,
    queryFn: async () =>
      (await getLibraries({ throwOnError: true })).data.result,
  });

export const generalConfigQuery = () =>
  queryOptions({
    queryKey: indexKeys.generalConfig,
    queryFn: async () =>
      (await getGeneralConfig({ throwOnError: true })).data.result,
  });

export const distinctReleasesQuery = (
  field: string,
  filters: SeenReleaseFilters = {},
) =>
  queryOptions({
    queryKey: indexKeys.distinctReleases(field, filters),
    queryFn: async () =>
      (
        await distinctSeenReleases({
          query: { field, ...filters },
          throwOnError: true,
        })
      ).data.result,
  });

export const filteredReleasesQuery = (filters: SeenReleaseFilters = {}) =>
  queryOptions({
    queryKey: indexKeys.filteredReleases(filters),
    queryFn: async () =>
      (await filterSeenReleases({ query: filters, throwOnError: true })).data
        .result,
  });

export const addShow = async (body: ShowCreate) =>
  (await createShow({ body, throwOnError: true })).data.result;

export const editShow = async (show: Show) =>
  (
    await updateShow({
      path: { show_id: show.id_ },
      body: show,
      throwOnError: true,
    })
  ).data.result;

export const removeShow = async (showId: number) => {
  await deleteShow({ path: { show_id: showId }, throwOnError: true });
};
