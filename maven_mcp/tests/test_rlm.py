"""
Tests for Maven RLM (Recursive Language Model) Module.

Tests the core RLM functionality including context management,
chunking strategies, and processing pipelines.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

# Import the RLM module
from ..rlm import (
    RLMContext,
    llm_query,
    process_with_map_reduce,
    process_with_search_and_extract,
    process_iteratively,
    rlm_query,
    analyze_financial_documents,
    RLM_CONFIG
)


class TestRLMContext:
    """Tests for the RLMContext class."""

    def test_context_initialization(self):
        """Test that context is properly initialized."""
        text = "Hello world! " * 1000  # ~13000 chars
        ctx = RLMContext(context=text)

        assert ctx.context == text
        assert ctx.context_length == len(text)
        assert ctx.context_type == "string"
        assert ctx.chunks == []
        assert ctx.variables == {}
        assert ctx.sub_calls == []

    def test_get_chunk(self):
        """Test slicing context by position."""
        ctx = RLMContext(context="0123456789ABCDEF")

        assert ctx.get_chunk(0, 5) == "01234"
        assert ctx.get_chunk(10, 16) == "ABCDEF"
        assert ctx.get_chunk(0, 100) == "0123456789ABCDEF"

    def test_chunk_by_size(self):
        """Test chunking by fixed size."""
        ctx = RLMContext(context="A" * 100)
        chunks = ctx.chunk_by_size(30)

        assert len(chunks) == 4  # 30 + 30 + 30 + 10
        assert chunks[0] == "A" * 30
        assert chunks[3] == "A" * 10

    def test_chunk_by_delimiter(self):
        """Test chunking by delimiter."""
        ctx = RLMContext(context="Doc1\n\nDoc2\n\nDoc3")
        chunks = ctx.chunk_by_delimiter("\n\n")

        assert len(chunks) == 3
        assert chunks[0] == "Doc1"
        assert chunks[1] == "Doc2"
        assert chunks[2] == "Doc3"

    def test_chunk_by_regex(self):
        """Test chunking by regex pattern."""
        ctx = RLMContext(context="# Header 1\nContent 1\n# Header 2\nContent 2")
        chunks = ctx.chunk_by_regex(r"\n(?=#)")

        assert len(chunks) == 2
        assert "Header 1" in chunks[0]
        assert "Header 2" in chunks[1]

    def test_search(self):
        """Test searching within context."""
        ctx = RLMContext(context="The quick brown fox jumps over the lazy dog. Fox is smart.")
        results = ctx.search("fox", max_results=5)

        assert len(results) == 2
        assert results[0]["match"] == "fox"
        assert results[1]["match"].lower() == "fox"

    def test_get_stats(self):
        """Test getting context statistics."""
        ctx = RLMContext(context="Test content")
        ctx.chunk_by_size(5)
        ctx.sub_calls.append({"test": "call"})

        stats = ctx.get_stats()
        assert stats["context_length"] == 12
        assert stats["num_chunks"] == 3
        assert stats["num_sub_calls"] == 1


class TestLLMQuery:
    """Tests for the llm_query function."""

    @patch('maven_mcp.rlm.anthropic.Anthropic')
    def test_llm_query_basic(self, mock_anthropic):
        """Test basic llm_query functionality."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Test response")]
        mock_message.usage.input_tokens = 100
        mock_message.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_message

        # Test
        result = llm_query("Test prompt")

        assert result == "Test response"
        mock_client.messages.create.assert_called_once()

    @patch('maven_mcp.rlm.anthropic.Anthropic')
    def test_llm_query_with_context_tracking(self, mock_anthropic):
        """Test that llm_query tracks calls in RLM context."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_message.usage.input_tokens = 100
        mock_message.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_message

        # Test with context tracking
        rlm_ctx = RLMContext(context="test")
        result = llm_query("Prompt", context="Context chunk", rlm_context=rlm_ctx)

        assert len(rlm_ctx.sub_calls) == 1
        assert rlm_ctx.total_input_tokens == 100
        assert rlm_ctx.total_output_tokens == 50


class TestRLMStrategies:
    """Tests for RLM processing strategies."""

    @patch('maven_mcp.rlm.llm_query')
    def test_map_reduce_strategy(self, mock_llm_query):
        """Test map-reduce processing strategy."""
        mock_llm_query.return_value = "Chunk analysis result"

        ctx = RLMContext(context="A" * 500)  # 500 char context
        result = process_with_map_reduce(
            ctx,
            map_prompt="Analyze: {chunk}",
            reduce_prompt="Synthesize: {results}",
            chunk_size=100
        )

        assert result["success"] is True
        assert "final_answer" in result
        # Should have 5 map calls + 1 reduce call
        assert mock_llm_query.call_count == 6

    @patch('maven_mcp.rlm.llm_query')
    def test_search_extract_strategy(self, mock_llm_query):
        """Test search-and-extract processing strategy."""
        mock_llm_query.return_value = "Extracted info"

        ctx = RLMContext(context="The answer is 42. Also, 42 appears here.")
        result = process_with_search_and_extract(
            ctx,
            search_patterns=["42"],
            extraction_prompt="Extract: {context}",
            synthesis_prompt="Synthesize: {extractions}"
        )

        assert result["success"] is True
        assert result["num_matches"] >= 1

    @patch('maven_mcp.rlm.llm_query')
    def test_iterative_strategy(self, mock_llm_query):
        """Test iterative processing strategy."""
        mock_llm_query.return_value = "Accumulated understanding"

        ctx = RLMContext(context="A" * 300)
        result = process_iteratively(
            ctx,
            initial_prompt="Start: {chunk}",
            iteration_prompt="Continue with {buffer}: {chunk}",
            termination_check=lambda x: False,  # Never terminate early
            max_iterations=3,
            chunk_size=100
        )

        assert result["success"] is True
        assert result["iterations"] == 3


class TestHighLevelRLMQuery:
    """Tests for the high-level rlm_query function."""

    @patch('maven_mcp.rlm.process_with_map_reduce')
    def test_rlm_query_map_reduce(self, mock_map_reduce):
        """Test rlm_query with map_reduce strategy."""
        mock_map_reduce.return_value = {
            "success": True,
            "final_answer": "Analysis complete"
        }

        result = rlm_query(
            query="What is the main topic?",
            context="Long document content...",
            strategy="map_reduce"
        )

        assert result["success"] is True
        assert result["strategy"] == "map_reduce"
        mock_map_reduce.assert_called_once()

    def test_rlm_query_invalid_strategy(self):
        """Test rlm_query with invalid strategy."""
        result = rlm_query(
            query="Test",
            context="Content",
            strategy="invalid_strategy"
        )

        assert result["success"] is False
        assert "Unknown strategy" in result["error"]


class TestFinancialAnalysis:
    """Tests for Maven-specific financial analysis functions."""

    @patch('maven_mcp.rlm.rlm_query')
    def test_analyze_financial_documents(self, mock_rlm_query):
        """Test financial document analysis."""
        mock_rlm_query.return_value = {
            "success": True,
            "final_answer": "Financial analysis complete"
        }

        documents = [
            "Q1 Report: Revenue $1M",
            "Q2 Report: Revenue $1.2M",
            "Q3 Report: Revenue $1.5M"
        ]

        result = analyze_financial_documents(
            documents=documents,
            query="What is the revenue trend?"
        )

        assert result["success"] is True
        mock_rlm_query.assert_called_once()

        # Check that documents were combined
        call_args = mock_rlm_query.call_args
        combined_context = call_args[1]["context"]
        assert "Q1 Report" in combined_context
        assert "Q3 Report" in combined_context


class TestRLMConfig:
    """Tests for RLM configuration."""

    def test_default_config_values(self):
        """Test that default config values are sensible."""
        assert RLM_CONFIG["max_chunk_chars"] > 0
        assert RLM_CONFIG["max_depth"] >= 1
        assert RLM_CONFIG["max_sub_calls"] > 0
        assert RLM_CONFIG["timeout"] > 0


# Integration test (requires actual API key)
@pytest.mark.skip(reason="Requires API key - run manually")
class TestRLMIntegration:
    """Integration tests that make real API calls."""

    def test_real_llm_query(self):
        """Test actual API call to Claude."""
        result = llm_query("What is 2+2? Answer with just the number.")
        assert "4" in result

    def test_real_rlm_query_small(self):
        """Test RLM with a small context."""
        context = "The capital of France is Paris. The capital of Germany is Berlin."
        result = rlm_query(
            query="What is the capital of France?",
            context=context,
            strategy="search_extract",
            search_patterns=["France", "capital"]
        )
        assert result["success"] is True
        assert "Paris" in result["final_answer"]
