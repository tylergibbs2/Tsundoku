import { queryOptions } from "@tanstack/react-query";
import type { WebhookBaseCreate, WebhookBaseUpdate } from "../api";
import {
  createWebhookBase,
  deleteWebhookBase,
  getWebhookBases,
  updateWebhookBase,
  webhookIsValid,
} from "../api";

// Keys and options for the webhooks page. Add to this as call sites here need
// it, rather than mirroring the whole API surface up front.
export const webhookKeys = {
  bases: ["webhooks"] as const,
  validity: (baseId: number) => ["webhook-validity", baseId] as const,
};

export const webhookBasesQuery = () =>
  queryOptions({
    queryKey: webhookKeys.bases,
    queryFn: async () =>
      (await getWebhookBases({ throwOnError: true })).data.result,
  });

export const webhookValidityQuery = (baseId: number) =>
  queryOptions({
    queryKey: webhookKeys.validity(baseId),
    queryFn: async () =>
      (
        await webhookIsValid({
          path: { base_id: baseId },
          throwOnError: true,
        })
      ).data.result,
  });

export const addWebhook = async (body: WebhookBaseCreate) =>
  (await createWebhookBase({ body, throwOnError: true })).data.result;

export const editWebhook = async (baseId: number, body: WebhookBaseUpdate) =>
  (
    await updateWebhookBase({
      path: { base_id: baseId },
      body,
      throwOnError: true,
    })
  ).data.result;

export const removeWebhook = async (baseId: number) => {
  await deleteWebhookBase({ path: { base_id: baseId }, throwOnError: true });
};
