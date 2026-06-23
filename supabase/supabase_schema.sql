-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Profiles Table
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    balance numeric(20,2) default 10000000.00,
    created_at timestamp default now()
);

-- 2. Orders Table
create table if not exists public.orders (
    id uuid primary key,
    user_id uuid references public.profiles(id),
    side text check (side in ('BUY', 'SELL')),
    price numeric(20,2) not null,
    quantity numeric(20,6) not null,
    status text check (status in ('NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED')),
    is_bot boolean default false,
    source text default 'user',
    created_at timestamp default now()
);

-- 3. Trades Table
create table if not exists public.trades (
    id uuid primary key,
    buyer_id uuid references public.profiles(id),
    seller_id uuid references public.profiles(id),
    price numeric(20,2) not null,
    quantity numeric(20,6) not null,
    is_bot_trade boolean default false,
    created_at timestamp default now()
);

-- 4. Portfolios Table
create table if not exists public.portfolios (
    user_id uuid references public.profiles(id) on delete cascade,
    asset text,
    quantity numeric(20,6) default 0,
    avg_price numeric(20,2) default 0,
    primary key (user_id, asset)
);

-- Indexes
create index if not exists idx_orders_user on public.orders(user_id);
create index if not exists idx_trades_time on public.trades(created_at);
create index if not exists idx_portfolio_user on public.portfolios(user_id);

-- Constraints
alter table public.orders drop constraint if exists check_price_positive;
alter table public.orders add constraint check_price_positive check (price > 0);

alter table public.orders drop constraint if exists check_quantity_positive;
alter table public.orders add constraint check_quantity_non_negative check (quantity >= 0);

alter table public.trades drop constraint if exists check_trade_price_positive;
alter table public.trades add constraint check_trade_price_positive check (price > 0);

alter table public.trades drop constraint if exists check_trade_quantity_positive;
alter table public.trades add constraint check_trade_quantity_positive check (quantity > 0);

-- Triggers: Auto Profile Creation
create or replace function public.create_profile()
returns trigger as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.create_profile();

-- Seed System Bot User & Profile (for Simulator FK compatibility)
insert into auth.users (id, email, raw_user_meta_data, created_at, updated_at, role, aud)
values (
  '00000000-0000-0000-0000-000000000000',
  'bot@nanotrade.com',
  '{"name": "Market Simulator Bot"}'::jsonb,
  now(),
  now(),
  'authenticated',
  'authenticated'
) on conflict (id) do nothing;

insert into public.profiles (id, balance)
values ('00000000-0000-0000-0000-000000000000', 999999999999.00)
on conflict (id) do nothing;

-- Row Level Security (RLS)
alter table public.profiles enable row level security;
alter table public.orders enable row level security;
alter table public.trades enable row level security;
alter table public.portfolios enable row level security;

-- SELECT Policies
drop policy if exists "Users can view their profile" on public.profiles;
create policy "Users can view their profile"
on public.profiles for select using (auth.uid() = id);

drop policy if exists "Users can view their orders" on public.orders;
create policy "Users can view their orders"
on public.orders for select using (auth.uid() = user_id);

drop policy if exists "Users can view their trades" on public.trades;
create policy "Users can view their trades"
on public.trades for select using (auth.uid() = buyer_id OR auth.uid() = seller_id);

drop policy if exists "Users can view their portfolio" on public.portfolios;
create policy "Users can view their portfolio"
on public.portfolios for select using (auth.uid() = user_id);

-- WRITE Block Policies (Client direct write prevention)
drop policy if exists "No direct insert orders" on public.orders;
create policy "No direct insert orders"
on public.orders for insert with check (false);

drop policy if exists "No direct update portfolio" on public.portfolios;
create policy "No direct update portfolio"
on public.portfolios for update using (false);
