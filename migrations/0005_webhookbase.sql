create sequence "public"."webhook_base_id_seq";

alter table "public"."wh_trigger" drop constraint "wh_trigger_wh_id_fkey";

alter table "public"."wh_trigger" drop constraint "wh_trigger_pkey";

drop index if exists "public"."wh_trigger_pkey";

drop table "public"."wh_trigger";

create table "public"."webhook_base" (
    "id" smallint not null default nextval('webhook_base_id_seq'::regclass),
    "base_service" webhook_service not null,
    "base_url" text not null,
    "content_fmt" text not null default '[{name}], episode [{episode}] has been marked as [{state}]'::text
);


create table "public"."webhook_trigger" (
    "wh_id" smallint not null,
    "trigger" show_state not null
);


alter table "public"."webhook" drop column "content_fmt";

alter table "public"."webhook" drop column "wh_service";

alter table "public"."webhook" drop column "wh_url";

alter table "public"."webhook" add column "base" smallint;

alter sequence "public"."webhook_base_id_seq" owned by "public"."webhook_base"."id";

CREATE UNIQUE INDEX webhook_base_pkey ON public.webhook_base USING btree (id);

CREATE UNIQUE INDEX webhook_trigger_pkey ON public.webhook_trigger USING btree (wh_id, trigger);

alter table "public"."webhook_base" add constraint "webhook_base_pkey" PRIMARY KEY using index "webhook_base_pkey";

alter table "public"."webhook_trigger" add constraint "webhook_trigger_pkey" PRIMARY KEY using index "webhook_trigger_pkey";

alter table "public"."webhook" add constraint "webhook_base_fkey" FOREIGN KEY (base) REFERENCES webhook_base(id) ON DELETE CASCADE;

alter table "public"."webhook_trigger" add constraint "webhook_trigger_wh_id_fkey" FOREIGN KEY (wh_id) REFERENCES webhook(id) ON DELETE CASCADE;

