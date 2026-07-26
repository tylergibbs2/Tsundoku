import { queryOptions } from "@tanstack/react-query";

import { getEntry, getShow, getShows } from "../api";

// Keys and options for the logs page. Add to this as call sites here need it,
// rather than mirroring the whole API surface up front.
export const logKeys = {
  shows: (page: number, limit: number) => ["shows", { page, limit }] as const,
  show: (showId: number) => ["shows", { id_: showId }] as const,
  entry: (entryId: number) => ["entries", { id: entryId }] as const,
};

// Context lookups hang off log lines, so a miss should not be retried or
// refetched in the background.
const contextQueryDefaults = {
  retry: false,
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchOnReconnect: false,
} as const;

export const showsPageQuery = (page: number, limit: number) =>
  queryOptions({
    queryKey: logKeys.shows(page, limit),
    queryFn: async () =>
      (await getShows({ query: { page, limit }, throwOnError: true })).data
        .result,
  });

export const entryQuery = (entryId: number | null | undefined) =>
  queryOptions({
    queryKey: logKeys.entry(entryId ?? -1),
    queryFn: async () =>
      (
        await getEntry({
          path: { entry_id: entryId as number },
          throwOnError: true,
        })
      ).data.result,
    enabled: !!entryId,
    ...contextQueryDefaults,
  });

export const showQuery = (
  showId: number | null | undefined,
  enabled: boolean,
) =>
  queryOptions({
    queryKey: logKeys.show(showId ?? -1),
    queryFn: async () =>
      (
        await getShow({
          path: { show_id: showId as number },
          throwOnError: true,
        })
      ).data.result,
    enabled,
    ...contextQueryDefaults,
  });
