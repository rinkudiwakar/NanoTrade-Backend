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
    status text check (status in ('NEW', 'QUEUED', 'PROCESSING', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED', 'FAILED')),
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
    buy_order_id uuid references public.orders(id),
    sell_order_id uuid references public.orders(id),
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

-- -----------------------------------------------------------------------------------------
-- ATOMIC TRADE SETTLEMENT RPC (Idempotent)
-- -----------------------------------------------------------------------------------------
create or replace function public.settle_trade_atomic(
    p_trade_id uuid,
    p_buyer_id uuid,
    p_seller_id uuid,
    p_price numeric,
    p_quantity numeric,
    p_buy_order_id uuid,
    p_sell_order_id uuid,
    p_is_bot_trade boolean,
    p_trade_timestamp timestamp
) returns void as $$
declare
    v_trade_value numeric := p_price * p_quantity;
    v_seller_qty numeric;
    v_inserted_id uuid;
begin
    -- 1. Insert trade (IDEMPOTENCY CHECK)
    -- If trade_id already exists, this will do nothing and v_inserted_id will be NULL
    insert into public.trades (id, buyer_id, seller_id, price, quantity, buy_order_id, sell_order_id, is_bot_trade, created_at)
    values (p_trade_id, p_buyer_id, p_seller_id, p_price, p_quantity, p_buy_order_id, p_sell_order_id, p_is_bot_trade, p_trade_timestamp)
    on conflict (id) do nothing
    returning id into v_inserted_id;

    -- If the trade already existed (idempotency triggered), exit the function to prevent double balance updates
    if v_inserted_id is null then
        return;
    end if;

    -- 2. Update buyer balance (deduct INR, add BTC)
    if p_buyer_id != '00000000-0000-0000-0000-000000000000' then
        update public.profiles set balance = balance - v_trade_value where id = p_buyer_id;
        
        insert into public.portfolios (user_id, asset, quantity, avg_price)
        values (p_buyer_id, 'BTC', p_quantity, p_price)
        on conflict (user_id, asset) do update set 
            avg_price = round(((public.portfolios.quantity * public.portfolios.avg_price) + v_trade_value) / (public.portfolios.quantity + p_quantity), 2),
            quantity = public.portfolios.quantity + p_quantity;
    end if;

    -- 3. Update seller balance (add INR, deduct BTC)
    if p_seller_id != '00000000-0000-0000-0000-000000000000' then
        update public.profiles set balance = balance + v_trade_value where id = p_seller_id;
        
        select quantity into v_seller_qty from public.portfolios where user_id = p_seller_id and asset = 'BTC';
        if v_seller_qty - p_quantity < 0.000001 then
            delete from public.portfolios where user_id = p_seller_id and asset = 'BTC';
        else
            update public.portfolios set quantity = quantity - p_quantity where user_id = p_seller_id and asset = 'BTC';
        end if;
    end if;

    -- Note: Order quantity/status updates are expected to be handled by the Python worker
    -- based on the final RemainingQuantity returned by the C++ engine to keep things simple.
end;
$$ language plpgsql security definer;
