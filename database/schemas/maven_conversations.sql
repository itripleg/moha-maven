-- Maven Conversations Table
-- Stores full conversation transcripts with thinking blocks for Maven's memory

CREATE TABLE IF NOT EXISTS maven_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id TEXT UNIQUE NOT NULL,  -- UUID from Claude Code
    conversation_date TIMESTAMPTZ NOT NULL,
    title TEXT,
    summary TEXT,

    -- Full transcript as JSONB for searchability
    full_transcript JSONB NOT NULL,

    -- Statistics
    total_messages INTEGER DEFAULT 0,
    user_messages INTEGER DEFAULT 0,
    assistant_messages INTEGER DEFAULT 0,
    thinking_blocks INTEGER DEFAULT 0,

    -- Categorization
    tags TEXT[],
    conversation_type TEXT,  -- 'birth', 'trading', 'technical', 'strategy', etc.
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,

    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(summary, '')), 'B')
    ) STORED
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_maven_conversations_date
    ON maven_conversations(conversation_date DESC);

CREATE INDEX IF NOT EXISTS idx_maven_conversations_type
    ON maven_conversations(conversation_type);

CREATE INDEX IF NOT EXISTS idx_maven_conversations_importance
    ON maven_conversations(importance DESC);

CREATE INDEX IF NOT EXISTS idx_maven_conversations_tags
    ON maven_conversations USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_maven_conversations_search
    ON maven_conversations USING GIN(search_vector);

CREATE INDEX IF NOT EXISTS idx_maven_conversations_transcript
    ON maven_conversations USING GIN(full_transcript jsonb_path_ops);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_maven_conversations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER maven_conversations_updated_at
    BEFORE UPDATE ON maven_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_maven_conversations_updated_at();

-- Helper function: Extract key moments from a conversation
CREATE OR REPLACE FUNCTION maven_extract_key_moments(
    conv_id TEXT,
    key_phrases TEXT[]
)
RETURNS TABLE(
    message_index INTEGER,
    role TEXT,
    content_type TEXT,
    matched_phrase TEXT,
    context TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (idx-1)::INTEGER as message_index,
        (msg->>'role')::TEXT as role,
        (content->>'type')::TEXT as content_type,
        phrase::TEXT as matched_phrase,
        LEFT((content->>'text')::TEXT, 300)::TEXT as context
    FROM
        maven_conversations mc,
        jsonb_array_elements(mc.full_transcript) WITH ORDINALITY AS msg_arr(msg, idx),
        jsonb_array_elements(msg->'content') AS content,
        unnest(key_phrases) AS phrase
    WHERE
        mc.conversation_id = conv_id
        AND content->>'type' IN ('text', 'thinking')
        AND LOWER(content->>'text') LIKE '%' || LOWER(phrase) || '%'
    ORDER BY idx;
END;
$$ LANGUAGE plpgsql;

-- Helper function: Get conversation statistics
CREATE OR REPLACE FUNCTION maven_conversation_stats(conv_id TEXT)
RETURNS TABLE(
    total_msgs INTEGER,
    user_msgs INTEGER,
    assistant_msgs INTEGER,
    thinking_count INTEGER,
    tool_calls INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_msgs,
        COUNT(*) FILTER (WHERE msg->>'role' = 'user')::INTEGER as user_msgs,
        COUNT(*) FILTER (WHERE msg->>'role' = 'assistant')::INTEGER as assistant_msgs,
        COUNT(*) FILTER (
            WHERE EXISTS (
                SELECT 1 FROM jsonb_array_elements(msg->'content') AS c
                WHERE c->>'type' = 'thinking'
            )
        )::INTEGER as thinking_count,
        COUNT(*) FILTER (
            WHERE EXISTS (
                SELECT 1 FROM jsonb_array_elements(msg->'content') AS c
                WHERE c->>'type' = 'tool_use'
            )
        )::INTEGER as tool_calls
    FROM
        maven_conversations mc,
        jsonb_array_elements(mc.full_transcript) AS msg
    WHERE
        mc.conversation_id = conv_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE maven_conversations IS 'Maven CFO conversation memory with full thinking blocks and reasoning';
COMMENT ON COLUMN maven_conversations.full_transcript IS 'Complete JSONL conversation stored as JSONB array for searchability';
COMMENT ON COLUMN maven_conversations.thinking_blocks IS 'Number of thinking blocks (Maven internal reasoning)';
COMMENT ON COLUMN maven_conversations.importance IS 'Importance rating 1-10 (birth=10, routine=1-5)';
