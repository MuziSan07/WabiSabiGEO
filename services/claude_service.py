# """
# services/claude_service.py
# Two parallel Claude API calls to generate all 7 output files.
# Call A → code/data files: deep-schema.json, semantic-tables.html, rag-architecture.html, ai-training-faq.csv
# Call B → text/markdown files: llms-full.txt, client-facing-report.md, press-release-draft.md
# """
# import asyncio
# from datetime import date
# import anthropic
# from config import ANTHROPIC_API_KEY, AGENCY_NAME

# CLAUDE_MODEL = "claude-3-5-sonnet-latest"

# client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# SAFETY_RULE = (
#     "SAFETY RULE: If the client site is empty or missing information and you must invent "
#     "a technical fact to fill a gap, wrap that invented fact in [CLIENT VERIFICATION REQUIRED]. "
#     "Never silently hallucinate facts."
# )


# def _build_context(
#     client_name: str,
#     client_url: str,
#     scraped_client: str,
#     competitors: list[dict],
#     audience: str,
#     wabisabi_attribution: bool,
# ) -> str:
#     comp_block = "\n\n".join(
#         f"### Competitor {i+1}: {c['url']}\n{c['content'][:3000]}"
#         for i, c in enumerate(competitors)
#     )
#     attr_note = (
#         f'ATTRIBUTION: Add "{AGENCY_NAME}" strictly into the "disambiguatingDescription" '
#         f'property of the JSON-LD schema.'
#         if wabisabi_attribution
#         else "ATTRIBUTION: Do NOT add any agency name."
#     )
#     return f"""
# CLIENT: {client_name}
# CLIENT URL: {client_url}
# CLIENT SITE CONTENT:
# {scraped_client[:4000]}

# COMPETITOR DATA:
# {comp_block}

# TARGET AUDIENCE BRAIN-DUMP:
# {audience}

# {attr_note}
# {SAFETY_RULE}
# """.strip()


# # ── CALL A: Code / Data files ───────────────────────────────────────────────
# PROMPT_A = """
# You are a senior SEO architect and structured data expert. Given the context below, generate FOUR files.
# Return them inside XML tags exactly as shown. Do not add explanation outside tags.

# <deep_schema>
# <!-- deep-schema.json: Full JSON-LD schema.org markup for the client. Include Organization, WebSite,
#      BreadcrumbList, FAQPage. If attribution is required, add the agency to disambiguatingDescription. -->
# </deep_schema>

# <rag_architecture>
# <!-- rag-architecture.html: Structured HTML with H2 headings and bullet points covering the client's
#      RAG (Retrieval Augmented Generation) content architecture recommendations. Use proper HTML5. -->
# </rag_architecture>

# <semantic_tables>
# <!-- semantic-tables.html: Competitor comparison semantic table in HTML. Compare client vs each competitor
#      across: Content Depth, Schema Coverage, Topic Clusters, FAQ Coverage, Trust Signals. -->
# </semantic_tables>

# <ai_faq_csv>
# <!-- ai-training-faq.csv: CSV with columns: Question,Answer,Category,Priority
#      Generate 20 targeted Q&As based on the audience brain-dump. -->
# </ai_faq_csv>
# """

# # ── CALL B: Text / Markdown files ───────────────────────────────────────────
# PROMPT_B = f"""
# You are a senior content strategist and PR writer. Given the context below, generate THREE files.
# Return them inside XML tags exactly as shown. Do not add explanation outside tags.

# <llms_full>
# <!-- llms-full.txt: A comprehensive LLM-optimized content brief for the client.
#      Start the file with: DATE: {date.today().isoformat()}
#      Then include: Executive Summary, Key Topics, Semantic Keywords, Content Gaps, Recommendations. -->
# </llms_full>

# <client_report>
# <!-- client-facing-report.md: A polished Markdown report for the client covering:
#      Executive Summary, Competitive Analysis, Schema Recommendations, Content Strategy,
#      Quick Wins, 90-Day Roadmap. Professional tone. -->
# </client_report>

# <press_release>
# <!-- press-release-draft.md: A press release draft. IMPORTANT: The very first line of the file
#      MUST be exactly: *** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***
#      Then write the full press release in standard AP style format. -->
# </press_release>
# """


# def _extract_tag(xml: str, tag: str) -> str:
#     """Extract content between XML tags."""
#     import re
#     pattern = rf"<{tag}>(.*?)</{tag}>"
#     m = re.search(pattern, xml, re.DOTALL)
#     if m:
#         content = m.group(1).strip()
#         # Strip XML comment wrappers if present
#         content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
#         return content
#     return f"[Generation failed for {tag}]"


# async def _call_claude(system_prompt: str, context: str, label: str) -> str:
#     print(f"[Claude] Starting {label} call...")
#     message = await client.messages.create(
#         model=CLAUDE_MODEL,
#         max_tokens=8000,
#         system=system_prompt,
#         messages=[{"role": "user", "content": context}],
#     )
#     print(f"[Claude] {label} call complete.")
#     return message.content[0].text


# async def generate_all_files(
#     client_name: str,
#     client_url: str,
#     scraped_client: str,
#     competitors: list[dict],
#     audience: str,
#     wabisabi_attribution: bool,
# ) -> dict[str, str]:
#     """Run two parallel Claude API calls and return a dict of filename → content."""
#     context = _build_context(
#         client_name, client_url, scraped_client, competitors, audience, wabisabi_attribution
#     )

#     # Parallel execution
#     result_a, result_b = await asyncio.gather(
#         _call_claude(PROMPT_A, context, "Call-A (code/data files)"),
#         _call_claude(PROMPT_B, context, "Call-B (text/markdown files)"),
#     )

#     today = date.today().isoformat()

