import { APIResponse, Entry, Show, WebhookBase } from "./interfaces";

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
    throw new Error(`${response.status}: ${response.statusText}}`);

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
  if (response.ok) {
    let data: APIResponse<ConfigType> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to set config, ${response.status}: ${response.statusText}`
  );
};

export const fetchWebhookBases = async (): Promise<WebhookBase[]> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch("/api/v1/webhooks", request);
  if (response.ok) {
    let data: APIResponse<WebhookBase[]> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to fetch webhook bases, ${response.status}: ${response.statusText}`
  );
};

export const fetchShows = async (): Promise<Show[]> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch("/api/v1/shows", request);
  if (response.ok) {
    let data: APIResponse<Show[]> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to get shows list, ${response.status}: ${response.statusText}`
  );
};

export const fetchShowById = async (id: number): Promise<Show> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/shows/${id}`, request);
  if (response.ok) {
    let data: APIResponse<Show> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to get show by ID '${id}', ${response.status}: ${response.statusText}`
  );
};

export const fetchEntryById = async (id: number): Promise<Entry> => {
  let request = {
    method: "GET",
    headers: COMMON_HEADERS,
  };

  let response = await fetch(`/api/v1/entries/${id}`, request);
  if (response.ok) {
    let data: APIResponse<Entry> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to get entry by ID '${id}', ${response.status}: ${response.statusText}`
  );
};

export const addNewShow = async (formData: any): Promise<Show> => {
  let request = {
    method: "POST",
    headers: COMMON_HEADERS,
    body: JSON.stringify(formData),
  };

  let response = await fetch("/api/v1/shows", request);
  if (response.ok) {
    let data: APIResponse<Show> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to create new show, ${response.status}: ${response.statusText}`
  );
};

export const addNewWebhook = async (formData: any): Promise<Show> => {
  let request = {
    method: "POST",
    headers: COMMON_HEADERS,
    body: JSON.stringify(formData),
  };

  let response = await fetch("/api/v1/webhooks", request);
  if (response.ok) {
    let data: APIResponse<Show> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to create new webhook, ${response.status}: ${response.statusText}`
  );
};

export const updateShowById = async (show: Show): Promise<Show> => {
  let request = {
    method: "PUT",
    headers: COMMON_HEADERS,
    body: JSON.stringify(show),
  };

  let response = await fetch(`/api/v1/shows/${show.id_}`, request);
  if (response.ok) {
    let data: APIResponse<Show> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to update show by ID '${show.id_}', ${response.status}: ${response.statusText}`
  );
};

export const updateWebhookById = async (
  webhook: WebhookBase
): Promise<WebhookBase> => {
  let request = {
    method: "PUT",
    headers: COMMON_HEADERS,
    body: JSON.stringify(webhook),
  };

  let response = await fetch(`/api/v1/webhooks/${webhook.base_id}`, request);
  if (response.ok) {
    let data: APIResponse<WebhookBase> = await response.json();
    return data.result;
  }

  throw new Error(
    `Failed to update webhook by ID '${webhook.base_id}', ${response.status}: ${response.statusText}`
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
      `Failed to delete show, ${response.status}: ${response.statusText}`
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
      `Failed to delete webhook, ${response.status}: ${response.statusText}`
    );
};
