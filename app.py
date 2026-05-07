"""
app.py — Wabi Sabi Executioner (Streamlit Edition)
Gated with username/password login.
"""
import asyncio
import io
import zipfile
from datetime import datetime

import streamlit as st

# ── Page config MUST be first ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Wabi Sabi Executioner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auth credentials ──────────────────────────────────────────────────────────
VALID_USERNAME = "wabisabi"
VALID_PASSWORD = "@123Darklord"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Global */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0a;
    color: #e8e8e8;
}

/* App background */
.stApp { background-color: #0a0a0a; }

/* ── LOGIN PAGE ── */
.login-wrap {
    max-width: 420px;
    margin: 8vh auto 0;
    padding: 2.5rem;
    background: #111111;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
}
.login-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    letter-spacing: 3px;
    color: #e8e8e8;
    margin-bottom: 0;
    line-height: 1;
}
.login-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #c8f135;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}
.login-error {
    background: rgba(255,92,53,0.1);
    border: 1px solid rgba(255,92,53,0.3);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #ff5c35;
    margin-bottom: 1rem;
}

/* ── HEADER ── */
.ws-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 2rem 0;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 2rem;
}
.ws-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 3px;
    color: #e8e8e8;
}
.ws-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    background: #c8f135;
    color: #000;
    padding: 3px 8px;
    border-radius: 3px;
    letter-spacing: 1px;
    margin-left: 0.75rem;
    vertical-align: middle;
}
.ws-logout {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #666;
    letter-spacing: 1px;
}

/* ── SECTION LABELS ── */
.section-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    color: #c8f135;
    line-height: 1;
}
.section-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #e8e8e8;
}
.section-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: #666;
    margin-top: 2px;
}
.section-card {
    background: #111111;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
}

/* ── STATUS BOXES ── */
.status-complete {
    background: rgba(0,200,150,0.05);
    border: 1px solid rgba(0,200,150,0.3);
    border-radius: 8px;
    padding: 1.25rem;
    font-family: 'DM Mono', monospace;
}
.status-error {
    background: rgba(255,92,53,0.05);
    border: 1px solid rgba(255,92,53,0.3);
    border-radius: 8px;
    padding: 1.25rem;
    font-family: 'DM Mono', monospace;
}
.status-running {
    background: rgba(200,241,53,0.05);
    border: 1px solid rgba(200,241,53,0.3);
    border-radius: 8px;
    padding: 1.25rem;
    font-family: 'DM Mono', monospace;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #e8e8e8 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
    border-radius: 4px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #c8f135 !important;
    box-shadow: 0 0 0 2px rgba(200,241,53,0.1) !important;
}

/* Labels */
.stTextInput label, .stTextArea label, .stToggle label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #666 !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: #c8f135 !important;
    color: #000 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.75rem 2rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    background: #d8ff3a !important;
    box-shadow: 0 8px 24px rgba(200,241,53,0.2) !important;
    transform: translateY(-1px) !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #666 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 4px !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #c8f135 !important;
    color: #c8f135 !important;
}

/* Download button */
.stDownloadButton > button {
    background: #c8f135 !important;
    color: #000 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.2rem !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 6px !important;
    width: 100% !important;
    padding: 1rem !important;
}

