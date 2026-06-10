create extension if not exists pgcrypto;
create extension if not exists citext;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.categories (
  id uuid primary key default gen_random_uuid(),
  name citext not null unique check (char_length(trim(name::text)) between 1 and 40),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.search_history (
  id uuid primary key default gen_random_uuid(),
  prompt text not null check (char_length(trim(prompt)) between 1 and 500),
  category_id uuid not null references public.categories(id) on delete restrict,
  searched_at timestamptz not null default timezone('utc', now()),
  result_count integer not null default 0 check (result_count >= 0),
  result_payload jsonb not null default '[]'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

drop trigger if exists categories_set_updated_at on public.categories;
create trigger categories_set_updated_at
before update on public.categories
for each row execute function public.set_updated_at();

drop trigger if exists search_history_set_updated_at on public.search_history;
create trigger search_history_set_updated_at
before update on public.search_history
for each row execute function public.set_updated_at();

insert into public.categories (name)
values ('Default'), ('Trending')
on conflict (name) do nothing;

alter table public.categories enable row level security;
alter table public.search_history enable row level security;

-- The backend uses the service-role key and bypasses RLS.
-- Do not add anonymous write policies unless the threat model changes.

