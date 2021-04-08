set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.now_utc()
 RETURNS timestamp without time zone
 LANGUAGE sql
AS $function$
  SELECT NOW() AT TIME ZONE 'utc';
$function$
;


alter table "public"."show_entry" add column "last_update" timestamp without time zone not null default now_utc();

alter table "public"."shows" add column "created_at" timestamp without time zone not null default now_utc();

alter table "public"."users" alter column "created_at" set default now_utc();
