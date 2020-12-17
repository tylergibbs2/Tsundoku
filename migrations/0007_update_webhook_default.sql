alter table "public"."webhook_base" alter column "content_fmt" set default '{name}, episode {episode}, has been marked as {state}'::text;

