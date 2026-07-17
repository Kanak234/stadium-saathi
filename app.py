"""
StadiumSaathi - Smart Stadium & Tournament Operations Assistant
FIFA World Cup 2026 | PromptWars Challenge 4
Runs 100% offline: no external API, no database.
"""

import random
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from assistant import DATA, LANGS, answer, quick_suggestions

# ----------------------------------------------------------------- page setup
st.set_page_config(
    page_title="StadiumSaathi | FIFA World Cup 2026",
    page_icon="\U0001F3DF\uFE0F",
    layout="wide",
)

st.markdown(
    """
    <style>
      .hero {
        background: linear-gradient(105deg, #0b1f3a 0%, #123c6b 55%, #1b6ca8 100%);
        border-radius: 14px; padding: 26px 30px; color: #ffffff; margin-bottom: 6px;
      }
      .hero h1 { margin: 0; font-size: 2.0rem; letter-spacing: 0.5px; }
      .hero p  { margin: 6px 0 0 0; opacity: 0.92; font-size: 1.02rem; }
      .pill {
        display: inline-block; background: #ffd447; color: #123c6b;
        border-radius: 999px; padding: 2px 12px; font-weight: 700;
        font-size: 0.8rem; margin-top: 10px;
      }
      div[data-testid="stChatMessage"] { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero">
      <h1>\U0001F3DF\uFE0F StadiumSaathi</h1>
      <p>Smart Stadium &amp; Tournament Operations Assistant \u2014 {DATA['stadium']['event']}</p>
      <p style="font-size:0.9rem; opacity:0.85;">{DATA['stadium']['name']} \u00B7 Capacity {DATA['stadium']['capacity']:,}</p>
      <span class="pill">Works fully offline \u00B7 No API \u00B7 Multilingual</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("\u2699\uFE0F Your Settings")
    lang = st.selectbox("\U0001F310 Language / \u092d\u093e\u0937\u093e", LANGS, index=2)
    zone = st.selectbox("\U0001F4CD I am currently near", DATA["zones"], index=0)
    st.divider()
    st.caption(
        "**StadiumSaathi** helps fans, organizers, volunteers and venue staff "
        "during FIFA World Cup 2026.\n\n"
        "Built for **PromptWars \u2013 Challenge 4: Smart Stadiums & Tournament Operations**."
    )
    st.caption("\U0001F512 Privacy friendly: everything runs on-device / on-server. "
               "No personal data is collected.")

# ----------------------------------------------------------------- tabs
tab_chat, tab_nav, tab_crowd, tab_match, tab_access = st.tabs(
    [
        "\U0001F4AC AI Fan Assistant",
        "\U0001F5FA\uFE0F Navigate Stadium",
        "\U0001F465 Crowd Dashboard (Organizers)",
        "\U0001F4C5 Matches",
        "\u267F Accessibility & \u267B\uFE0F Green",
    ]
)

# ================================================================= TAB 1: CHAT
with tab_chat:
    st.subheader("Ask me anything about the stadium")
    st.caption("English \u00B7 \u0939\u093f\u0902\u0926\u0940 \u00B7 Hinglish \u2014 sab chalega!")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None

    # quick suggestion chips
    sugg = quick_suggestions(lang)
    cols = st.columns(len(sugg))
    for c, s in zip(cols, sugg):
        if c.button(s, use_container_width=True, key=f"chip_{s}"):
            st.session_state.pending_query = s

    # history
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="\U0001F9D1" if m["role"] == "user" else "\U0001F3DF\uFE0F"):
            st.markdown(m["content"])

    # input
    user_q = st.chat_input("Type here... e.g. 'Gate 3 kahan hai?'")
    if st.session_state.pending_query and not user_q:
        user_q = st.session_state.pending_query
        st.session_state.pending_query = None

    if user_q:
        st.session_state.messages.append({"role": "user", "content": user_q})
        with st.chat_message("user", avatar="\U0001F9D1"):
            st.markdown(user_q)
        reply, intent = answer(user_q, lang, zone)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="\U0001F3DF\uFE0F"):
            st.markdown(reply)

    if st.session_state.messages:
        if st.button("\U0001F9F9 Clear chat"):
            st.session_state.messages = []
            st.rerun()

# ================================================================= TAB 2: NAVIGATION
with tab_nav:
    st.subheader("Find any facility")
    facility = st.selectbox(
        "What are you looking for?",
        ["Entry Gates", "Food Stalls", "Washrooms", "First Aid", "Parking",
         "Emergency Exits", "Water Refill (free)", "Recycling Points", "ATMs",
         "Merchandise Stores"],
    )

    def as_df(rows):
        return pd.DataFrame(rows)

    if facility == "Entry Gates":
        df = as_df(DATA["gates"]).rename(columns={"id": "Gate", "zone": "Zone",
                                                  "serves": "Serves", "landmark": "Landmark"})
    elif facility == "Food Stalls":
        df = as_df(DATA["food_stalls"]).rename(columns={"name": "Stall", "cuisine": "Cuisine",
                                                        "zone": "Zone", "near": "Location"})
    elif facility == "Washrooms":
        df = as_df(DATA["washrooms"]).rename(columns={"zone": "Zone", "location": "Location",
                                                      "accessible": "Wheelchair OK"})
    elif facility == "First Aid":
        df = as_df(DATA["first_aid"]).rename(columns={"zone": "Zone", "location": "Location"})
    elif facility == "Parking":
        df = as_df(DATA["parking"]).rename(columns={"lot": "Lot", "for": "For",
                                                    "zone": "Zone", "capacity": "Capacity"})
    elif facility == "Emergency Exits":
        df = as_df(DATA["exits"]).rename(columns={"id": "Exit", "zone": "Zone", "note": "Location"})
    elif facility == "Water Refill (free)":
        df = as_df(DATA["water_stations"]).rename(columns={"zone": "Zone", "location": "Location"})
    elif facility == "Recycling Points":
        df = as_df(DATA["recycling_points"]).rename(columns={"zone": "Zone", "location": "Location"})
    elif facility == "ATMs":
        df = as_df(DATA["atms"]).rename(columns={"zone": "Zone", "location": "Location"})
    else:
        df = as_df(DATA["other"]["merchandise"]).rename(columns={"name": "Store", "zone": "Zone",
                                                                 "near": "Location"})

    # highlight user's own zone first
    if "Zone" in df.columns:
        df["_near_me"] = (df["Zone"] == zone)
        df = df.sort_values("_near_me", ascending=False).drop(columns="_near_me").reset_index(drop=True)
        in_zone = (df["Zone"] == zone).sum()
        if in_zone:
            st.success(f"\u2705 {in_zone} option(s) available in your zone (**{zone}**) \u2014 shown on top.")
        else:
            st.info(f"No {facility.lower()} in **{zone}** \u2014 nearest options listed below.")

    st.dataframe(df, use_container_width=True, hide_index=True)

# ================================================================= TAB 3: CROWD
with tab_crowd:
    st.subheader("Live crowd control room")
    st.caption("Simulated live feed (demo). In production this connects to gate "
               "sensors / turnstile counts / CCTV analytics.")

    if "crowd_seed" not in st.session_state:
        st.session_state.crowd_seed = 42
    if st.button("\U0001F504 Refresh live data"):
        st.session_state.crowd_seed = random.randint(0, 99999)

    rng = np.random.default_rng(st.session_state.crowd_seed)
    zones = DATA["zones"]
    caps = {"North Stand": 20000, "South Stand": 20000, "East Stand": 18000,
            "West Stand": 18000, "VIP Lounge": 6500}
    density = {z: int(rng.uniform(35, 98)) for z in zones}
    gate_queue = {g["id"]: int(rng.uniform(5, 45)) for g in DATA["gates"]}

    total_in = sum(int(caps[z] * density[z] / 100) for z in zones)
    busiest = max(density, key=density.get)
    calmest_gate = min(gate_queue, key=gate_queue.get)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fans inside", f"{total_in:,}")
    c2.metric("Capacity used", f"{int(total_in / DATA['stadium']['capacity'] * 100)}%")
    c3.metric("Busiest zone", busiest, f"{density[busiest]}% full")
    c4.metric("Fastest gate", f"Gate {calmest_gate}", f"~{gate_queue[calmest_gate]} min wait")

    st.markdown("#### Zone occupancy")
    zdf = pd.DataFrame({
        "Zone": zones,
        "Occupancy %": [density[z] for z in zones],
        "Status": ["\U0001F534 High" if density[z] > 85 else
                   ("\U0001F7E1 Medium" if density[z] > 60 else "\U0001F7E2 OK") for z in zones],
    })
    st.dataframe(
        zdf, use_container_width=True, hide_index=True,
        column_config={"Occupancy %": st.column_config.ProgressColumn(
            "Occupancy %", min_value=0, max_value=100, format="%d%%")},
    )

    st.markdown("#### Gate queues (minutes)")
    gdf = pd.DataFrame({"Gate": [f"Gate {g}" for g in gate_queue],
                        "Wait (min)": list(gate_queue.values())}).set_index("Gate")
    st.bar_chart(gdf)

    # ---- rule-based decision support (offline "AI recommendations")
    st.markdown("#### \U0001F9E0 Decision support \u2014 recommended actions")
    recs = []
    for z, d in density.items():
        if d > 85:
            calm = min(density, key=density.get)
            recs.append(f"\U0001F534 **{z}** is {d}% full \u2014 pause new entries, "
                        f"announce redirection towards **{calm}** concourse, deploy 2 extra stewards.")
        elif d > 60:
            recs.append(f"\U0001F7E1 **{z}** at {d}% \u2014 monitor closely; keep one standby steward.")
    slow_gates = [g for g, w in gate_queue.items() if w > 30]
    for g in slow_gates:
        recs.append(f"\u23F3 **Gate {g}** queue ~{gate_queue[g]} min \u2014 open extra lane, "
                    f"guide fans to **Gate {calmest_gate}** ({gate_queue[calmest_gate]} min).")
    if not recs:
        recs.append("\U0001F7E2 All zones and gates within safe limits. No action needed.")
    for r in recs:
        st.markdown("- " + r)

    st.caption("Recommendations are generated automatically from live thresholds "
               "(crowd > 85% = red, > 60% = amber; queue > 30 min = action).")

# ================================================================= TAB 4: MATCHES
with tab_match:
    st.subheader("Matches at this stadium")
    mdf = pd.DataFrame(DATA["matches"]).rename(
        columns={"match": "Match", "teams": "Teams", "date": "Date",
                 "time": "Kickoff", "status": "Status"})
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    final = DATA["matches"][-1]
    final_date = dt.date.fromisoformat(final["date"])
    days_left = (final_date - dt.date.today()).days
    if days_left > 0:
        st.info(f"\u26BD **{final['match']}** in **{days_left} day(s)** \u2014 "
                f"{final['date']} at {final['time']}. Gates open 11:00, come early!")
    elif days_left == 0:
        st.success(f"\u26BD **{final['match']} is TODAY!** Kickoff {final['time']}. "
                   "Gates are open \u2014 reach at least 2 hours early.")

# ================================================================= TAB 5: ACCESS + GREEN
with tab_access:
    left, right = st.columns(2)
    with left:
        st.subheader("\u267F Accessibility")
        a = DATA["accessibility"]
        for v in [a["wheelchair_ramps"], a["assistance_desk"], a["accessible_parking"],
                  a["sensory_room"], a["sign_language"]]:
            st.markdown("- " + v)
        st.markdown(f"- \U0001F64F {DATA['other']['prayer_room']}")
        st.markdown(f"- \U0001F50E Lost & Found: {DATA['other']['lost_and_found']}")
    with right:
        st.subheader("\u267B\uFE0F Sustainability")
        st.markdown("- Free water refill stations in every stand \u2014 "
                    "carry a reusable bottle.")
        for r in DATA["recycling_points"]:
            st.markdown(f"- Recycling bins: {r['location']} ({r['zone']})")
        st.markdown("- Use shuttle buses from Lot P3 to cut traffic and emissions.")

st.divider()
st.caption("StadiumSaathi \u00B7 PromptWars Challenge 4 \u00B7 Built with Python + Streamlit \u00B7 "
           "100% offline AI (no external API, no database)")
