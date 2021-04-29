create table "public"."encode" (
    "entry_id" integer not null,
    "initial_size" bigint,
    "final_size" bigint,
    "started_at" timestamp without time zone not null default now_utc(),
    "ended_at" timestamp without time zone
);

CREATE UNIQUE INDEX encode_pkey ON public.encode USING btree (entry_id);

alter table "public"."encode" add constraint "encode_pkey" PRIMARY KEY using index "encode_pkey";

alter table "public"."encode" add constraint "encode_entry_id_fkey" FOREIGN KEY (entry_id) REFERENCES show_entry(id) on delete cascade;
