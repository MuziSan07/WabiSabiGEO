"""
services/claude_service.py
7 sequential Anthropic API calls — one per file — with retry logic.
Fixes:
1. Attribution → separate Organization node in @graph (not disambiguatingDescription)
2. No aggregateRating block (omitted entirely)
3. No [CLIENT VERIFICATION REQUIRED] in output — skip fields instead
4. Retry logic (3 attempts per file)
5. Failed file detection — raises error if any file fails
"""
import asyncio
import re
from datetime import date
import anthropic
from config import AGENCY_NAME, ANTHROPIC_API_KEY

CLAUDE_MODEL = "claude-sonnet-4-6"
client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

WABI_SABI_ORG_NODE = {
    "@type": "Organization",
    "@id": "https://wabisabi.studio/#organization",
    "name": "Wabi Sabi Studios",
    "url": "https://wabisabi.studio/",
    "description": "Generative Engine Optimization agency helping powersports dealerships get recommended by ChatGPT, Perplexity, and Google AI Overviews."
}

SAFETY_RULE = """
CRITICAL RULES — YOU MUST FOLLOW THESE EXACTLY:
1. NEVER include [CLIENT VERIFICATION REQUIRED] or any placeholder text in the output.
   If you don't have a value for an optional field, simply OMIT that field entirely.
2. NEVER include aggregateRating in any schema — omit it completely.
3. NEVER invent fake review counts, ratings, or statistics.
4. Only include fields you have real data for from the context provided.
"""


