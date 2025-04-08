-- Create profiles table
create table if not exists public.profiles (
    id uuid primary key,
    email varchar(255) not null,
    full_name varchar(255),
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Enable RLS
alter table public.profiles enable row level security;

-- Create policies
create policy "Public profiles are viewable by everyone."
    on public.profiles for select
    using ( true );

create policy "Users can insert their own profile."
    on public.profiles for insert
    with check ( auth.uid() = id );

create policy "Users can update own profile."
    on public.profiles for update
    using ( auth.uid() = id );

-- Grant permissions
grant usage on schema public to authenticated;
grant usage on schema public to service_role;
grant usage on schema public to anon;

grant all on public.profiles to service_role;
grant select on public.profiles to authenticated;
grant select on public.profiles to anon;
grant insert on public.profiles to authenticated;
grant update on public.profiles to authenticated;
