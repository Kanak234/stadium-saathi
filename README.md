# 🏟️ StadiumSaathi — Smart Stadium & Tournament Operations Assistant

**PromptWars — [Challenge 4] Smart Stadiums & Tournament Operations**
**Event context: FIFA World Cup 2026 · Demo venue: New York New Jersey Stadium (MetLife)**

StadiumSaathi is an AI-powered assistant that helps **fans, organizers, volunteers and venue staff** during FIFA World Cup 2026 — navigation, crowd management, accessibility, multilingual help, sustainability and real-time decision support — all in one Streamlit app.

> ⚡ Works **100% offline** at runtime: no external API keys, no database, no internet dependency. Perfect for crowded stadiums where mobile networks get congested.

---

## ✨ Features → Challenge mapping

| Challenge requirement | How StadiumSaathi delivers |
|---|---|
| **Navigation** | Facility finder (gates, food, washrooms, parking, ATMs, exits) sorted by the fan's current zone + chat-based directions |
| **Crowd management** | Live crowd control room: zone occupancy, gate queues, red/amber/green alerts |
| **Real-time decision support** | Auto-generated action recommendations for organizers (redirect crowds, open gate lanes, deploy stewards) |
| **Multilingual assistance** | Full trilingual assistant — **English, हिंदी (Devanagari), Hinglish** — understands mixed queries like *"gate 3 kahan hai"* |
| **Accessibility** | Wheelchair ramps/seating info, sensory room, sign-language desk, accessible parking & washrooms |
| **Sustainability** | Free water-refill points, recycling-bin locator, shuttle guidance |
| **Transportation** | Parking lots, shuttle/bus lot, metro-side gate info |

## 🧠 How the AI works (offline)

The assistant is a lightweight **NLU + NLG pipeline** built in pure Python:

1. **Intent detection** — keyword + fuzzy matching (`difflib`) over 20 intents, with Hindi (Devanagari + romanised) and English trigger words.
2. **Entity extraction** — regex pulls specifics like gate numbers ("gate 3" → Gate C).
3. **Response generation** — template-based natural-language generation, filled live from `stadium_data.json` and the user's selected zone, in the user's chosen language.
4. **Decision support** — threshold rules convert live crowd numbers into plain-language operator recommendations.

Generative AI tools were used end-to-end to **design, build and deploy** this solution (as permitted by the event: *"YOU CAN USE ANY AI TOOL TO BUILD & DEPLOY"*). The runtime engine is intentionally offline-first for reliability inside a packed stadium; a cloud LLM API can be plugged into `assistant.answer()` later without changing the UI.

## 📁 Project structure

```
stadium-saathi/
├── app.py              # Streamlit UI (5 tabs)
├── assistant.py        # Offline AI engine (intents + trilingual NLG)
├── stadium_data.json   # Static stadium knowledge base
├── requirements.txt    # streamlit, pandas, numpy
└── README.md
```

## ▶️ Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## 🚀 Deploy free on Streamlit Community Cloud

1. Create a **public GitHub repo** (e.g. `stadium-saathi`) and upload all files of this folder to the repo **root**.
2. Go to **https://share.streamlit.io** → sign in with GitHub.
3. Click **"Create app" → "Deploy a public app from GitHub"**.
4. Select your repo, branch `main`, main file **`app.py`** → **Deploy**.
5. In ~2 minutes you get a public link like `https://<your-app>.streamlit.app` — submit this as your deployment link.

### 🇮🇳 Deploy (Hindi)

1. GitHub par public repo banao aur ye saari files repo ke **root** mein upload karo.
2. **share.streamlit.io** kholo → GitHub se sign in.
3. **Create app** → repo select karo → main file `app.py` → **Deploy** dabao.
4. 2 minute mein live link mil jayega — wahi link submission mein daal do.

## 👤 Team

**Kanak Prabhakar** — BCA, AISECT University, Hazaribagh
PromptWars (Hack2Skill) — Challenge 4 submission

---

*StadiumSaathi = Stadium + Saathi (साथी, "companion") — your companion inside the stadium.*