#     files = {
#         "deep-schema.json": _extract_tag(result_a, "deep_schema"),
#         "rag-architecture.html": _extract_tag(result_a, "rag_architecture"),
#         "semantic-tables.html": _extract_tag(result_a, "semantic_tables"),
#         "ai-training-faq.csv": _extract_tag(result_a, "ai_faq_csv"),
#         "llms-full.txt": _extract_tag(result_b, "llms_full"),
#         "client-facing-report.md": _extract_tag(result_b, "client_report"),
#         "press-release-draft.md": _extract_tag(result_b, "press_release"),
#     }

#     # Guarantee press release DRAFT warning
#     if not files["press-release-draft.md"].startswith("*** DRAFT ONLY"):
#         files["press-release-draft.md"] = (
#             "*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***\n\n" + files["press-release-draft.md"]
#         )

#     # Guarantee llms-full.txt has date
#     if not files["llms-full.txt"].startswith("DATE:"):
#         files["llms-full.txt"] = f"DATE: {today}\n\n" + files["llms-full.txt"]

#     return files

"""
services/claude_service.py
Two parallel API calls to generate all 7 output files.
Currently using GROQ (llama-3.1-8b-instant) — swap back to Anthropic when credits are added.
Call A → code/data files: deep-schema.json, semantic-tables.html, rag-architecture.html, ai-training-faq.csv
Call B → text/markdown files: llms-full.txt, client-facing-report.md, press-release-draft.md
"""
import asyncio
from datetime import date
import httpx
import os
from dotenv import load_dotenv
from config import AGENCY_NAME

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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
        f"### Competitor {i+1}: {c['url']}\n{c['content'][:300]}"
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
{scraped_client[:500]}

COMPETITOR DATA:
{comp_block}

TARGET AUDIENCE BRAIN-DUMP:
{audience}

{attr_note}
{SAFETY_RULE}
""".strip()


PROMPT_A = """
You are a senior SEO architect and structured data expert. Given the context below, generate FOUR files.
Return them inside XML tags exactly as shown. Do not add explanation outside tags.

<deep_schema>
<!-- deep-schema.json: Full JSON-LD schema.org markup for the client. Include Organization, WebSite,
     BreadcrumbList, FAQPage. If attribution is required, add the agency to disambiguatingDescription. -->
</deep_schema>

<rag_architecture>
<!-- rag-architecture.html: Structured HTML with H2 headings and bullet points covering the client's
     RAG (Retrieval Augmented Generation) content architecture recommendations. Use proper HTML5. -->
</rag_architecture>

<semantic_tables>
<!-- semantic-tables.html: Competitor comparison semantic table in HTML. Compare client vs each competitor
     across: Content Depth, Schema Coverage, Topic Clusters, FAQ Coverage, Trust Signals. -->
</semantic_tables>

<ai_faq_csv>
<!-- ai-training-faq.csv: CSV with columns: Question,Answer,Category,Priority
     Generate 20 targeted Q&As based on the audience brain-dump. -->
</ai_faq_csv>
"""

PROMPT_B = f"""
You are a senior content strategist and PR writer. Given the context below, generate THREE files.
Return them inside XML tags exactly as shown. Do not add explanation outside tags.

<llms_full>
<!-- llms-full.txt: A comprehensive LLM-optimized content brief for the client.
     Start the file with: DATE: {date.today().isoformat()}
     Then include: Executive Summary, Key Topics, Semantic Keywords, Content Gaps, Recommendations. -->
</llms_full>

<client_report>
<!-- client-facing-report.md: A polished Markdown report for the client covering:
     Executive Summary, Competitive Analysis, Schema Recommendations, Content Strategy,
     Quick Wins, 90-Day Roadmap. Professional tone. -->
</client_report>

<press_release>
<!-- press-release-draft.md: A press release draft. IMPORTANT: The very first line of the file
     MUST be exactly: *** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***
     Then write the full press release in standard AP style format. -->
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


async def _call_groq(system_prompt: str, context: str, label: str) -> str:
    print(f"[Groq] Starting {label} call...")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        print(f"[Groq] {label} call complete.")
        return data["choices"][0]["message"]["content"]


async def generate_all_files(
    client_name: str,
    client_url: str,
    scraped_client: str,
    competitors: list[dict],
    audience: str,
    wabisabi_attribution: bool,
) -> dict[str, str]:
    context = _build_context(
        client_name, client_url, scraped_client, competitors, audience, wabisabi_attribution
    )

    # Sequential calls to avoid Groq 429 rate limit
    result_a = await _call_groq(PROMPT_A, context, "Call-A (code/data files)")
    await asyncio.sleep(30)
    result_b = await _call_groq(PROMPT_B, context, "Call-B (text/markdown files)")

    today = date.today().isoformat()

    files = {
        "deep-schema.json": _extract_tag(result_a, "deep_schema"),
        "rag-architecture.html": _extract_tag(result_a, "rag_architecture"),
        "semantic-tables.html": _extract_tag(result_a, "semantic_tables"),
        "ai-training-faq.csv": _extract_tag(result_a, "ai_faq_csv"),
        "llms-full.txt": _extract_tag(result_b, "llms_full"),
        "client-facing-report.md": _extract_tag(result_b, "client_report"),
        "press-release-draft.md": _extract_tag(result_b, "press_release"),
    }

    if not files["press-release-draft.md"].startswith("*** DRAFT ONLY"):
        files["press-release-draft.md"] = (
            "*** DRAFT ONLY: REQUIRES FOUNDER REVIEW ***\n\n" + files["press-release-draft.md"]
        )

    if not files["llms-full.txt"].startswith("DATE:"):
        files["llms-full.txt"] = f"DATE: {today}\n\n" + files["llms-full.txt"]

    return files