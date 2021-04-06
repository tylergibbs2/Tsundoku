create extension if not exists "uuid-ossp" with schema "public" version '1.1';

alter table "public"."users" add column "api_key" uuid not null default uuid_generate_v4();
