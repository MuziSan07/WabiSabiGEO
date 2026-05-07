"""
services/claude_service.py
THREE parallel Anthropic API calls using claude-sonnet-4-6
Call A → deep-schema.json + ai-training-faq.csv
Call B → rag-architecture.html + semantic-tables.html
Call C → llms-full.txt + client-facing-report.md + press-release-draft.md
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
        f"### Competitor {i+1}: {c['url']}\n{c['content'][:2000]}"
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
{scraped_client[:3000]}

COMPETITOR DATA:
{comp_block}

TARGET AUDIENCE BRAIN-DUMP:
{audience}

{attr_note}
{SAFETY_RULE}
""".strip()


# ── CALL A: Schema + FAQ ─────────────────────────────────────────────────────
PROMPT_A = """
You are a senior SEO architect. Given the context below, generate TWO files.
Return them inside XML tags exactly as shown. No explanation outside tags.

<deep_schema>
Generate complete production-ready JSON-LD schema.org markup. Include:
- Organization schema with full details (name, url, logo, sameAs, contactPoint, address)
- WebSite schema with SearchAction potentialAction
- BreadcrumbList with 3 items
- FAQPage with 5 detailed Q&As relevant to the target audience
- If attribution required, add agency to disambiguatingDescription
Output ONLY valid JSON, no markdown fences.
</deep_schema>

<ai_faq_csv>
Generate a CSV with header: Question,Answer,Category,Priority
Generate exactly 20 targeted Q&As based on the audience brain-dump.
Categories: Product, Pricing, Technical, Trust, Comparison
Priority: High, Medium, or Low
Wrap answers containing commas in double quotes.
Output ONLY raw CSV, no markdown fences.
</ai_faq_csv>
"""

# ── CALL B: HTML files ───────────────────────────────────────────────────────
PROMPT_B = """
You are a senior SEO architect. Given the context below, generate TWO files.
Return them inside XML tags exactly as shown. No explanation outside tags.

<rag_architecture>
Generate a complete styled HTML5 page (full document) for RAG content architecture. Include:
<!DOCTYPE html> with embedded CSS styling (dark professional theme)
H1 title, then H2 sections:
- Content Inventory & Gap Analysis
- Recommended Topic Clusters (5 clusters)
- Semantic Keyword Groups
- Vector Store & Chunking Strategy
- Metadata Schema Recommendations
- Implementation Roadmap
Use bullet points, tables where appropriate. Make it visually polished.
</rag_architecture>

<semantic_tables>
Generate a complete styled HTML5 page (full document) for competitor comparison. Include:
<!DOCTYPE html> with embedded CSS styling (dark professional theme)
H1 title, then:
- A detailed HTML table comparing client vs each competitor across:
  Content Depth, Schema Coverage, Topic Clusters, FAQ Coverage, Trust Signals,
  AI Visibility Score, Mobile Experience, B2B Focus
- Use colored cells (green=good, red=weak, yellow=moderate)
- A Key Insights section below the table
Make it visually polished and professional.
</semantic_tables>
"""

# ── CALL C: Text/Markdown files ──────────────────────────────────────────────
PROMPT_C = f"""
You are a senior content strategist and PR writer. Given the context below, generate THREE files.
Return them inside XML tags exactly as shown. No explanation outside tags.

<llms_full>
Generate a comprehensive LLM-optimized content brief:
DATE: {date.today().isoformat()}

# LLM CONTENT BRIEF — [CLIENT NAME]

## Executive Summary
## Brand Voice & Positioning
## Primary Keywords (20 keywords)
## Secondary Keywords (20 keywords)
## Topic Clusters (5 clusters with 5 subtopics each)
## Semantic Keyword Groups
## Content Gaps vs Competitors
## Recommended Content Types
## Entity Relationships
## Quick Wins & Recommendations
</llms_full>

<client_report>
Generate a polished professional Markdown report:

# SEO & Content Strategy Report — [CLIENT NAME]

## Executive Summary
## Current State Analysis
## Competitive Landscape
## Schema & Structured Data Recommendations
## Content Strategy
## Technical SEO Recommendations
## Quick Wins (top 5 prioritized)
## 90-Day Roadmap
### Month 1: Foundation
### Month 2: Execution
### Month 3: Scale
## KPIs to Track
## Conclusion
</client_report>

<press_release>
*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***

Generate a full AP style press release:
FOR IMMEDIATE RELEASE
[City, Date]

[Strong Headline]
[Subheadline]

[Opening paragraph - most newsworthy info]
[Quote from CEO/Founder]
[Body paragraph 2]
[Quote from client or industry expert]
[Body paragraph 3]
[Body paragraph 4]

About [Company]:
[2-sentence boilerplate]

Media Contact:
[Name placeholder]
[Email placeholder]
[Phone placeholder]

###
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
        max_tokens=6000,
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
    """Run THREE parallel Claude API calls and return a dict of filename → content."""
    context = _build_context(
        client_name, client_url, scraped_client, competitors, audience, wabisabi_attribution
    )

    # 3 parallel calls — each has fewer files so token limit never hit
    result_a, result_b, result_c = await asyncio.gather(
        _call_claude(PROMPT_A, context, "Call-A (schema + FAQ)"),
        _call_claude(PROMPT_B, context, "Call-B (HTML files)"),
        _call_claude(PROMPT_C, context, "Call-C (text/markdown files)"),
    )

    today = date.today().isoformat()

    files = {
        "deep-schema.json":        _extract_tag(result_a, "deep_schema"),
        "ai-training-faq.csv":     _extract_tag(result_a, "ai_faq_csv"),
        "rag-architecture.html":   _extract_tag(result_b, "rag_architecture"),
        "semantic-tables.html":    _extract_tag(result_b, "semantic_tables"),
        "llms-full.txt":           _extract_tag(result_c, "llms_full"),
        "client-facing-report.md": _extract_tag(result_c, "client_report"),
        "press-release-draft.md":  _extract_tag(result_c, "press_release"),
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
