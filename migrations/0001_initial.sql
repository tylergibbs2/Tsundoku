create type "public"."show_state" as enum ('downloading', 'downloaded', 'renamed', 'moved', 'completed');

create sequence "public"."show_entry_id_seq";

create sequence "public"."show_entry_show_id_seq";

create sequence "public"."shows_id_seq";

create sequence "public"."users_id_seq";

create table "public"."show_entry" (
    "id" bigint not null default nextval('show_entry_id_seq'::regclass),
    "show_id" bigint not null default nextval('show_entry_show_id_seq'::regclass),
    "episode" smallint not null,
    "current_state" show_state not null default 'downloading'::show_state,
    "torrent_hash" text not null,
    "file_path" text
);


create table "public"."shows" (
    "id" bigint not null default nextval('shows_id_seq'::regclass),
    "title" text not null,
    "desired_format" text,
    "desired_folder" text,
    "season" smallint not null,
    "episode_offset" smallint not null default 0,
    "kitsu_id" integer,
    "cached_poster_url" text
);


create table "public"."users" (
    "id" smallint not null default nextval('users_id_seq'::regclass),
    "username" text not null,
    "password_hash" text not null,
    "created_at" timestamp without time zone not null default now()
);


alter sequence "public"."show_entry_id_seq" owned by "public"."show_entry"."id";

alter sequence "public"."show_entry_show_id_seq" owned by "public"."show_entry"."show_id";

alter sequence "public"."shows_id_seq" owned by "public"."shows"."id";

alter sequence "public"."users_id_seq" owned by "public"."users"."id";

CREATE UNIQUE INDEX show_entry_pkey ON public.show_entry USING btree (id);

CREATE UNIQUE INDEX shows_pkey ON public.shows USING btree (id);

CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id);

CREATE UNIQUE INDEX users_username_key ON public.users USING btree (username);

alter table "public"."show_entry" add constraint "show_entry_pkey" PRIMARY KEY using index "show_entry_pkey";

alter table "public"."shows" add constraint "shows_pkey" PRIMARY KEY using index "shows_pkey";

alter table "public"."users" add constraint "users_pkey" PRIMARY KEY using index "users_pkey";

alter table "public"."show_entry" add constraint "show_entry_show_id_fkey" FOREIGN KEY (show_id) REFERENCES shows(id);

alter table "public"."users" add constraint "users_username_key" UNIQUE using index "users_username_key";

