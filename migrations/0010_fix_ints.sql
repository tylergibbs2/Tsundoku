alter table "public"."webhook" drop constraint "webhook_show_id_base_key";

alter table "public"."webhook_trigger" drop constraint "webhook_trigger_wh_id_fkey";

alter table "public"."webhook" drop constraint "webhook_pkey";

alter table "public"."webhook_trigger" drop constraint "webhook_trigger_pkey";

drop index if exists "public"."webhook_show_id_base_key";

drop index if exists "public"."webhook_pkey";

drop index if exists "public"."webhook_trigger_pkey";

alter table "public"."kitsu_info" alter column "show_id" set data type integer using "show_id"::integer;

alter table "public"."show_entry" alter column "show_id" set data type integer using "show_id"::integer;

alter table "public"."webhook" alter column "base" set not null;

alter table "public"."webhook" alter column "base" set data type integer using "base"::integer;

alter table "public"."webhook" alter column "show_id" set not null;

alter table "public"."webhook" alter column "show_id" set data type integer using "show_id"::integer;

alter table "public"."webhook_trigger" add column "base" integer;
alter table "public"."webhook_trigger" add column "show_id" integer;

alter table "public"."webhook_trigger" alter column "wh_id" drop not null;

-- Insert values into base and show_id here. based on wh_id
insert into "public"."webhook_trigger" ("base", "show_id", "trigger") select wh.base, wh.show_id, tr.trigger from "public"."webhook" as wh right join "public"."webhook_trigger" as tr on wh.id = tr.wh_id;

delete from "public"."webhook_trigger" where base is null or show_id is null;

alter table "public"."webhook_trigger" alter column "base" set not null;
alter table "public"."webhook_trigger" alter column "show_id" set not null;

alter table "public"."webhook_trigger" drop column "wh_id";
alter table "public"."webhook" drop column "id";

drop sequence if exists "public"."webhook_id_seq";

CREATE UNIQUE INDEX webhook_pkey ON public.webhook USING btree (show_id, base);

CREATE UNIQUE INDEX webhook_trigger_pkey ON public.webhook_trigger USING btree (show_id, base, trigger);

alter table "public"."webhook" add constraint "webhook_pkey" PRIMARY KEY using index "webhook_pkey";

alter table "public"."webhook_trigger" add constraint "webhook_trigger_pkey" PRIMARY KEY using index "webhook_trigger_pkey";

alter table "public"."webhook_trigger" add constraint "webhook_trigger_show_id_base_fkey" FOREIGN KEY (show_id, base) REFERENCES webhook(show_id, base) ON DELETE CASCADE;

