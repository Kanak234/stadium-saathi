"""StadiumSaathi — Smart Stadium & Tournament Operations Assistant.

FIFA World Cup 2026 | PromptWars Challenge 4.
Runs 100% offline: no external API, no database.
Accessibility: high-contrast mode, large-text mode, chart data tables,
descriptive labels and help tooltips throughout.
"""

from __future__ import annotations

import datetime as dt
import random

import numpy as np
import pandas as pd
import streamlit as st

from assistant import DATA, LANGS, answer, quick_suggestions

# ----------------------------------------------------------------- page setup
st.set_page_config(
    page_title="StadiumSaathi | FIFA World Cup 2026",
    page_icon="🏟️",
    layout="wide",
)

# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Your Settings")
    lang = st.selectbox(
        "🌐 Language / भाषा", LANGS, index=2,
        help="The assistant will reply in this language.",
    )
    zone = st.selectbox(
        "📍 I am currently near", DATA["zones"], index=0,
        help="Used to show you the nearest facilities first.",
    )
    st.divider()
    st.subheader("♿ Accessibility")
    high_contrast = st.toggle(
        "High contrast mode", value=False,
        help="Stronger colours and borders for low-vision users.",
    )
    large_text = st.toggle(
        "Large text", value=False,
        help="Increases the base font size across the app.",
    )
    st.divider()
    st.caption(
        "**StadiumSaathi** helps fans, organizers, volunteers and venue staff "
        "during FIFA World Cup 2026.\n\n"
        "Built for **PromptWars — Challenge 4: Smart Stadiums & Tournament Operations**."
    )
    st.caption("🔒 Privacy friendly: runs fully offline. No personal data is collected or stored.")

# ------------------------------------------------------------ theming (a11y)
_base_font = "19px" if large_text else "16px"
_hero_bg = ("linear-gradient(105deg, #000000 0%, #0a0a0a 100%)" if high_contrast
            else "linear-gradient(105deg, #0b1f3a 0%, #123c6b 55%, #1b6ca8 100%)")
_pill_bg, _pill_fg = ("#ffff00", "#000000") if high_contrast else ("#ffd447", "#123c6b")

