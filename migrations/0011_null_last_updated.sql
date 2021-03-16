alter table "public"."kitsu_info" alter column "last_updated" drop default;

alter table "public"."kitsu_info" alter column "last_updated" drop not null;

update "public"."kitsu_info" set "last_updated" = null;
