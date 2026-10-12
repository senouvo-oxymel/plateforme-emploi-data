-- Base distante Supabase (PostgreSQL) pour le tableau de bord des offres data.
create table if not exists public.job_offers (
  id bigint generated always as identity primary key,
  source_id text not null,
  source_url text not null,
  title text not null,
  company text,
  country text,
  location text,
  work_mode text,
  contract_type text,
  salary text,
  published_at timestamptz,
  collected_at timestamptz not null default now(),
  deadline timestamptz,
  description text,
  skills text[] not null default '{}',
  status text not null default 'to_check' check (status in ('open','to_check','closed')),
  status_checked_at timestamptz,
  unique (source_id, source_url)
);
create index if not exists job_offers_country_idx on public.job_offers(country);
create index if not exists job_offers_collected_idx on public.job_offers(collected_at desc);
alter table public.job_offers enable row level security;
-- Public dashboard may read offers only; writes use the server-side service key.
drop policy if exists "Public can read offers" on public.job_offers;
create policy "Public can read offers" on public.job_offers for select using (true);
grant select on public.job_offers to anon, authenticated;
revoke insert, update, delete on public.job_offers from anon, authenticated;
