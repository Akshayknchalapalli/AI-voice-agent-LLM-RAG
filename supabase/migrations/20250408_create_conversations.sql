-- Create conversations table
create table conversations (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references auth.users(id) on delete cascade,
    transcript text not null,
    ai_response text not null,
    audio_url text,  -- URL to stored audio file if we want to save audio
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table conversations enable row level security;

-- Create policy to allow users to view their own conversations
create policy "Users can view their own conversations"
    on conversations for select
    using (auth.uid() = user_id or user_id is null);

-- Create policy to allow users to insert conversations
create policy "Users can insert conversations"
    on conversations for insert
    with check (
        -- Allow authenticated users to insert their own conversations
        (auth.uid() = user_id) or
        -- Allow anonymous conversations (user_id is null)
        (user_id is null)
    );

-- Create index for faster querying
create index conversations_user_id_created_at_idx on conversations(user_id, created_at desc);
