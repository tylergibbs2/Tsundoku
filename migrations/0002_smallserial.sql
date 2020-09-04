alter table "public"."show_entry" alter column "id" set data type smallint using "id"::smallint;

alter table "public"."show_entry" alter column "show_id" drop default;

alter table "public"."show_entry" alter column "show_id" set data type smallint using "show_id"::smallint;

alter table "public"."shows" alter column "id" set data type smallint using "id"::smallint;

drop sequence if exists "public"."show_entry_show_id_seq";