st.markdown(
    f"""
    <style>
      html, body, [class*="css"] {{ font-size: {_base_font}; }}
      .hero {{
        background: {_hero_bg};
        border-radius: 14px; padding: 26px 30px; color: #ffffff; margin-bottom: 6px;
        {'border: 3px solid #ffff00;' if high_contrast else ''}
      }}
      .hero h1 {{ margin: 0; font-size: 2.0rem; letter-spacing: 0.5px; }}
      .hero p  {{ margin: 6px 0 0 0; opacity: 0.95; font-size: 1.02rem; }}
      .pill {{
        display: inline-block; background: {_pill_bg}; color: {_pill_fg};
        border-radius: 999px; padding: 2px 12px; font-weight: 700;
        font-size: 0.8rem; margin-top: 10px;
      }}
      div[data-testid="stChatMessage"] {{ border-radius: 12px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero" role="banner" aria-label="StadiumSaathi — Smart Stadium Assistant">
      <h1>🏟️ StadiumSaathi</h1>
      <p>Smart Stadium &amp; Tournament Operations Assistant — {DATA['stadium']['event']}</p>
      <p style="font-size:0.9rem; opacity:0.9;">{DATA['stadium']['name']} · Capacity {DATA['stadium']['capacity']:,}</p>
      <span class="pill">Works fully offline · No API · Multilingual · Accessible</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- tabs
tab_chat, tab_nav, tab_crowd, tab_match, tab_access = st.tabs(
    ["💬 AI Fan Assistant", "🗺️ Navigate Stadium",
     "👥 Crowd Dashboard (Organizers)", "📅 Matches", "♿ Accessibility & ♻️ Green"]
)

# ================================================================= TAB 1: CHAT
with tab_chat:
    st.subheader("Ask me anything about the stadium")
    st.caption("English · हिंदी · Hinglish — sab chalega!")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None

    sugg = quick_suggestions(lang)
    cols = st.columns(len(sugg))
    for c, s in zip(cols, sugg):
        if c.button(s, use_container_width=True, key=f"chip_{s}",
                    help=f"Ask: {s}"):
            st.session_state.pending_query = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🏟️"):
            st.markdown(m["content"])

    user_q = st.chat_input("Type here... e.g. 'Gate 3 kahan hai?'", max_chars=300)
    if st.session_state.pending_query and not user_q:
        user_q = st.session_state.pending_query
        st.session_state.pending_query = None

    if user_q:
        st.session_state.messages.append({"role": "user", "content": user_q})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_q)
        reply, _intent = answer(user_q, lang, zone)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="🏟️"):
            st.markdown(reply)

    if st.session_state.messages and st.button("🧹 Clear chat", help="Remove all messages from this conversation"):
        st.session_state.messages = []
        st.rerun()

# ================================================================= TAB 2: NAVIGATION
FACILITY_OPTIONS: list[str] = [
    "Entry Gates", "Food Stalls", "Washrooms", "First Aid", "Parking",
    "Emergency Exits", "Water Refill (free)", "Recycling Points", "ATMs",
    "Merchandise Stores",
]


@st.cache_data(show_spinner=False)
def build_facility_df(facility: str) -> pd.DataFrame:
    """Build (and cache) the display table for a facility type."""
    if facility == "Entry Gates":
        df = pd.DataFrame(DATA["gates"]).rename(columns={
            "id": "Gate", "zone": "Zone", "serves": "Serves", "landmark": "Landmark"})
    elif facility == "Food Stalls":
        df = pd.DataFrame(DATA["food_stalls"]).rename(columns={
            "name": "Stall", "cuisine": "Cuisine", "zone": "Zone", "near": "Location"})
    elif facility == "Washrooms":
        df = pd.DataFrame(DATA["washrooms"]).rename(columns={
            "zone": "Zone", "location": "Location", "accessible": "Wheelchair OK"})
    elif facility == "First Aid":
        df = pd.DataFrame(DATA["first_aid"]).rename(columns={"zone": "Zone", "location": "Location"})
    elif facility == "Parking":
        df = pd.DataFrame(DATA["parking"]).rename(columns={
            "lot": "Lot", "for": "For", "zone": "Zone", "capacity": "Capacity"})
    elif facility == "Emergency Exits":
        df = pd.DataFrame(DATA["exits"]).rename(columns={"id": "Exit", "zone": "Zone", "note": "Location"})
    elif facility == "Water Refill (free)":
        df = pd.DataFrame(DATA["water_stations"]).rename(columns={"zone": "Zone", "location": "Location"})
    elif facility == "Recycling Points":
        df = pd.DataFrame(DATA["recycling_points"]).rename(columns={"zone": "Zone", "location": "Location"})
    elif facility == "ATMs":
        df = pd.DataFrame(DATA["atms"]).rename(columns={"zone": "Zone", "location": "Location"})
    else:
        df = pd.DataFrame(DATA["other"]["merchandise"]).rename(columns={
            "name": "Store", "zone": "Zone", "near": "Location"})
    return df


with tab_nav:
    st.subheader("Find any facility")
    facility = st.selectbox(
        "What are you looking for?", FACILITY_OPTIONS,
        help="Choose a facility type; options in your zone are shown first.",
    )
    df = build_facility_df(facility).copy()
    if "Zone" in df.columns:
        df["_near"] = df["Zone"] == zone
        df = df.sort_values("_near", ascending=False).drop(columns="_near").reset_index(drop=True)
        in_zone = int((df["Zone"] == zone).sum())
        if in_zone:
            st.success(f"✅ {in_zone} option(s) available in your zone (**{zone}**) — shown on top.")
        else:
            st.info(f"No {facility.lower()} in **{zone}** — nearest options listed below.")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("Table is screen-reader friendly and sortable — click any column header.")

# ================================================================= TAB 3: CROWD
ZONE_CAPACITY: dict[str, int] = {
    "North Stand": 20000, "South Stand": 20000, "East Stand": 18000,
    "West Stand": 18000, "VIP Lounge": 6500,
}
RED_THRESHOLD, AMBER_THRESHOLD, QUEUE_LIMIT = 85, 60, 30

with tab_crowd:
    st.subheader("Live crowd control room")
    st.caption("Simulated live feed (demo). In production this connects to gate "
               "sensors / turnstile counts / CCTV analytics.")

    if "crowd_seed" not in st.session_state:
        st.session_state.crowd_seed = 42
    if st.button("🔄 Refresh live data", help="Fetch the latest simulated readings"):
        st.session_state.crowd_seed = random.randint(0, 99999)

    rng = np.random.default_rng(st.session_state.crowd_seed)
    zones = DATA["zones"]
    density = {z: int(rng.uniform(35, 98)) for z in zones}
    gate_queue = {g["id"]: int(rng.uniform(5, 45)) for g in DATA["gates"]}

    total_in = sum(int(ZONE_CAPACITY[z] * density[z] / 100) for z in zones)
    busiest = max(density, key=lambda k: density[k])
    calmest_gate = min(gate_queue, key=lambda k: gate_queue[k])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fans inside", f"{total_in:,}")
    c2.metric("Capacity used", f"{int(total_in / DATA['stadium']['capacity'] * 100)}%")
    c3.metric("Busiest zone", busiest, f"{density[busiest]}% full")
    c4.metric("Fastest gate", f"Gate {calmest_gate}", f"~{gate_queue[calmest_gate]} min wait")

    st.markdown("#### Zone occupancy")
    zdf = pd.DataFrame({
        "Zone": zones,
        "Occupancy %": [density[z] for z in zones],
        "Status": ["🔴 High" if density[z] > RED_THRESHOLD else
                   "🟡 Medium" if density[z] > AMBER_THRESHOLD else "🟢 OK" for z in zones],
    })
    st.dataframe(
        zdf, use_container_width=True, hide_index=True,
        column_config={"Occupancy %": st.column_config.ProgressColumn(
            "Occupancy %", min_value=0, max_value=100, format="%d%%")},
    )

    st.markdown("#### Gate queues (minutes)")
    gdf = pd.DataFrame({"Gate": [f"Gate {g}" for g in gate_queue],
                        "Wait (min)": list(gate_queue.values())})
    st.bar_chart(gdf.set_index("Gate"))
    with st.expander("View gate queue data as a table (screen-reader friendly)"):
        st.dataframe(gdf, hide_index=True, use_container_width=True)

    st.markdown("#### 🧠 Decision support — recommended actions")
    recs: list[str] = []
    for z, d in density.items():
        if d > RED_THRESHOLD:
            calm = min(density, key=lambda k: density[k])
            recs.append(f"🔴 **{z}** is {d}% full — pause new entries, "
                        f"announce redirection towards **{calm}** concourse, deploy 2 extra stewards.")
        elif d > AMBER_THRESHOLD:
            recs.append(f"🟡 **{z}** at {d}% — monitor closely; keep one standby steward.")
    for g, w in gate_queue.items():
        if w > QUEUE_LIMIT:
            recs.append(f"⏳ **Gate {g}** queue ~{w} min — open extra lane, "
                        f"guide fans to **Gate {calmest_gate}** ({gate_queue[calmest_gate]} min).")
    if not recs:
        recs.append("🟢 All zones and gates within safe limits. No action needed.")
    for r in recs:
        st.markdown("- " + r)

    st.caption(f"Rules: crowd > {RED_THRESHOLD}% = red, > {AMBER_THRESHOLD}% = amber; "
               f"queue > {QUEUE_LIMIT} min triggers a gate action.")

# ================================================================= TAB 4: MATCHES
with tab_match:
    st.subheader("Matches at this stadium")
    mdf = pd.DataFrame(DATA["matches"]).rename(columns={
        "match": "Match", "teams": "Teams", "date": "Date",
        "time": "Kickoff", "status": "Status"})
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    final = DATA["matches"][-1]
    final_date = dt.date.fromisoformat(final["date"])
    days_left = (final_date - dt.datetime.now(dt.timezone.utc).date()).days
    if days_left > 0:
        st.info(f"⚽ **{final['match']}** in **{days_left} day(s)** — "
                f"{final['date']} at {final['time']}. Gates open 11:00, come early!")
    elif days_left == 0:
        st.success(f"⚽ **{final['match']} is TODAY!** Kickoff {final['time']}. "
                   "Gates are open — reach at least 2 hours early.")

# ================================================================= TAB 5: ACCESS + GREEN
with tab_access:
    left, right = st.columns(2)
    with left:
        st.subheader("♿ Accessibility")
        a = DATA["accessibility"]
        for v in [a["wheelchair_ramps"], a["assistance_desk"], a["accessible_parking"],
                  a["sensory_room"], a["sign_language"]]:
            st.markdown("- " + v)
        st.markdown(f"- 🙏 {DATA['other']['prayer_room']}")
        st.markdown(f"- 🔎 Lost & Found: {DATA['other']['lost_and_found']}")
        st.caption("This app also offers high-contrast and large-text modes "
                   "(sidebar) and table alternatives for every chart.")
    with right:
        st.subheader("♻️ Sustainability")
        st.markdown("- Free water refill stations in every stand — carry a reusable bottle.")
        for r in DATA["recycling_points"]:
            st.markdown(f"- Recycling bins: {r['location']} ({r['zone']})")
        st.markdown("- Use shuttle buses from Lot P3 to cut traffic and emissions.")

st.divider()
st.caption("StadiumSaathi v2.0 · PromptWars Challenge 4 · Python + Streamlit · "
           "100% offline AI (no external API, no database) · Unit-tested with pytest")