/* Toggle */
.stToggle > label { color: #e8e8e8 !important; }

/* Divider */
hr { border-color: #2a2a2a !important; }

/* Pipeline steps */
.pipe-step {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #111;
    border: 1px solid #2a2a2a;
    padding: 4px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #666;
    border-radius: 3px;
    margin: 2px;
}
.pipe-dot { color: #c8f135; }

/* File badges */
.file-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    margin: 3px;
}
.badge-json { background: rgba(200,241,53,0.15); color: #c8f135; }
.badge-html { background: rgba(255,92,53,0.15); color: #ff5c35; }
.badge-txt  { background: rgba(100,100,255,0.15); color: #8888ff; }
.badge-csv  { background: rgba(0,200,150,0.15); color: #00c896; }
.badge-md   { background: rgba(255,200,0,0.15); color: #ffc800; }
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "zip_bytes" not in st.session_state:
    st.session_state.zip_bytes = None
if "zip_name" not in st.session_state:
    st.session_state.zip_name = "wabisabi-output.zip"


# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div class='login-wrap'>
        <div class='login-title'>WABI SABI</div>
        <div class='login-sub'>// Executioner v1.0 — Restricted Access</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            username = st.text_input("Username", placeholder="wabisabi", key="login_user")
            password = st.text_input("Password", type="password", placeholder="••••••••••••", key="login_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("⚡  ENTER", type="primary", key="login_btn"):
                if username == VALID_USERNAME and password == VALID_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.markdown("<div class='login-error'>✗ Invalid credentials. Access denied.</div>", unsafe_allow_html=True)
        st.markdown("<br>")
        st.markdown("<center style='font-family:DM Mono,monospace;font-size:0.6rem;color:#333'>WABI SABI AGENCY · INTERNAL TOOL</center>", unsafe_allow_html=True)


# ── MAIN APP ──────────────────────────────────────────────────────────────────
def show_app():
    from services.firecrawl_service import scrape_url, scrape_multiple
    from services.claude_service import generate_all_files
    from services.indexnow_service import ping_indexnow
    from services.sheets_service import save_client, load_clients

    # Header
    st.markdown("""
    <div class='ws-header'>
        <div>
            <span class='ws-logo'>WABI SABI</span>
            <span class='ws-badge'>EXECUTIONER v1.0</span>
        </div>
        <div class='ws-logout'>// AUTHENTICATED</div>
    </div>
    """, unsafe_allow_html=True)

    # Logout button top right
    col_h1, col_h2 = st.columns([5, 1])
    with col_h2:
        if st.button("Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.zip_bytes = None
            st.rerun()

    # Pipeline pills
    st.markdown("""
    <div style='margin-bottom:2rem'>
        <span class='pipe-step'><span class='pipe-dot'>●</span> CLIENT URL</span>
        <span style='color:#2a2a2a;font-family:DM Mono,monospace'> → </span>
        <span class='pipe-step'><span class='pipe-dot'>●</span> FIRECRAWL</span>
        <span style='color:#2a2a2a;font-family:DM Mono,monospace'> → </span>
        <span class='pipe-step'><span class='pipe-dot'>●</span> GROQ CALL A</span>
        <span style='color:#2a2a2a;font-family:DM Mono,monospace'> + </span>
        <span class='pipe-step'><span class='pipe-dot'>●</span> GROQ CALL B</span>
        <span style='color:#2a2a2a;font-family:DM Mono,monospace'> → </span>
        <span class='pipe-step'><span class='pipe-dot'>●</span> ZIP</span>
        <span style='color:#2a2a2a;font-family:DM Mono,monospace'> → </span>
        <span class='pipe-step'><span class='pipe-dot'>●</span> INDEXNOW</span>
    </div>
    """, unsafe_allow_html=True)

    # ── FORM ──
    col_form, col_side = st.columns([3, 2], gap="large")

    with col_form:
        # 01 Client Info
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<span class='section-num'>01</span> <span class='section-title'>Client Information</span><br><span class='section-sub'>Primary website to analyze</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            client_name = st.text_input("Client Name *", placeholder="Acme Corporation", key="client_name")
        with c2:
            client_url = st.text_input("Client URL *", placeholder="https://acme.com", key="client_url")
        st.markdown("</div>", unsafe_allow_html=True)

        # 02 Competitors
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<span class='section-num'>02</span> <span class='section-title'>Competitor URLs</span><br><span class='section-sub'>Up to 3 competitor sites to scrape via Firecrawl</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        competitor_1 = st.text_input("Competitor 1", placeholder="https://competitor1.com", key="comp1")
        competitor_2 = st.text_input("Competitor 2", placeholder="https://competitor2.com", key="comp2")
        competitor_3 = st.text_input("Competitor 3", placeholder="https://competitor3.com", key="comp3")
        st.markdown("</div>", unsafe_allow_html=True)

        # 03 Audience
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<span class='section-num'>03</span> <span class='section-title'>Audience Brain-Dump</span><br><span class='section-sub'>Raw notes → Claude generates targeted Q&A CSV</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        audience = st.text_area(
            "Audience Notes",
            placeholder="e.g. B2B SaaS founders in the US, aged 35-55, struggle with churn, care about LTV, compare tools on G2 and Reddit...",
            height=100,
            key="audience"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # 04 Attribution
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<span class='section-num'>04</span> <span class='section-title'>Wabi Sabi Attribution</span><br><span class='section-sub'>Inject agency name into schema disambiguatingDescription</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        attribution = st.toggle("Add Agency Attribution to Schema", value=False, key="attribution")
        if attribution:
            st.markdown("<span style='font-family:DM Mono,monospace;font-size:0.65rem;color:#c8f135'>✓ YES — Agency name will be injected into disambiguatingDescription</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='font-family:DM Mono,monospace;font-size:0.65rem;color:#666'>✗ NO — Schema will be clean</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── EXECUTE BUTTON ──
        st.markdown("<br>", unsafe_allow_html=True)
        execute = st.button("⚡  EXECUTE MASTER PLAN", type="primary", key="execute_btn")

    # ── SIDEBAR / RIGHT COLUMN ──
    with col_side:
        # Output files list
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<span class='section-title'>Output Files</span><br><span class='section-sub'>7 files packed into one ZIP</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <span class='file-badge badge-json'>JSON</span> deep-schema.json<br><br>
        <span class='file-badge badge-html'>HTML</span> rag-architecture.html<br><br>
        <span class='file-badge badge-html'>HTML</span> semantic-tables.html<br><br>
        <span class='file-badge badge-txt'>TXT</span> llms-full.txt<br><br>
        <span class='file-badge badge-csv'>CSV</span> ai-training-faq.csv<br><br>
        <span class='file-badge badge-md'>MD</span> client-facing-report.md<br><br>
        <span class='file-badge badge-md'>MD</span> press-release-draft.md
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Download if available
        if st.session_state.zip_bytes:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='status-complete'>", unsafe_allow_html=True)
            st.markdown("<span style='color:#00c896;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:2px'>// COMPLETE ✓</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇  DOWNLOAD ZIP",
                data=st.session_state.zip_bytes,
                file_name=st.session_state.zip_name,
                mime="application/zip",
            )

    # ── EXECUTION LOGIC ──
    if execute:
        if not client_name or not client_url:
            st.error("Client Name and Client URL are required!")
        else:
            st.session_state.zip_bytes = None

            competitor_urls = [u for u in [competitor_1, competitor_2, competitor_3] if u.strip()]

            with st.status("⚡ Executing master plan...", expanded=True) as status:
                try:
                    # Step 1: Scrape client
                    st.write("🔍 Scraping client URL via Firecrawl...")
                    client_scraped = asyncio.run(scrape_url(client_url))
                    client_content = client_scraped.get("content", "") if isinstance(client_scraped, dict) else ""
                    st.write("✅ Client URL scraped")

                    # Step 2: Scrape competitors
                    competitors_data = []
                    if competitor_urls:
                        st.write("🔍 Scraping competitor URLs...")
                        competitors_data = asyncio.run(scrape_multiple(competitor_urls))
                        st.write(f"✅ {len(competitors_data)} competitor(s) scraped")

                    # Step 3 & 4: Generate files via Groq
                    st.write("🤖 Claude Call A — generating schema, tables, HTML, CSV...")
                    st.write("🤖 Claude Call B — generating reports, press release, LLM brief...")
                    files = asyncio.run(generate_all_files(
                        client_name=client_name,
                        client_url=client_url,
                        scraped_client=client_content,
                        competitors=competitors_data,
                        audience=audience,
                        wabisabi_attribution=attribution,
                    ))
                    st.write("✅ All 7 files generated")

                    # Step 5: IndexNow
                    st.write("📡 Pinging IndexNow API...")
                    indexnow_result = asyncio.run(ping_indexnow(client_url))
                    st.write(f"✅ IndexNow: {indexnow_result['message']}")

                    # Step 6: Google Sheets
                    st.write("📊 Saving to Google Sheets...")
                    save_client({
                        "client_name": client_name,
                        "client_url": client_url,
                        "competitor_1": competitor_1,
                        "competitor_2": competitor_2,
                        "competitor_3": competitor_3,
                        "audience": audience,
                        "wabisabi_attribution": attribution,
                    })
                    st.write("✅ Saved to Google Sheets")

                    # Step 7: Package ZIP
                    st.write("📦 Packaging ZIP...")
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for filename, content in files.items():
                            zf.writestr(filename, content)
                        manifest = f"""WABI SABI EXECUTIONER — Generation Manifest
Generated: {datetime.utcnow().isoformat()} UTC
Client: {client_name}
Client URL: {client_url}
Competitors: {', '.join(competitor_urls) or 'None'}
Attribution: {'Yes' if attribution else 'No'}
IndexNow: {indexnow_result['message']}

FILES:
""" + "\n".join(f"  - {f}" for f in files)
                        zf.writestr("MANIFEST.txt", manifest)
                    zip_buffer.seek(0)

                    safe_name = client_name.lower().replace(" ", "-")
                    zip_name = f"wabisabi-{safe_name}-{datetime.utcnow().strftime('%Y%m%d')}.zip"

                    st.session_state.zip_bytes = zip_buffer.getvalue()
                    st.session_state.zip_name = zip_name

                    status.update(label="✅ Master plan complete! Download your ZIP →", state="complete")
                    st.rerun()

                except Exception as e:
                    status.update(label=f"❌ Error: {str(e)}", state="error")
                    st.error(str(e))

    # ── CLIENTS TAB ──
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown("<span class='section-title'>Client Registry</span><br><span class='section-sub'>// Loaded from Google Sheets</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        from services.sheets_service import load_clients
        clients = load_clients()
        if clients:
            st.dataframe(
                clients,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.markdown("<span style='font-family:DM Mono,monospace;font-size:0.75rem;color:#666'>No clients saved yet. Run a generation to populate this table.</span>", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"<span style='font-family:DM Mono,monospace;font-size:0.72rem;color:#666'>Sheets not connected: {e}</span>", unsafe_allow_html=True)


# ── ROUTER ───────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login()
else:
    show_app()
