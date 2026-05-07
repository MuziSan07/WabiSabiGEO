"""
services/claude_service.py
Two PARALLEL Anthropic API calls using claude-sonnet-4-6
Call A → code/data files: deep-schema.json, rag-architecture.html, semantic-tables.html, ai-training-faq.csv
Call B → text/markdown files: llms-full.txt, client-facing-report.md, press-release-draft.md
"""
import asyncio
from datetime import date
import anthropic
import os
from config import AGENCY_NAME, ANTHROPIC_API_KEY

CLAUDE_MODEL = "claude-sonnet-4-6"

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SAFETY_RULE = (
    "SAFETY RULE: If the client site is empty or missing information and you must invent "
    "a technical fact to fill a gap, wrap that invented fact in [CLIENT VERIFICATION REQUIRED]. "
    "Never silently hallucinate facts."
)


def _build_context(
    client_name: str,
    client_url: str,
    scraped_client: str,
    competitors: list[dict],
    audience: str,
    wabisabi_attribution: bool,
) -> str:
    comp_block = "\n\n".join(
        f"### Competitor {i+1}: {c['url']}\n{c['content'][:3000]}"
        for i, c in enumerate(competitors)
    )
    attr_note = (
        f'ATTRIBUTION: Add "{AGENCY_NAME}" strictly into the "disambiguatingDescription" '
        f'property of the JSON-LD schema.'
        if wabisabi_attribution
        else "ATTRIBUTION: Do NOT add any agency name."
    )
    return f"""
CLIENT: {client_name}
CLIENT URL: {client_url}
CLIENT SITE CONTENT:
{scraped_client[:4000]}

COMPETITOR DATA:
{comp_block}

TARGET AUDIENCE BRAIN-DUMP:
{audience}

{attr_note}
{SAFETY_RULE}
""".strip()


# ── CALL A: Code / Data files ────────────────────────────────────────────────
PROMPT_A = """
You are a senior SEO architect and structured data expert. Given the context below, generate FOUR files.
Return them inside XML tags exactly as shown. Do not add ANY explanation outside the tags.

<deep_schema>
Generate a complete, production-ready JSON-LD schema.org markup. Include:
- Organization schema with full details
- WebSite schema with SearchAction
- BreadcrumbList schema
- FAQPage schema with at least 5 real Q&As
- If attribution required, add agency to disambiguatingDescription
Output ONLY valid JSON, no markdown fences.
</deep_schema>

<rag_architecture>
Generate a complete HTML5 page (full document with <!DOCTYPE html>) covering RAG content architecture recommendations for the client. Include:
- Professional styling with CSS
- H2 sections: Content Inventory, Topic Clusters, Semantic Gaps, Vector Store Recommendations, Chunking Strategy, Metadata Schema
- Bullet points and tables where appropriate
</rag_architecture>

<semantic_tables>
Generate a complete HTML5 page (full document with <!DOCTYPE html>) with a semantic competitor comparison. Include:
- Professional styling with CSS
- A detailed table comparing client vs each competitor across: Content Depth, Schema Coverage, Topic Clusters, FAQ Coverage, Trust Signals, Page Speed Indicators, Backlink Profile, AI Visibility Score
- A summary insights section below the table
</semantic_tables>

<ai_faq_csv>
Generate a CSV with columns: Question,Answer,Category,Priority
Generate exactly 20 targeted Q&As based on the audience brain-dump.
Categories should be: Product, Pricing, Technical, Trust, Comparison
Priority should be: High, Medium, or Low
Output ONLY the CSV content, no markdown fences.
</ai_faq_csv>
"""

# ── CALL B: Text / Markdown files ────────────────────────────────────────────
PROMPT_B = f"""
You are a senior content strategist and PR writer. Given the context below, generate THREE files.
Return them inside XML tags exactly as shown. Do not add ANY explanation outside the tags.

<llms_full>
Generate a comprehensive LLM-optimized content brief. Structure:
DATE: {date.today().isoformat()}

# LLM CONTENT BRIEF — [CLIENT NAME]

## Executive Summary
## Brand Voice & Positioning
## Primary Keywords (20+)
## Secondary Keywords (20+)
## Topic Clusters (5 clusters with subtopics)
## Semantic Keyword Groups
## Content Gaps vs Competitors
## Recommended Content Types
## AI Training Notes
## Entity Relationships
## Recommendations & Quick Wins
</llms_full>

<client_report>
Generate a polished, professional Markdown report. Structure:

# SEO & Content Strategy Report — [CLIENT NAME]

Include these sections with real analysis:
## Executive Summary
## Current State Analysis
## Competitive Landscape
## Schema & Structured Data Recommendations
## Content Strategy
## Technical SEO Recommendations
## Quick Wins (prioritized list)
## 90-Day Roadmap (Month 1, Month 2, Month 3)
## KPIs to Track
## Investment Summary

Use professional tone. Be specific and actionable.
</client_report>

<press_release>
*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***

Generate a full press release in standard AP style. Include:
- FOR IMMEDIATE RELEASE header
- City, Date dateline
- Strong headline and subheadline
- 4-5 paragraphs with quotes
- Boilerplate about the company
- Contact information placeholder
- ### END ###
</press_release>
"""


def _extract_tag(xml: str, tag: str) -> str:
    import re
    pattern = rf"<{tag}>(.*?)</{tag}>"
    m = re.search(pattern, xml, re.DOTALL)
    if m:
        content = m.group(1).strip()
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
        return content
    return f"[Generation failed for {tag}]"


async def _call_claude(system_prompt: str, context: str, label: str) -> str:
    print(f"[Claude] Starting {label} call...")
    message = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": context}],
    )
    print(f"[Claude] {label} call complete.")
    return message.content[0].text


async def generate_all_files(
    client_name: str,
    client_url: str,
    scraped_client: str,
    competitors: list[dict],
    audience: str,
    wabisabi_attribution: bool,
) -> dict[str, str]:
    """Run two PARALLEL Claude API calls and return a dict of filename → content."""
    context = _build_context(
        client_name, client_url, scraped_client, competitors, audience, wabisabi_attribution
    )

    # Parallel execution — Claude can handle it unlike Groq
    result_a, result_b = await asyncio.gather(
        _call_claude(PROMPT_A, context, "Call-A (code/data files)"),
        _call_claude(PROMPT_B, context, "Call-B (text/markdown files)"),
    )

    today = date.today().isoformat()

    files = {
        "deep-schema.json":        _extract_tag(result_a, "deep_schema"),
        "rag-architecture.html":   _extract_tag(result_a, "rag_architecture"),
        "semantic-tables.html":    _extract_tag(result_a, "semantic_tables"),
        "ai-training-faq.csv":     _extract_tag(result_a, "ai_faq_csv"),
        "llms-full.txt":           _extract_tag(result_b, "llms_full"),
        "client-facing-report.md": _extract_tag(result_b, "client_report"),
        "press-release-draft.md":  _extract_tag(result_b, "press_release"),
    }

    # Guarantee press release DRAFT warning
    if not files["press-release-draft.md"].startswith("*** DRAFT ONLY"):
        files["press-release-draft.md"] = (
            "*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***\n\n" + files["press-release-draft.md"]
        )

    # Guarantee llms-full.txt has date
    if not files["llms-full.txt"].startswith("DATE:"):
        files["llms-full.txt"] = f"DATE: {today}\n\n" + files["llms-full.txt"]

    return files
