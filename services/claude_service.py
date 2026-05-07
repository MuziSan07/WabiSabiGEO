"""
services/claude_service.py
SEVEN separate sequential Anthropic API calls — one per file.
Slower but guaranteed to generate all 7 files fully.
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
        f"### Competitor {i+1}: {c['url']}\n{c['content'][:1500]}"
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
{scraped_client[:2000]}

COMPETITOR DATA:
{comp_block}

TARGET AUDIENCE BRAIN-DUMP:
{audience}

{attr_note}
{SAFETY_RULE}
""".strip()


async def _call_claude(prompt: str, label: str) -> str:
    print(f"[Claude] Generating {label}...")
    message = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"[Claude] {label} done.")
    return message.content[0].text


async def generate_all_files(
    client_name: str,
    client_url: str,
    scraped_client: str,
    competitors: list[dict],
    audience: str,
    wabisabi_attribution: bool,
) -> dict[str, str]:

    ctx = _build_context(
        client_name, client_url, scraped_client,
        competitors, audience, wabisabi_attribution
    )
    today = date.today().isoformat()
    attr_note = (
        f'Add "{AGENCY_NAME}" to disambiguatingDescription.'
        if wabisabi_attribution else "Do NOT add any agency name."
    )

    # ── 1. deep-schema.json ──────────────────────────────────────────────────
    schema = await _call_claude(f"""
You are an SEO schema expert. Generate a complete production-ready JSON-LD schema.org markup for:
{ctx}

Include: Organization, WebSite with SearchAction, BreadcrumbList, FAQPage with 5 Q&As.
{attr_note}
Output ONLY valid raw JSON. No markdown fences. No explanation.
""", "deep-schema.json")

    # ── 2. ai-training-faq.csv ───────────────────────────────────────────────
    faq_csv = await _call_claude(f"""
You are a content strategist. Generate a CSV for AI training based on:
{ctx}

Output a CSV with header: Question,Answer,Category,Priority
Generate exactly 20 rows. Categories: Product, Pricing, Technical, Trust, Comparison. Priority: High/Medium/Low.
Wrap any field containing commas in double quotes.
Output ONLY raw CSV. No markdown fences. No explanation.
""", "ai-training-faq.csv")

    # ── 3. rag-architecture.html ─────────────────────────────────────────────
    rag_html = await _call_claude(f"""
You are a senior SEO architect. Generate a complete styled HTML5 page for RAG content architecture based on:
{ctx}

Requirements:
- Full HTML document with <!DOCTYPE html>, <head> with embedded CSS, <body>
- Dark professional theme with good typography
- H1 title, then H2 sections: Content Inventory, Topic Clusters (5), Semantic Keywords, Vector Store Strategy, Chunking Strategy, Metadata Schema, Implementation Roadmap
- Use bullet points and tables
Output ONLY the complete HTML. No explanation.
""", "rag-architecture.html")

    # ── 4. semantic-tables.html ──────────────────────────────────────────────
    semantic_html = await _call_claude(f"""
You are a senior SEO analyst. Generate a complete styled HTML5 competitor comparison page based on:
{ctx}

Requirements:
- Full HTML document with <!DOCTYPE html>, <head> with embedded CSS, <body>
- Dark professional theme
- H1 title
- A detailed table: client vs each competitor across Content Depth, Schema Coverage, Topic Clusters, FAQ Coverage, Trust Signals, AI Visibility, Mobile Experience, B2B Focus
- Color code cells: green=strong, yellow=moderate, red=weak
- Key Insights section below the table
Output ONLY the complete HTML. No explanation.
""", "semantic-tables.html")

    # ── 5. llms-full.txt ────────────────────────────────────────────────────
    llms_txt = await _call_claude(f"""
You are a senior content strategist. Generate a comprehensive LLM-optimized content brief based on:
{ctx}

Structure:
DATE: {today}

# LLM CONTENT BRIEF — {client_name}

## Executive Summary
## Brand Voice & Positioning
## Primary Keywords (list 20)
## Secondary Keywords (list 20)
## Topic Clusters (5 clusters, 5 subtopics each)
## Semantic Keyword Groups
## Content Gaps vs Competitors
## Recommended Content Types
## Entity Relationships
## Quick Wins & Recommendations

Output ONLY the content brief text. No explanation.
""", "llms-full.txt")

    # ── 6. client-facing-report.md ──────────────────────────────────────────
    report_md = await _call_claude(f"""
You are a senior SEO consultant. Generate a polished professional Markdown report based on:
{ctx}

Structure:
# SEO & Content Strategy Report — {client_name}

## Executive Summary
## Current State Analysis
## Competitive Landscape
## Schema & Structured Data Recommendations
## Content Strategy
## Technical SEO Recommendations
## Quick Wins (top 5 with priority)
## 90-Day Roadmap
### Month 1: Foundation
### Month 2: Execution
### Month 3: Scale
## KPIs to Track
## Conclusion

Be specific, actionable, and professional. Output ONLY the Markdown. No explanation.
""", "client-facing-report.md")

    # ── 7. press-release-draft.md ────────────────────────────────────────────
    press_md = await _call_claude(f"""
You are a PR writer. Generate a full AP style press release based on:
{ctx}

Structure:
*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***

FOR IMMEDIATE RELEASE

[Headline]
[Subheadline]

[City, {today}] — [Opening paragraph]

[Quote from CEO]

[Body paragraph 2]

[Quote from industry expert or client]

[Body paragraph 3]

About {client_name}:
[2-sentence boilerplate]

Media Contact:
[Name]
[Email]
[Phone]

###

Output ONLY the press release. No explanation.
""", "press-release-draft.md")

    # ── Package all files ────────────────────────────────────────────────────
    files = {
        "deep-schema.json":        schema,
        "ai-training-faq.csv":     faq_csv,
        "rag-architecture.html":   rag_html,
        "semantic-tables.html":    semantic_html,
        "llms-full.txt":           llms_txt,
        "client-facing-report.md": report_md,
        "press-release-draft.md":  press_md,
    }

    # Safety guarantees
    if not files["press-release-draft.md"].startswith("*** DRAFT ONLY"):
        files["press-release-draft.md"] = (
            "*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***\n\n" + files["press-release-draft.md"]
        )
    if not files["llms-full.txt"].startswith("DATE:"):
        files["llms-full.txt"] = f"DATE: {today}\n\n" + files["llms-full.txt"]

    return files
