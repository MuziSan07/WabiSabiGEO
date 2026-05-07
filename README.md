# ⚡ Wabi Sabi Executioner — Streamlit Edition
---

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Open: **http://localhost:8501**

---

## 🚀 Deploy FREE on Streamlit Cloud (live in 2 mins)

1. Push this folder to a **GitHub repo**
2. Go to → **[share.streamlit.io](https://share.streamlit.io)**
3. Click **New app** → connect your GitHub repo
4. Set **Main file:** `app.py`
5. Click **Advanced settings** → add your secrets:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
FIRECRAWL_API_KEY = "fc-..."
GROQ_API_KEY = "gsk_..."
GOOGLE_SHEET_ID = "1BLRvH3pZe_..."
INDEXNOW_KEY = "wabisabi2024xk39"
AGENCY_NAME = "Wabi Sabi Agency"
GOOGLE_CREDENTIALS_PATH = "credentials.json"
```

6. Hit **Deploy** — live URL in ~60 seconds! ✅

---

## Project Structure
```
wabisabi_streamlit/
├── app.py                  ← Main Streamlit app
├── config.py               ← Settings loader
├── requirements.txt        ← Dependencies
├── credentials.json        ← Google Service Account
├── .env                    ← Local API keys
├── .streamlit/
│   └── config.toml         ← Dark theme config
└── services/
    ├── claude_service.py   ← Groq API calls
    ├── firecrawl_service.py
    ├── sheets_service.py
    └── indexnow_service.py
```