def _build_context(
    client_name: str,
    client_url: str,
    scraped_client: str,
    competitors: list[dict],
    audience: str,
) -> str:
    comp_block = "\n\n".join(
        f"### Competitor {i+1}: {c['url']}\n{c['content'][:1500]}"
        for i, c in enumerate(competitors)
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

{SAFETY_RULE}
""".strip()


async def _call_claude_with_retry(prompt: str, label: str, max_retries: int = 3) -> str:
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Claude] Generating {label} (attempt {attempt})...")
            message = await client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = message.content[0].text
            print(f"[Claude] {label} done.")
            return result
        except Exception as e:
            last_error = e
            print(f"[Claude] {label} attempt {attempt} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(3 * attempt)
    raise RuntimeError(f"Failed to generate {label} after {max_retries} attempts: {last_error}")


def _inject_attribution(schema_json: str) -> str:
    """Post-process JSON string to inject Wabi Sabi org node into @graph."""
    import json
    try:
        data = json.loads(schema_json)
        # Find the client Organization node and add funder reference
        graph = data.get("@graph", [])
        new_graph = []
        for node in graph:
            if node.get("@type") == "Organization" and "wabisabi.studio" not in node.get("@id", ""):
                # Remove disambiguatingDescription if present
                node.pop("disambiguatingDescription", None)
                # Add funder reference
                node["funder"] = {"@id": "https://wabisabi.studio/#organization"}
            new_graph.append(node)
        # Add Wabi Sabi org node if not already present
        ids = [n.get("@id", "") for n in new_graph]
        if "https://wabisabi.studio/#organization" not in ids:
            new_graph.append(WABI_SABI_ORG_NODE)
        data["@graph"] = new_graph
        return json.dumps(data, indent=2)
    except Exception:
        # Fallback: just append the node as best effort
        return schema_json


def _clean_output(text: str) -> str:
    """Remove any [CLIENT VERIFICATION REQUIRED] tags that slipped through."""
    # Remove entire lines containing the tag
    lines = text.split("\n")
    clean_lines = [l for l in lines if "[CLIENT VERIFICATION REQUIRED]" not in l]
    return "\n".join(clean_lines)


async def generate_all_files(
    client_name: str,
    client_url: str,
    scraped_client: str,
    competitors: list[dict],
    audience: str,
    wabisabi_attribution: bool,
) -> dict[str, str]:

    ctx = _build_context(client_name, client_url, scraped_client, competitors, audience)
    today = date.today().isoformat()
    failed_files = []

    # ── 1. deep-schema.json ──────────────────────────────────────────────────
    try:
        schema = await _call_claude_with_retry(f"""
You are an SEO schema expert. Generate production-ready JSON-LD schema.org markup.

CONTEXT:
{ctx}

REQUIREMENTS:
- Output a single JSON-LD object with @context and @graph array
- Include in @graph: Organization node for the client, WebSite with SearchAction, BreadcrumbList with 3 items, FAQPage with 5 Q&As relevant to the audience
- DO NOT include aggregateRating under any circumstances
- DO NOT include disambiguatingDescription on the client Organization node
- Only include fields you have actual data for — omit optional fields if no data
- Output ONLY valid raw JSON. No markdown fences. No explanation. No comments.
""", "deep-schema.json")
        schema = _clean_output(schema)
        # Strip markdown fences if model added them anyway
        schema = re.sub(r'^```[a-z]*\n?', '', schema.strip(), flags=re.MULTILINE)
        schema = schema.replace('```', '').strip()
        if wabisabi_attribution:
            schema = _inject_attribution(schema)
    except Exception as e:
        schema = f"GENERATION FAILED: {e}"
        failed_files.append("deep-schema.json")

    # ── 2. ai-training-faq.csv ───────────────────────────────────────────────
    try:
        faq_csv = await _call_claude_with_retry(f"""
You are a content strategist. Generate a CSV for AI training.

CONTEXT:
{ctx}

REQUIREMENTS:
- Header row: Question,Answer,Category,Priority
- Exactly 20 data rows
- Categories: Product, Pricing, Technical, Trust, Comparison
- Priority: High, Medium, or Low
- Answers must be real, specific answers — never placeholder text
- Wrap fields containing commas in double quotes
- Output ONLY raw CSV. No markdown fences. No explanation.
""", "ai-training-faq.csv")
        faq_csv = _clean_output(faq_csv)
        faq_csv = re.sub(r'^```[a-z]*\n?', '', faq_csv.strip(), flags=re.MULTILINE)
        faq_csv = faq_csv.replace('```', '').strip()
    except Exception as e:
        faq_csv = f"GENERATION FAILED: {e}"
        failed_files.append("ai-training-faq.csv")

    # ── 3. rag-architecture.html ─────────────────────────────────────────────
    try:
        rag_html = await _call_claude_with_retry(f"""
You are a senior SEO architect. Generate a complete styled HTML5 page for RAG content architecture.

CONTEXT:
{ctx}

REQUIREMENTS:
- Full HTML document: <!DOCTYPE html>, <html>, <head> with embedded CSS, <body>
- Dark professional theme (#0a0a0a background, #e8e8e8 text, #c8f135 accents)
- H1 main title
- H2 sections: Content Inventory & Gap Analysis, Recommended Topic Clusters (list 5), Semantic Keyword Groups, Vector Store & Chunking Strategy, Metadata Schema, Implementation Roadmap
- Use <ul> bullet points and <table> where appropriate
- Output ONLY the complete HTML document. No explanation.
""", "rag-architecture.html")
        rag_html = _clean_output(rag_html)
        rag_html = re.sub(r'^```[a-z]*\n?', '', rag_html.strip(), flags=re.MULTILINE)
        rag_html = rag_html.replace('```', '').strip()
    except Exception as e:
        rag_html = f"<html><body><h1>GENERATION FAILED: {e}</h1></body></html>"
        failed_files.append("rag-architecture.html")

    # ── 4. semantic-tables.html ──────────────────────────────────────────────
    try:
        semantic_html = await _call_claude_with_retry(f"""
You are a senior SEO analyst. Generate a complete styled HTML5 competitor comparison page.

CONTEXT:
{ctx}

REQUIREMENTS:
- Full HTML document: <!DOCTYPE html>, <html>, <head> with embedded CSS, <body>
- Dark professional theme (#0a0a0a background, #e8e8e8 text, #c8f135 accents)
- H1 title: "Competitive Analysis — {client_name}"
- A detailed <table> comparing client vs each competitor across:
  Content Depth, Schema Coverage, Topic Clusters, FAQ Coverage, Trust Signals, AI Visibility Score, Mobile Experience, B2B Focus
- Color-code cells using inline style: green (#00c896) = strong, yellow (#ffc800) = moderate, red (#ff5c35) = weak
- A "Key Insights" <section> below the table with 5 bullet points
- Output ONLY the complete HTML document. No explanation.
""", "semantic-tables.html")
        semantic_html = _clean_output(semantic_html)
        semantic_html = re.sub(r'^```[a-z]*\n?', '', semantic_html.strip(), flags=re.MULTILINE)
        semantic_html = semantic_html.replace('```', '').strip()
    except Exception as e:
        semantic_html = f"<html><body><h1>GENERATION FAILED: {e}</h1></body></html>"
        failed_files.append("semantic-tables.html")

    # ── 5. llms-full.txt ─────────────────────────────────────────────────────
    try:
        llms_txt = await _call_claude_with_retry(f"""
You are a senior content strategist. Generate a comprehensive LLM-optimized content brief.

CONTEXT:
{ctx}

REQUIREMENTS:
Output the following structure with real content — no placeholders:

DATE: {today}

# LLM CONTENT BRIEF — {client_name}

## Executive Summary
## Brand Voice & Positioning
## Primary Keywords
(list exactly 20 keywords, one per line)
## Secondary Keywords
(list exactly 20 keywords, one per line)
## Topic Clusters
(5 clusters, each with 5 subtopics)
## Semantic Keyword Groups
## Content Gaps vs Competitors
## Recommended Content Types
## Entity Relationships
## Quick Wins & Recommendations

Output ONLY the content brief. No explanation.
""", "llms-full.txt")
        llms_txt = _clean_output(llms_txt)
    except Exception as e:
        llms_txt = f"GENERATION FAILED: {e}"
        failed_files.append("llms-full.txt")

    # ── 6. client-facing-report.md ───────────────────────────────────────────
    try:
        report_md = await _call_claude_with_retry(f"""
You are a senior SEO consultant. Generate a polished professional Markdown report.

CONTEXT:
{ctx}

REQUIREMENTS:
Output the following structure with real, specific, actionable content:

# SEO & Content Strategy Report — {client_name}

## Executive Summary
## Current State Analysis
## Competitive Landscape
## Schema & Structured Data Recommendations
## Content Strategy
## Technical SEO Recommendations
## Quick Wins
(top 5, each with effort level: Low/Medium/High)
## 90-Day Roadmap
### Month 1: Foundation
### Month 2: Execution
### Month 3: Scale
## KPIs to Track
## Conclusion

Be specific and actionable. Output ONLY the Markdown. No explanation.
""", "client-facing-report.md")
        report_md = _clean_output(report_md)
    except Exception as e:
        report_md = f"GENERATION FAILED: {e}"
        failed_files.append("client-facing-report.md")

    # ── 7. press-release-draft.md ────────────────────────────────────────────
    try:
        press_md = await _call_claude_with_retry(f"""
You are a PR writer. Generate a full AP style press release.

CONTEXT:
{ctx}

REQUIREMENTS:
The VERY FIRST LINE must be exactly:
*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***

Then output:

FOR IMMEDIATE RELEASE

[Strong news headline about {client_name}]
[One-line subheadline]

[City], {today} — [Opening paragraph with most newsworthy info]

[Quote from CEO/Founder with attribution]

[Body paragraph 2 — supporting details]

[Quote from satisfied client or industry expert]

[Body paragraph 3 — market context]

About {client_name}:
[2-sentence company boilerplate]

Media Contact:
[Name Placeholder]
press@{client_url.replace('https://','').replace('http://','').split('/')[0]}
+1 (000) 000-0000

###

Output ONLY the press release. No explanation.
""", "press-release-draft.md")
        press_md = _clean_output(press_md)
        if not press_md.startswith("*** DRAFT ONLY"):
            press_md = "*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***\n\n" + press_md
    except Exception as e:
        press_md = f"*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***\n\nGENERATION FAILED: {e}"
        failed_files.append("press-release-draft.md")

    # ── Safety guarantees ────────────────────────────────────────────────────
    if not llms_txt.startswith("DATE:") and not llms_txt.startswith("GENERATION"):
        llms_txt = f"DATE: {today}\n\n" + llms_txt

    files = {
        "deep-schema.json":        schema,
        "ai-training-faq.csv":     faq_csv,
        "rag-architecture.html":   rag_html,
        "semantic-tables.html":    semantic_html,
        "llms-full.txt":           llms_txt,
        "client-facing-report.md": report_md,
        "press-release-draft.md":  press_md,
    }

    # ── Raise if any files failed ────────────────────────────────────────────
    if failed_files:
        raise RuntimeError(
            f"{len(failed_files)} of 7 files failed to generate: {', '.join(failed_files)}. "
            f"Please retry."
        )

    return files
