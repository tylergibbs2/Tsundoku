CREATE UNIQUE INDEX webhook_show_id_base_key ON public.webhook USING btree (show_id, base);

alter table "public"."webhook" add constraint "webhook_show_id_base_key" UNIQUE using index "webhook_show_id_base_key";

