"""
Maven RLM (Recursive Language Model) Module.

Implements the RLM paradigm from "Recursive Language Models" (Zhang et al., 2025)
allowing Maven to process arbitrarily long contexts by treating prompts as external
environment variables that can be programmatically examined, decomposed, and
recursively processed via sub-LLM calls.

Key Components:
1. Context Loading - Load large documents as REPL environment variables
2. llm_query() - Spawn sub-LLM calls over context chunks
3. Chunking Strategies - Smart decomposition of large contexts
4. Aggregation - Combine sub-call results into final answers

Reference: arXiv:2512.24601v1 [cs.AI] 31 Dec 2025
"""
import json
import logging
import os
import re
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

import anthropic

from .config import PATHS, get_iso_timestamp

logger = logging.getLogger(__name__)


# =============================================================================
# RLM Configuration
# =============================================================================

RLM_CONFIG = {
    # Sub-LM model for recursive calls (smaller/cheaper model)
    "sub_model": os.getenv("MAVEN_RLM_SUB_MODEL", "claude-sonnet-4-20250514"),
    # Root model for final synthesis
    "root_model": os.getenv("MAVEN_RLM_ROOT_MODEL", "claude-sonnet-4-20250514"),
    # Max tokens per sub-call context
    "max_chunk_chars": int(os.getenv("MAVEN_RLM_CHUNK_SIZE", "200000")),
    # Max recursive depth (paper uses depth=1, sub-calls are LMs not RLMs)
    "max_depth": int(os.getenv("MAVEN_RLM_MAX_DEPTH", "1")),
    # Max sub-calls per query (cost control)
    "max_sub_calls": int(os.getenv("MAVEN_RLM_MAX_CALLS", "50")),
    # Default timeout for sub-calls (seconds)
    "timeout": int(os.getenv("MAVEN_RLM_TIMEOUT", "60")),
}


# =============================================================================
# RLM Context Environment
# =============================================================================

