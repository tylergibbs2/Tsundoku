create type "public"."webhook_service" as enum ('discord', 'slack', 'custom');

create sequence "public"."webhook_id_seq";

alter table "public"."show_entry" drop constraint "show_entry_show_id_fkey";

create table "public"."webhook" (
    "id" smallint not null default nextval('webhook_id_seq'::regclass),
    "show_id" smallint,
    "wh_service" webhook_service,
    "wh_url" text not null,
    "content_fmt" text not null default '[{name}], episode [{episode}] has been marked as [{state}]'::text
);


create table "public"."wh_trigger" (
    "wh_id" smallint not null,
    "trigger" show_state not null
);


alter sequence "public"."webhook_id_seq" owned by "public"."webhook"."id";

CREATE UNIQUE INDEX webhook_pkey ON public.webhook USING btree (id);

CREATE UNIQUE INDEX wh_trigger_pkey ON public.wh_trigger USING btree (wh_id, trigger);

alter table "public"."webhook" add constraint "webhook_pkey" PRIMARY KEY using index "webhook_pkey";

alter table "public"."wh_trigger" add constraint "wh_trigger_pkey" PRIMARY KEY using index "wh_trigger_pkey";

alter table "public"."webhook" add constraint "webhook_show_id_fkey" FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE;

alter table "public"."wh_trigger" add constraint "wh_trigger_wh_id_fkey" FOREIGN KEY (wh_id) REFERENCES webhook(id) ON DELETE CASCADE;

alter table "public"."show_entry" add constraint "show_entry_show_id_fkey" FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE;

