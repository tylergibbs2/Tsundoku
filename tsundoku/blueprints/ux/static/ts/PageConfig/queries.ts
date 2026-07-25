import { queryOptions } from "@tanstack/react-query";

import {
  createLibrary,
  deleteLibrary,
  getFeedsConfig,
  getGeneralConfig,
  getLibraries,
  getTorrentConfig,
  updateFeedsConfig,
  updateGeneralConfig,
  updateLibrary,
  updateTorrentConfig,
} from "../api";
import type {
  FeedsConfigUpdate,
  GeneralConfigUpdate,
  Library,
  LibraryCreate,
  TorrentConfigUpdate,
} from "../api";

// Keys and options for the config page. Add to this as call sites here need
// it, rather than mirroring the whole API surface up front.
export const configKeys = {
  general: ["config", "general"] as const,
  feeds: ["config", "feeds"] as const,
  torrent: ["config", "torrent"] as const,
  libraries: ["libraries"] as const,
};

export const generalConfigQuery = () =>
  queryOptions({
    queryKey: configKeys.general,
    queryFn: async () =>
      (await getGeneralConfig({ throwOnError: true })).data.result,
  });

export const feedsConfigQuery = () =>
  queryOptions({
    queryKey: configKeys.feeds,
    queryFn: async () =>
      (await getFeedsConfig({ throwOnError: true })).data.result,
  });

export const torrentConfigQuery = () =>
  queryOptions({
    queryKey: configKeys.torrent,
    queryFn: async () =>
      (await getTorrentConfig({ throwOnError: true })).data.result,
  });

export const saveGeneralConfig = async (body: GeneralConfigUpdate) =>
  (await updateGeneralConfig({ body, throwOnError: true })).data.result;

export const saveFeedsConfig = async (body: FeedsConfigUpdate) =>
  (await updateFeedsConfig({ body, throwOnError: true })).data.result;

export const saveTorrentConfig = async (body: TorrentConfigUpdate) =>
  (await updateTorrentConfig({ body, throwOnError: true })).data.result;

export const librariesQuery = () =>
  queryOptions({
    queryKey: configKeys.libraries,
    queryFn: async () =>
      (await getLibraries({ throwOnError: true })).data.result,
  });

export const addLibrary = async (body: LibraryCreate) =>
  (await createLibrary({ body, throwOnError: true })).data.result;

export const editLibrary = async (library: Library) =>
  (
    await updateLibrary({
      path: { library_id: library.id_ },
      body: library,
      throwOnError: true,
    })
  ).data.result;

export const removeLibrary = async (libraryId: number) => {
  await deleteLibrary({ path: { library_id: libraryId }, throwOnError: true });
};