@dataclass
class RLMContext:
    """
    Represents the REPL environment for an RLM session.

    The context variable holds the full input that would normally overflow
    the LLM's context window. The RLM can programmatically access slices
    of this context and spawn sub-LM calls over them.
    """
    # The full context string (can be millions of chars)
    context: str
    # Metadata about the context
    context_type: str = "string"
    context_length: int = 0
    # Chunked view of context (lazy computed)
    chunks: List[str] = field(default_factory=list)
    chunk_size: int = 0
    # Variables created during REPL execution
    variables: Dict[str, Any] = field(default_factory=dict)
    # Sub-call history for transparency
    sub_calls: List[Dict[str, Any]] = field(default_factory=list)
    # Cost tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def __post_init__(self):
        self.context_length = len(self.context)

    def get_chunk(self, start: int, end: int) -> str:
        """Get a slice of the context."""
        return self.context[start:end]

    def chunk_by_size(self, chunk_size: int) -> List[str]:
        """Chunk context into fixed-size pieces."""
        if not self.chunks or self.chunk_size != chunk_size:
            self.chunk_size = chunk_size
            self.chunks = [
                self.context[i:i+chunk_size]
                for i in range(0, len(self.context), chunk_size)
            ]
        return self.chunks

    def chunk_by_delimiter(self, delimiter: str = "\n\n") -> List[str]:
        """Chunk context by a delimiter (e.g., paragraphs, documents)."""
        return self.context.split(delimiter)

    def chunk_by_regex(self, pattern: str) -> List[str]:
        """Chunk context using a regex pattern (e.g., markdown headers)."""
        return re.split(pattern, self.context)

    def search(self, pattern: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search context for a pattern, return matches with positions."""
        results = []
        for match in re.finditer(pattern, self.context, re.IGNORECASE):
            if len(results) >= max_results:
                break
            # Get surrounding context (window of 500 chars)
            start = max(0, match.start() - 250)
            end = min(len(self.context), match.end() + 250)
            results.append({
                "match": match.group(),
                "start": match.start(),
                "end": match.end(),
                "context": self.context[start:end]
            })
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the context and processing."""
        return {
            "context_length": self.context_length,
            "context_type": self.context_type,
            "num_chunks": len(self.chunks) if self.chunks else "not chunked",
            "chunk_size": self.chunk_size,
            "num_sub_calls": len(self.sub_calls),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "variables": list(self.variables.keys())
        }


# =============================================================================
# Sub-LM Query Function
# =============================================================================

def llm_query(
    prompt: str,
    context: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    rlm_context: Optional[RLMContext] = None
) -> str:
    """
    Query a sub-LM with a prompt and optional context chunk.

    This is the core function that enables recursive processing. The sub-LM
    can process a chunk of the original context and return structured findings.

    Args:
        prompt: The query/instruction for the sub-LM
        context: Optional context chunk to include (if not part of prompt)
        model: Model to use (defaults to RLM_CONFIG["sub_model"])
        max_tokens: Max output tokens
        temperature: Sampling temperature
        rlm_context: Optional RLMContext for tracking

    Returns:
        The sub-LM's response text
    """
    try:
        client = anthropic.Anthropic()
        model = model or RLM_CONFIG["sub_model"]

        # Build the full message
        full_prompt = prompt
        if context:
            full_prompt = f"{prompt}\n\n---\nCONTEXT:\n{context}\n---"

        # Make the API call
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": full_prompt}]
        )

        response_text = message.content[0].text

        # Track in RLM context if provided
        if rlm_context:
            rlm_context.sub_calls.append({
                "timestamp": get_iso_timestamp(),
                "model": model,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "context_chars": len(context) if context else 0,
                "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            })
            rlm_context.total_input_tokens += message.usage.input_tokens
            rlm_context.total_output_tokens += message.usage.output_tokens

        return response_text

    except Exception as e:
        logger.error(f"llm_query failed: {e}")
        return f"ERROR: {str(e)}"


# =============================================================================
# RLM Processing Strategies
# =============================================================================

def process_with_map_reduce(
    rlm_context: RLMContext,
    map_prompt: str,
    reduce_prompt: str,
    chunk_size: int = 200000
) -> Dict[str, Any]:
    """
    Process a large context using map-reduce pattern.

    1. MAP: Apply map_prompt to each chunk independently
    2. REDUCE: Aggregate results with reduce_prompt

    Args:
        rlm_context: The RLM context with the full document
        map_prompt: Prompt to apply to each chunk (use {chunk} placeholder)
        reduce_prompt: Prompt to aggregate results (use {results} placeholder)
        chunk_size: Size of each chunk in characters

    Returns:
        Dict with final answer, chunk results, and statistics
    """
    chunks = rlm_context.chunk_by_size(chunk_size)
    chunk_results = []

    # MAP phase: Process each chunk
    for i, chunk in enumerate(chunks):
        if len(rlm_context.sub_calls) >= RLM_CONFIG["max_sub_calls"]:
            logger.warning(f"Hit max sub-calls limit ({RLM_CONFIG['max_sub_calls']})")
            break

        prompt = map_prompt.format(
            chunk=chunk,
            chunk_num=i+1,
            total_chunks=len(chunks)
        )
        result = llm_query(prompt, rlm_context=rlm_context)
        chunk_results.append({
            "chunk_num": i+1,
            "chunk_start": i * chunk_size,
            "chunk_end": min((i+1) * chunk_size, rlm_context.context_length),
            "result": result
        })
        logger.info(f"Processed chunk {i+1}/{len(chunks)}")

    # REDUCE phase: Aggregate results
    results_text = "\n\n".join([
        f"=== Chunk {r['chunk_num']} ===\n{r['result']}"
        for r in chunk_results
    ])
    final_prompt = reduce_prompt.format(
        results=results_text,
        num_chunks=len(chunk_results)
    )
    final_answer = llm_query(final_prompt, rlm_context=rlm_context)

    return {
        "success": True,
        "final_answer": final_answer,
        "chunk_results": chunk_results,
        "stats": rlm_context.get_stats()
    }


def process_with_search_and_extract(
    rlm_context: RLMContext,
    search_patterns: List[str],
    extraction_prompt: str,
    synthesis_prompt: str
) -> Dict[str, Any]:
    """
    Process context by searching for relevant sections, then extracting.

    Useful for needle-in-haystack type tasks where most of the context
    is irrelevant.

    Args:
        rlm_context: The RLM context
        search_patterns: Regex patterns to find relevant sections
        extraction_prompt: Prompt to extract info from found sections
        synthesis_prompt: Prompt to synthesize extracted info

    Returns:
        Dict with final answer and extraction details
    """
    # Search phase
    all_matches = []
    for pattern in search_patterns:
        matches = rlm_context.search(pattern)
        all_matches.extend(matches)

    if not all_matches:
        return {
            "success": False,
            "error": "No matching sections found",
            "patterns_tried": search_patterns
        }

    # Deduplicate overlapping matches
    seen_ranges = set()
    unique_matches = []
    for match in all_matches:
        range_key = (match["start"] // 1000, match["end"] // 1000)
        if range_key not in seen_ranges:
            seen_ranges.add(range_key)
            unique_matches.append(match)

    # Extract from each match
    extractions = []
    for match in unique_matches[:RLM_CONFIG["max_sub_calls"]]:
        prompt = extraction_prompt.format(
            context=match["context"],
            match=match["match"]
        )
        extraction = llm_query(prompt, rlm_context=rlm_context)
        extractions.append({
            "match": match["match"],
            "position": match["start"],
            "extraction": extraction
        })

    # Synthesize
    extractions_text = "\n\n".join([
        f"--- Match: {e['match']} (position {e['position']}) ---\n{e['extraction']}"
        for e in extractions
    ])
    synthesis = llm_query(
        synthesis_prompt.format(extractions=extractions_text),
        rlm_context=rlm_context
    )

    return {
        "success": True,
        "final_answer": synthesis,
        "extractions": extractions,
        "num_matches": len(all_matches),
        "num_processed": len(extractions),
        "stats": rlm_context.get_stats()
    }


def process_iteratively(
    rlm_context: RLMContext,
    initial_prompt: str,
    iteration_prompt: str,
    termination_check: Callable[[str], bool],
    max_iterations: int = 10,
    chunk_size: int = 200000
) -> Dict[str, Any]:
    """
    Process context iteratively, building up understanding chunk by chunk.

    Good for tasks where later chunks might reference earlier ones, or
    where understanding accumulates.

    Args:
        rlm_context: The RLM context
        initial_prompt: First chunk prompt
        iteration_prompt: Subsequent chunk prompt (use {buffer}, {chunk})
        termination_check: Function to check if we can stop early
        max_iterations: Max chunks to process
        chunk_size: Size per chunk

    Returns:
        Dict with final answer and iteration history
    """
    chunks = rlm_context.chunk_by_size(chunk_size)
    buffer = ""
    history = []

    for i, chunk in enumerate(chunks[:max_iterations]):
        if i == 0:
            prompt = initial_prompt.format(chunk=chunk)
        else:
            prompt = iteration_prompt.format(
                buffer=buffer,
                chunk=chunk,
                chunk_num=i+1,
                total_chunks=len(chunks)
            )

        result = llm_query(prompt, rlm_context=rlm_context)
        buffer = result  # Update running buffer

        history.append({
            "iteration": i+1,
            "chunk_preview": chunk[:100] + "...",
            "result_preview": result[:200] + "..."
        })

        # Check if we can terminate early
        if termination_check(result):
            logger.info(f"Early termination at iteration {i+1}")
            break

    return {
        "success": True,
        "final_answer": buffer,
        "iterations": len(history),
        "history": history,
        "stats": rlm_context.get_stats()
    }


# =============================================================================
# High-Level RLM Query Function
# =============================================================================

def rlm_query(
    query: str,
    context: str,
    strategy: str = "map_reduce",
    **kwargs
) -> Dict[str, Any]:
    """
    High-level RLM query function that handles the full pipeline.

    This is the main entry point for using RLM capabilities. It:
    1. Creates an RLM context
    2. Selects the appropriate processing strategy
    3. Executes the strategy
    4. Returns structured results

    Args:
        query: The question/task to answer using the context
        context: The (potentially very long) context to process
        strategy: Processing strategy - "map_reduce", "search_extract", "iterative", "smart"
        **kwargs: Strategy-specific parameters

    Returns:
        Dict with answer, statistics, and processing details
    """
    timestamp = get_iso_timestamp()

    # Create RLM context
    rlm_ctx = RLMContext(
        context=context,
        context_type=kwargs.get("context_type", "document")
    )

    logger.info(f"RLM query starting: {len(context)} chars, strategy={strategy}")

    try:
        if strategy == "map_reduce":
            # Default prompts for map-reduce
            map_prompt = kwargs.get("map_prompt",
                f"You are processing chunk {{chunk_num}}/{{total_chunks}} of a large document.\n\n"
                f"Original query: {query}\n\n"
                f"Extract all information relevant to the query from this chunk:\n\n{{chunk}}"
            )
            reduce_prompt = kwargs.get("reduce_prompt",
                f"You processed a large document in chunks. Here are the findings from each chunk:\n\n"
                f"{{results}}\n\n"
                f"Original query: {query}\n\n"
                f"Synthesize these findings into a final comprehensive answer:"
            )
            result = process_with_map_reduce(
                rlm_ctx,
                map_prompt,
                reduce_prompt,
                chunk_size=kwargs.get("chunk_size", RLM_CONFIG["max_chunk_chars"])
            )

        elif strategy == "search_extract":
            patterns = kwargs.get("search_patterns", [query.split()[0]])
            extraction_prompt = kwargs.get("extraction_prompt",
                f"Extract information relevant to: {query}\n\nFrom this section:\n{{context}}"
            )
            synthesis_prompt = kwargs.get("synthesis_prompt",
                f"Based on these extractions, answer: {query}\n\n{{extractions}}"
            )
            result = process_with_search_and_extract(
                rlm_ctx,
                patterns,
                extraction_prompt,
                synthesis_prompt
            )

        elif strategy == "iterative":
            initial_prompt = kwargs.get("initial_prompt",
                f"Starting to analyze a document for: {query}\n\nFirst section:\n{{chunk}}\n\n"
                f"Summarize relevant findings:"
            )
            iteration_prompt = kwargs.get("iteration_prompt",
                f"Previous findings:\n{{buffer}}\n\n"
                f"New section ({{chunk_num}}/{{total_chunks}}):\n{{chunk}}\n\n"
                f"Update your findings for: {query}"
            )
            def default_termination(result: str) -> bool:
                return "ANSWER_FOUND" in result or "FINAL_ANSWER" in result

            result = process_iteratively(
                rlm_ctx,
                initial_prompt,
                iteration_prompt,
                kwargs.get("termination_check", default_termination),
                max_iterations=kwargs.get("max_iterations", 10),
                chunk_size=kwargs.get("chunk_size", RLM_CONFIG["max_chunk_chars"])
            )

        elif strategy == "smart":
            # Smart strategy: analyze context first, then choose best approach
            # Sample beginning, middle, end to understand structure
            sample_size = min(5000, len(context) // 10)
            samples = [
                context[:sample_size],
                context[len(context)//2 - sample_size//2:len(context)//2 + sample_size//2],
                context[-sample_size:]
            ]

            analysis_prompt = f"""Analyze this document structure to determine the best processing strategy.

Query: {query}

Document samples (beginning, middle, end):
{samples[0]}
---
{samples[1]}
---
{samples[2]}

Based on the document structure and query, which strategy is best?
1. MAP_REDUCE - for aggregation tasks that need to process everything
2. SEARCH_EXTRACT - for finding specific information (needle in haystack)
3. ITERATIVE - for tasks where understanding builds cumulatively

Respond with just the strategy name and a brief reason."""

            strategy_choice = llm_query(analysis_prompt, rlm_context=rlm_ctx)

            # Parse and execute chosen strategy
            if "SEARCH" in strategy_choice.upper():
                result = rlm_query(query, context, strategy="search_extract", **kwargs)
            elif "ITERATIVE" in strategy_choice.upper():
                result = rlm_query(query, context, strategy="iterative", **kwargs)
            else:
                result = rlm_query(query, context, strategy="map_reduce", **kwargs)

            result["auto_strategy"] = strategy_choice

        else:
            result = {
                "success": False,
                "error": f"Unknown strategy: {strategy}. Use: map_reduce, search_extract, iterative, smart"
            }

        # Add metadata
        result["query"] = query
        result["context_length"] = len(context)
        result["strategy"] = strategy
        result["timestamp"] = timestamp

        return result

    except Exception as e:
        logger.error(f"RLM query failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "context_length": len(context),
            "strategy": strategy,
            "timestamp": timestamp
        }


# =============================================================================
# Financial Analysis Helpers (Maven-specific)
# =============================================================================

def analyze_financial_documents(
    documents: List[str],
    query: str,
    document_separator: str = "\n\n---DOCUMENT---\n\n"
) -> Dict[str, Any]:
    """
    Analyze multiple financial documents using RLM.

    Optimized for Maven's financial analysis tasks.

    Args:
        documents: List of document contents
        query: Financial analysis query
        document_separator: Separator between documents

    Returns:
        Analysis results
    """
    # Combine documents
    full_context = document_separator.join(documents)

    # Financial-specific prompts
    map_prompt = """You are Maven, an AI CFO analyzing financial documents.

Document {chunk_num}/{total_chunks}

Query: """ + query + """

Extract:
1. Key financial metrics and numbers
2. Risk factors mentioned
3. Opportunities identified
4. Any red flags or concerns

Document content:
{chunk}

Structured findings:"""

    reduce_prompt = """You are Maven, synthesizing financial analysis from multiple documents.

Findings from {num_chunks} documents:
{results}

Original query: """ + query + """

Provide a comprehensive financial analysis that:
1. Summarizes key findings
2. Identifies patterns across documents
3. Highlights risks and opportunities
4. Gives a confident recommendation

FINAL ANALYSIS:"""

    return rlm_query(
        query=query,
        context=full_context,
        strategy="map_reduce",
        map_prompt=map_prompt,
        reduce_prompt=reduce_prompt,
        chunk_size=150000  # Slightly smaller for financial docs
    )


def search_financial_data(
    data: str,
    search_terms: List[str],
    extraction_query: str
) -> Dict[str, Any]:
    """
    Search through large financial datasets for specific information.

    Args:
        data: Large financial dataset (CSV, JSON, etc.)
        search_terms: Terms to search for
        extraction_query: What to extract from found sections

    Returns:
        Search and extraction results
    """
    return rlm_query(
        query=extraction_query,
        context=data,
        strategy="search_extract",
        search_patterns=search_terms,
        extraction_prompt=f"""Extract financial data for: {extraction_query}

From this data section:
{{context}}

Return structured JSON with relevant numbers and metrics.""",
        synthesis_prompt=f"""Synthesize financial findings for: {extraction_query}

Extracted data:
{{extractions}}

Provide a clear summary with key numbers and insights."""
    )
