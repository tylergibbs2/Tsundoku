alter table "public"."show_entry" alter column "id" set data type integer using "id"::integer;

alter table "public"."shows" alter column "id" set data type integer using "id"::integer;

alter table "public"."users" alter column "id" set data type integer using "id"::integer;

alter table "public"."webhook" alter column "id" set data type integer using "id"::integer;

alter table "public"."webhook_base" alter column "id" set data type integer using "id"::integer;

