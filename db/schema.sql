-- Lauzhack test app schema (run in Supabase SQL editor)
create table if not exists public.items (
  id         bigserial primary key,
  name       text not null check (char_length(name) between 1 and 120),
  created_at timestamptz not null default now()
);

-- demo seed
insert into public.items (name) values ('first item'), ('second item');

-- API uses the service-role/direct connection, but keep RLS on and add a read policy
-- so the anon key can never do worse than read.
alter table public.items enable row level security;
drop policy if exists items_read on public.items;
create policy items_read on public.items for select using (true);
