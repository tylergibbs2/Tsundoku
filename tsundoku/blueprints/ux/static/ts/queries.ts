import { getReasonPhrase } from "http-status-codes";

import {
  APIResponse,
  Entry,
  Library,
  SeenRelease,
  Show,
  TreeResponse,
  WebhookBase,
  PaginatedShowsResponse,
} from "./interfaces";
import { APIError } from "./errors";
import { AddWebhookFormValues } from "./PageWebhooks/add_modal";
import { EditWebhookFormValues } from "./PageWebhooks/edit_modal";

const COMMON_HEADERS = {
  "Content-Type": "application/json",
};

export const fetchConfig = async <ConfigType>(
  config: string
): Promise<ConfigType> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/config/${config}`, request);
  if (!response.ok)
    throw new Error(`${response.status}: ${getReasonPhrase(response.status)}}`);

  let data: APIResponse<ConfigType> = await response.json();
  return data.result;
};

export const setConfig = async <ConfigType>(
  config: string,
  key: string,
  value: string
): Promise<ConfigType> => {
  let request = {
    method: "PATCH",
    headers: COMMON_HEADERS,
    body: JSON.stringify({
      [key]: value,
    }),
  };

  let response = await fetch(`/api/v1/config/${config}`, request);
  let data: APIResponse<ConfigType> = await response.json();
  if (response.ok) return data.result;

  throw new APIError(
    `Failed to set config, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const fetchWebhookBases = async (): Promise<WebhookBase[]> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch("/api/v1/webhooks", request);
  let data: APIResponse<WebhookBase[]> = await response.json();
  if (response.ok) return data.result;

  throw new APIError(
    `Failed to fetch webhook bases, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const fetchShows = async (
  page: number = 1,
  limit: number = 17,
  filters: string[] = [],
  textFilter: string = "",
  sortKey: string = "title",
  sortDirection: string = "+"
): Promise<PaginatedShowsResponse> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...(filters.length > 0 ? { filters: filters.join(",") } : {}),
    ...(textFilter ? { text_filter: textFilter } : {}),
    ...(sortKey ? { sort_key: sortKey } : {}),
    ...(sortDirection ? { sort_direction: sortDirection } : {}),
  });

  let response = await fetch(`/api/v1/shows?${params}`, request);
  let data: APIResponse<PaginatedShowsResponse> = await response.json();
  if (response.ok) return data.result;

  throw new APIError(
    `Failed to get shows list, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const fetchLibraries = async (): Promise<Library[]> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch("/api/v1/libraries", request);
  let data: APIResponse<Library[]> = await response.json();
  if (response.ok) return data.result;

  throw new APIError(
    `Failed to get libraries list, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const fetchShowById = async (id: number): Promise<Show> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/shows/${id}`, request);
  let data: APIResponse<Show> = await response.json();
  if (response.ok) return data.result;

  throw new APIError(
    `Failed to get show by ID '${id}', ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const fetchLibraryById = async (id: number): Promise<Library> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/libraries/${id}`, request);
  let data: APIResponse<Library> = await response.json();
  if (response.ok) return data.result;

  throw new APIError(
    `Failed to get library by ID '${id}', ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const fetchEntryById = async (id: number): Promise<Entry> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/entries/${id}`, request);
  let data: APIResponse<Entry> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to get entry by ID '${id}', ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const addNewLibrary = async (formData: any): Promise<Library> => {
  let request = {
    method: "POST",
    headers: COMMON_HEADERS,
    body: JSON.stringify(formData),
  };

  let response = await fetch("/api/v1/libraries", request);
  let data: APIResponse<Library> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to create new library, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const addNewShow = async (formData: any): Promise<Show> => {
  let request = {
    method: "POST",
    headers: COMMON_HEADERS,
    body: JSON.stringify(formData),
  };

  let response = await fetch("/api/v1/shows", request);
  let data: APIResponse<Show> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to create new show, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const addNewWebhook = async (
  formData: AddWebhookFormValues
): Promise<Show> => {
  let request = {
    method: "POST",
    headers: COMMON_HEADERS,
    body: JSON.stringify(formData),
  };

  let response = await fetch("/api/v1/webhooks", request);
  let data: APIResponse<Show> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to create new webhook, ${response.status}: ${getReasonPhrase(
      response.status
    )}`,
    data?.error
  );
};

export const updateShowById = async (show: Show): Promise<Show> => {
  let request = {
    method: "PUT",
    headers: COMMON_HEADERS,
    body: JSON.stringify(show),
  };

  let response = await fetch(`/api/v1/shows/${show.id_}`, request);
  let data: APIResponse<Show> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to update show by ID '${show.id_}', ${
      response.status
    }: ${getReasonPhrase(response.status)}`,
    data?.error
  );
};

export const updateLibraryById = async (library: Library): Promise<Library> => {
  let request = {
    method: "PUT",
    headers: COMMON_HEADERS,
    body: JSON.stringify(library),
  };

  let response = await fetch(`/api/v1/libraries/${library.id_}`, request);
  let data: APIResponse<Library> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to update library by ID '${library.id_}', ${
      response.status
    }: ${getReasonPhrase(response.status)}`,
    data?.error
  );
};

export const updateWebhookById = async (
  webhook: EditWebhookFormValues
): Promise<WebhookBase> => {
  let request = {
    method: "PUT",
    headers: COMMON_HEADERS,
    body: JSON.stringify(webhook),
  };

  let response = await fetch(`/api/v1/webhooks/${webhook.base_id}`, request);
  let data: APIResponse<WebhookBase> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to update webhook by ID '${webhook.base_id}', ${
      response.status
    }: ${getReasonPhrase(response.status)}`,
    data?.error
  );
};

export const deleteShowById = async (id: number): Promise<void> => {
  let request = {
    method: "DELETE",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/shows/${id}`, request);
  if (!response.ok)
    throw new Error(
      `Failed to delete show, ${response.status}: ${getReasonPhrase(
        response.status
      )}`
    );
};

export const deleteLibraryById = async (id: number): Promise<Library> => {
  let request = {
    method: "DELETE",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/libraries/${id}`, request);
  let data: APIResponse<Library> = await response.json();

  if (response.ok) return data.result;

  if (!response.ok)
    throw new Error(
      `Failed to delete library, ${response.status}: ${getReasonPhrase(
        response.status
      )}`
    );
};

export const fetchWebhookValidityById = async (
  id: number
): Promise<boolean> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/webhooks/${id}/valid`, request);
  let data: APIResponse<boolean> = await response.json();

  if (response.ok) return data.result;

  throw new APIError(
    `Failed to fetch webhook validity by ID '${id}', ${
      response.status
    }: ${getReasonPhrase(response.status)}`,
    data?.error
  );
};

export const deleteWebhookById = async (id: number): Promise<void> => {
  let request = {
    method: "DELETE",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/webhooks/${id}`, request);
  if (!response.ok)
    throw new Error(
      `Failed to delete webhook, ${response.status}: ${getReasonPhrase(
        response.status
      )}`
    );
};

