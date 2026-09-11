# UI/UX Design Brief — StadiumSaathi

## 1. Executive Summary & Design Philosophy
StadiumSaathi is engineered for extreme high-density sports environments (80,000+ attendees at MetLife Stadium during FIFA World Cup 2026). At such scale, cellular bandwidth collapses, battery life is conserved aggressively, crowd noise is deafening, and attendees span dozens of nationalities and native languages.

The design philosophy is **Instantaneous, High-Contrast, Multilingual, and Resilient**:
- **Zero latency:** All views, chat queries, and table filters execute locally within milliseconds.
- **Multilingual first:** Native trilingual interface supporting English, Hindi (Devanagari), and colloquial Hinglish seamlessly.
- **Accessibility by default:** Built-in high-contrast mode, dynamic base-font scaling, screen-reader accessible tabular alternatives for visual charts, and physical facility locators for accessibility services.
- **Dual Surface:** Responsive web interface for mobile/tablet/desktop browsers (via Streamlit) and headless terminal CLI for kiosk automation, field-steward terminals, and headless verification.

---

## 2. Information Architecture & Navigation

```
┌────────────────────────────────────────────────────────────────────────┐
│                          StadiumSaathi Header                          │
│  🏟️ StadiumSaathi — Smart Stadium & Tournament Operations Assistant    │
│  New York New Jersey Stadium (MetLife) · Capacity 82,500               │
│  [Pill: Works fully offline · No API · Multilingual · Accessible]      │
└────────────────────────────────────────────────────────────────────────┘
│
├── Sidebar: User Settings & Accessibility Toggles
│   ├── 🌐 Language / भाषा (Select: English | हिंदी (Hindi) | Hinglish)
│   ├── 📍 I am currently near (Select: North Stand | South Stand | East Stand | West Stand | VIP Lounge)
│   ├── ♿ Accessibility
│   │   ├── High contrast mode (Toggle: True/False)
│   │   └── Large text (Toggle: True/False)
│   └── System Info & Privacy Disclaimer (Zero PII collected)
│
└── Main Surface (5 Tabbed Panes)
    ├── Tab 1: 💬 AI Fan Assistant
    │   ├── Quick Suggestion Chips (Localized 4-button quick prompt bar)
    │   ├── Interactive Chat History (Scrollable conversational bubble list)
    │   ├── Chat Input Bar (`st.chat_input` with 300-char limit)
    │   └── "🧹 Clear chat" action button
    │
    ├── Tab 2: 🗺️ Navigate Stadium
    │   ├── Facility Category Selector (Dropdown: 10 amenity categories)
    │   ├── Contextual Proximity Banner (Highlights items in active user zone)
    │   └── Sortable, Searchable Facility Dataframe (Screen-reader friendly)
    │
    ├── Tab 3: 👥 Crowd Dashboard (Organizers)
    │   ├── 4 Summary Metrics (Fans inside, Capacity used %, Busiest zone, Fastest gate)
    │   ├── Zone Occupancy Progress Table (Green / Amber / Red status tags)
    │   ├── Gate Queues Bar Chart + Expandable Table Alternative
    │   ├── 🧠 Decision Support — Recommended Actions (Rule-evaluated dispatch items)
    │   └── "🔄 Refresh live data" simulation button
    │
    ├── Tab 4: 📅 Matches
    │   ├── Tournament Match Schedule Dataframe (Teams, Dates, Kickoff, Status)
    │   └── Final Match Countdown Alert Card (Days-to-match or Game-Day banner)
    │
    └── Tab 5: ♿ Accessibility & ♻️ Green
        ├── Left Column: Accessibility Services (Wheelchair, Sensory room, Sign language, Lost & Found)
        └── Right Column: Sustainability & Transit (Water refill stations, Recycling points, Shuttles)
```

---

## 3. Visual System & Theming Specifications

### 3.1 Color Palette
- **Standard Mode:**
  - Hero Header: Linear gradient `linear-gradient(105deg, #0b1f3a 0%, #123c6b 55%, #1b6ca8 100%)`
  - Pill Badge: Background `#ffd447`, Foreground `#123c6b`
  - Base Font Size: `16px`
  - Body Background: Streamlit neutral theme with dark/light auto-adaptation
- **High-Contrast Mode (A11y):**
  - Hero Header: Solid `#000000` with 3px `#ffff00` border
  - Pill Badge: Background `#ffff00`, Foreground `#000000`
  - Chat Bubble Outlines: High-visibility distinct contrast borders
  - Chart Elements: Monochromatic/high-visibility distinct bar fills

### 3.2 Typography & Sizing
- **Standard Base Font:** `16px`
- **Large Text Mode:** `19px` applied dynamically to `html, body, [class*="css"]`
- **Hero Title:** `2.0rem`, font-weight 700, letter-spacing `0.5px`
- **Section Headers:** `1.25rem` to `1.5rem` with contextual emoji markers for quick recognition

---

## 4. Interaction Behavior & State Handling

### 4.1 Chat Assistant (`Tab 1`)
- **Pre-populated Chips:** Clicking a chip sets `st.session_state.pending_query` and immediately renders the answer without requiring manual keyboard input.
- **Empty & Erroneous Input:** Sanitizer collapses whitespace and strips control codes; empty queries trigger a friendly localized fallback rather than an unhandled exception.
- **Session Reset:** "Clear chat" cleanses `st.session_state.messages` and triggers `st.rerun()`.

### 4.2 Facility Wayfinding (`Tab 2`)
- **Zone Prioritization:** When an attendee selects their seating zone in the sidebar, facilities in that zone are sorted to the top of the table. A green notification badge displays the count of in-zone facilities.
- **Fallback Display:** If no matching facilities exist in the selected zone (e.g. specialized medical triage), out-of-zone facilities are listed below with an informational notice.

### 4.3 Live Crowd Control Room (`Tab 3`)
- **Threshold Rules:**
  - Red Alert (> 85% occupancy): Pauses gate entry, triggers steward dispatch, suggests concourse redirection.
  - Amber Alert (> 60% occupancy): Suggests close monitoring and standby stewards.
  - Gate Bottleneck (> 30 min queue): Suggests opening additional security lanes and redirecting attendees to calmest gate.
- **Simulation Control:** "Refresh live data" regenerates pseudorandom seed, providing realistic operator training scenarios.

### 4.4 Terminal CLI (`stadium-saathi`)
- Command: `stadium-saathi --query "<text>" [--lang <en|hi|hn>] [--zone <zone>]`
- Output: Structured markdown response directly to stdout, exiting with return code 0.
