create table "public"."kitsu_info" (
    "show_id" smallint not null,
    "kitsu_id" integer,
    "cached_poster_url" text,
    "show_status" text,
    "slug" text,
    "last_updated" timestamp without time zone not null default now()
);

insert into "public"."kitsu_info" ("show_id", "kitsu_id", "cached_poster_url") select "public"."shows"."id", "public"."shows"."kitsu_id", "public"."shows"."cached_poster_url" from "public"."shows";

alter table "public"."shows" drop column "cached_poster_url";

alter table "public"."shows" drop column "kitsu_id";

CREATE UNIQUE INDEX kitsu_info_pkey ON public.kitsu_info USING btree (show_id);

alter table "public"."kitsu_info" add constraint "kitsu_info_pkey" PRIMARY KEY using index "kitsu_info_pkey";

alter table "public"."kitsu_info" add constraint "kitsu_info_show_id_fkey" FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE;