type fetchDistinctFilters = {
  title?: string;
  release_group?: string;
  resolution?: string;
};

export const fetchDistinctSeenReleases = async (
  field: string,
  filters: fetchDistinctFilters = {}
): Promise<string[]> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let params = new URLSearchParams({ field: field, ...filters });
  let response = await fetch(
    `/api/v1/seen_releases/distinct?${params.toString()}`,
    request
  );
  let data: APIResponse<string[]> = await response.json();

  if (!response.ok) {
    throw new APIError(
      `Failed to get distinct field '${field}' seen releases, ${
        response.status
      }: ${getReasonPhrase(response.status)}`,
      data?.error
    );
  }

  return data.result;
};

type fetchFilteredFilters = {
  title?: string;
  release_group?: string;
  resolution?: string;
  episode?: string;
};

export const fetchFilteredSeenReleases = async (
  filters: fetchFilteredFilters = {}
): Promise<SeenRelease[]> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let params = new URLSearchParams(filters);
  let response = await fetch(
    `/api/v1/seen_releases/filter?${params.toString()}`,
    request
  );
  let data: APIResponse<SeenRelease[]> = await response.json();

  if (!response.ok) {
    throw new APIError(
      `Failed to get filtered seen releases, ${
        response.status
      }: ${getReasonPhrase(response.status)}`,
      data?.error
    );
  }

  return data.result;
};

export const fetchTree = async (
  dir: string,
  subdir: string | null = null
): Promise<TreeResponse> => {
  let request = {
    method: "POST",
    headers: COMMON_HEADERS,
    body: JSON.stringify({
      dir: dir,
      subdir: subdir,
    }),
  };

  let response = await fetch("/api/v1/tree", request);
  let data: APIResponse<TreeResponse> = await response.json();

  if (!response.ok) {
    throw new APIError(
      `Failed to get tree, ${response.status}: ${await response.text()}}`,
      data?.error
    );
  }

  return data.result;
};
