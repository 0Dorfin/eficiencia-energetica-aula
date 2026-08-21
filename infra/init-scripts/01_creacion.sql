CREATE TABLE public.ltss (
  "time"      timestamptz NOT NULL,
  entity_id   varchar     NOT NULL,
  state       varchar     NULL,
  attributes  jsonb       NULL
);
