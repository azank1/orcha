````markdown
# Orcha — Complete Design Handoff
# Source: Figma file UMMV4rfXHzESys9JcgeXB0 (partially built, migrating to Penpot)
# Generated: 2026-04-01
# Status: Full spec — covers all tokens, all completed Figma frames,
#         and all pending screens with pixel-precise build instructions.

---

## 1. DESIGN TOKENS

### 1.1 Color Palette

#### Brand Primary — "Sovereign Blue"
| Token                     | Hex       | Tailwind key              | Usage                                    |
|---------------------------|-----------|---------------------------|------------------------------------------|
| brand.primary.DEFAULT     | #3B6EF8   | blue-500                  | CTAs, focus rings, active states         |
| brand.primary.light       | #6B93FA   | blue-400                  | Agent badges, muted blue text            |
| brand.primary.dim         | #0A1F3D   | blue-950                  | Badge/bubble backgrounds                 |
| brand.primary.deep        | #060F3A   | blue-900                  | Darkest brand tint                       |
| brand.primary.hover       | #2251D6   | blue-600                  | Button hover/pressed                     |

#### Brand Secondary — "Precision Cyan"
| Token                     | Hex       | Tailwind key              | Usage                                    |
|---------------------------|-----------|---------------------------|------------------------------------------|
| brand.secondary.DEFAULT   | #00C8E8   | cyan-400                  | Live/streaming indicators, accent moments|
| brand.secondary.dim       | #002A30   | cyan-950                  | A2A badge backgrounds                    |
| brand.secondary.hover     | #009BB8   | cyan-500                  | Hover state                              |

#### Surface / Neutrals (dark-first, blue-tinted blacks)
| Token                     | Hex       | Tailwind key              | Usage                                    |
|---------------------------|-----------|---------------------------|------------------------------------------|
| surface.canvas            | #07070C   | zinc-950 (tinted)         | Root page background                     |
| surface.base              | #0D0D14   | zinc-900 (tinted)         | App shell, nav bars, left sidebar        |
| surface.elevated          | #13131E   | zinc-800 (tinted)         | Cards, right panel, tab bars             |
| surface.overlay           | #1A1A28   | zinc-700 (tinted)         | Agent cards, dropdowns, message bubbles  |
| surface.border            | #252535   | zinc-700                  | Default dividers, card outlines          |
| surface.borderLight       | #333348   | zinc-600                  | Input focus rings, active borders        |
| surface.muted             | #4A4A6A   | zinc-500                  | Placeholder text, disabled icons         |
| surface.subtle            | #6B6B8F   | zinc-400                  | Secondary labels, timestamps             |

#### Semantic
| Token                     | Hex       | Dim Hex   | Usage                                    |
|---------------------------|-----------|-----------|------------------------------------------|
| semantic.success          | #22C55E   | #052E16   | Done tasks, connected credentials        |
| semantic.warning          | #F59E0B   | #1C1400   | Pending states, interrupt badges         |
| semantic.error            | #EF4444   | #2D0A0A   | Failed tasks, auth errors                |
| semantic.info             | #3B82F6   | #0A1F3D   | Info toasts, neutral notes               |
| semantic.purple           | #A78BFA   | #1A0A3D   | Native agent badges                      |

#### Typography
| Token                     | Hex       | Usage                                    |
|---------------------------|-----------|------------------------------------------|
| text.heading              | #EEEEF2   | H1–H4, panel titles                      |
| text.body                 | #C4C4D4   | Body copy, chat messages                 |
| text.secondary            | #8888AA   | Labels, metadata, captions               |
| text.disabled             | #4A4A6A   | Placeholders, disabled states            |
| text.inverse              | #07070C   | Text on light/blue-filled surfaces       |
| text.brand                | #3B6EF8   | Brand name, inline links                 |
| text.accent               | #00C8E8   | Live status labels, streaming text       |

---

### 1.2 Spacing (4px base grid)
| Token       | rem     | px  |
|-------------|---------|-----|
| space.1     | 0.25rem | 4   |
| space.2     | 0.5rem  | 8   |
| space.3     | 0.75rem | 12  |
| space.4     | 1rem    | 16  |
| space.5     | 1.25rem | 20  |
| space.6     | 1.5rem  | 24  |
| space.8     | 2rem    | 32  |
| space.10    | 2.5rem  | 40  |
| space.12    | 3rem    | 48  |
| space.16    | 4rem    | 64  |

### 1.3 Border Radius
| Token        | px   | Usage                              |
|--------------|------|------------------------------------|
| radius.xs    | 4px  | Badges, small tags                 |
| radius.sm    | 6px  | Status badges, checklist rows      |
| radius.md    | 8px  | Buttons, agent cards, chips        |
| radius.lg    | 12px | Input bars, modal sections         |
| radius.xl    | 16px | Icon containers                    |
| radius.full  | 9999 | Pills, avatar dots                 |

### 1.4 Typography Scale
| Token           | Size | Weight    | Line-height | Usage                    |
|-----------------|------|-----------|-------------|--------------------------|
| type.display    | 48px | 700       | 56px        | Hero headings            |
| type.h1         | 36px | 700       | 44px        | Page titles              |
| type.h2         | 28px | 600       | 36px        | Section headings         |
| type.h3         | 20px | 600       | 28px        | Card / panel headers     |
| type.body.lg    | 16px | 400       | 24px        | Main body, subtitles     |
| type.body.md    | 14px | 400       | 22px        | Chat messages            |
| type.label      | 13px | 500       | 20px        | Buttons, nav labels      |
| type.caption    | 11px | 400 / 600 | 16px        | Metadata, log lines      |
| type.mono       | 13px | 400       | 20px        | Code, tool output        |

Font stack (sans): `'Geist', 'Inter', ui-sans-serif, system-ui`
Font stack (mono): `'Geist Mono', 'JetBrains Mono', ui-monospace`
Letter-spacing on ALL-CAPS labels: `+1.2px`

### 1.5 Shadow / Elevation
| Token          | Value                                      | Usage               |
|----------------|--------------------------------------------|---------------------|
| shadow.sm      | `0 1px 3px rgba(0,0,0,0.4)`               | Cards at rest       |
| shadow.md      | `0 4px 16px rgba(0,0,0,0.5)`              | Popovers, dropdowns |
| shadow.lg      | `0 8px 32px rgba(0,0,0,0.6)`              | Modals              |
| shadow.blue    | `0 0 20px rgba(59,110,248,0.25)`          | Active input glow   |
| shadow.cyan    | `0 0 12px rgba(0,200,232,0.2)`            | Streaming state     |

---

## 2. COMPONENT LIBRARY

### 2.1 Buttons
All buttons: height 40px, radius.md (8px), font type.label (13px/500)

| Variant    | Fill     | Text     | Border   | Hover fill |
|------------|----------|----------|----------|------------|
| Primary    | #3B6EF8  | #FFFFFF  | none     | #2251D6    |
| Secondary  | #13131E  | #3B6EF8  | #252535  | #1A1A28    |
| Ghost      | none     | #C4C4D4  | #252535  | #1A1A28    |
| Danger     | #2D0A0A  | #EF4444  | #3D1212  | #3D1010    |
| Accent     | #002A30  | #00C8E8  | #005060  | #003A42    |

### 2.2 Status Badges
All badges: height 26px, radius.xs (4-6px), font 11px/600, letter-spacing +0.6px
Padding: 0 10px

| Label    | Fill      | Text     | Border   |
|----------|-----------|----------|----------|
| MCP      | #0A1F3D   | #3B6EF8  | #1A3060  |
| A2A      | #002A30   | #00C8E8  | #005060  |
| Native   | #1A0A3D   | #A78BFA  | #2D1A60  |
| Active   | #052E16   | #22C55E  | #0A4A26  |
| Pending  | #1C1400   | #F59E0B  | #2D2000  |
| Failed   | #2D0A0A   | #EF4444  | #3D1212  |
| Running  | #0A1230   | #6B93FA  | #1A2248  |

### 2.3 Input Bar
- Height: 56px (chat home) / 52px (active session)
- Radius: 12px
- Fill: #13131E
- Border: 1px #333348
- Focus border: 1px #3B6EF8 + shadow.blue
- Placeholder: 14–15px Regular #4A4A6A
- Send button (child, right-inset 8px): 36–40px square, radius 8px, fill #3B6EF8, "↑" 16–18px Bold white

### 2.4 Message Bubbles
Max-width 560px, padding 14px 16px, radius 12px

| Variant      | Fill      | Border         | Text     |
|--------------|-----------|----------------|----------|
| User         | #0A1F3D   | 1px #3B6EF8@25%| #6B93FA  |
| Agent        | #13131E   | none           | #C4C4D4  |
| System event | #1A1A28   | 1px #252535    | #8888AA  |

System event: full chat-width minus 48px margins, radius 6px, 12px/500

### 2.5 Agent Cards (right panel)
- Size: (panel_width − 24px) × 54px, radius 8px
- Fill: #1A1A28, border 1px #252535
- Agent name: 13px/500 #C4C4D4, x:12, y:10
- Type badge: 38×20px, radius 4px (see badge table)
- Status dot: 8px circle, right-inset 20px, vertically centred
  - Running: #3B6EF8 | Done: #22C55E | Pending: #4A4A6A

### 2.6 Checklist Rows
- Size: (panel_width − 24px) × 36px, radius 6px, gap 6px, mx 12px

| State    | Fill      | Border             | Icon | Icon color | Text color |
|----------|-----------|--------------------|------|------------|------------|
| Done     | #052E16   | none               | ✓    | #22C55E    | #8888AA    |
| Running  | #0A1F3D   | 1px #3B6EF8@20%    | ◐    | #3B6EF8    | #C4C4D4    |
| Pending  | #1A1A28   | none               | ○    | #4A4A6A    | #8888AA    |
| Failed   | #2D0A0A   | 1px #EF4444@20%    | ✕    | #EF4444    | #8888AA    |

### 2.7 Meta Stats Grid (right panel)
- Container: (panel_width − 24px) × 88px, radius 8px, fill #1A1A28, border 1px #252535
- Layout: 2 × 2 grid, 2 columns × 2 rows
- Key label: 11px/400 #4A4A6A, y offset +0 within cell
- Value: 13px/600 #C4C4D4, y offset +14 within cell

---

## 3. COMPLETED SCREENS (built in Figma, recreate in Penpot)

---

### SCREEN A — Design Tokens Page
**Purpose:** Living reference page, not a user-facing screen.
**Canvas fill:** #07070C

#### Section 1 — Color Swatches
Title: "Orcha · Design Tokens" — 28px/700 #EEEEF2, x:40, y:20

Six groups rendered left-to-right with 108px column stride:
- Each swatch: 96×56px rect, radius 8px, filled with token color
- Token name below swatch: 10px/500 #6B6B8F
- Hex code below name: 10px/400 #4A4A6A
- Group label above row: 13px/600 #8888AA, letter-spacing +1.2px

Groups and their swatches:
```
Brand / Blue:   #3B6EF8  #6B93FA  #95B3FC  #2251D6  #1538A4  #060F3A
Accent / Cyan:  #00C8E8  #5DDDF2  #A3EDF8  #009BB8  #006E84
Surface:        #07070C  #0D0D14  #13131E  #1A1A28  #252535  #333348  #4A4A6A  #6B6B8F
Semantic:       #22C55E  #F59E0B  #EF4444  #3B82F6  #052E16  #2D0A0A
Typography:     #EEEEF2  #C4C4D4  #8888AA  #4A4A6A  #3B6EF8  #00C8E8
```

#### Section 2 — Typography Scale
Label column at x:40, specimen column at x:260
Eight rows (Display → Mono) as specified in token table 1.4.
Each row: meta label left (11px/400 #6B6B8F), specimen text right.

#### Section 3 — Button Components
Row at y:~1800, five buttons with 148px stride.
See component spec 2.1.

#### Section 4 — Status Badges
Row at y:~1960, seven badges with 92px stride.
See component spec 2.2.

---

### SCREEN B — Home / New Session
**Frame:** 1440 × 900px
**Canvas fill:** #07070C

#### Layer tree (bottom → top):
```
[Frame] Home — New Session  1440×900  fill:#07070C
  [Ellipse] Glow             700×500  x:370 y:100
      fill: RADIAL gradient center→edge
            stop0: rgba(59,110,248,0.07)
            stop1: rgba(7,7,12,0)
  [Frame]  Nav Bar           1440×56  x:0 y:0
      fill:#0D0D14 opacity:0.92
      border-bottom: 1px #252535
    [Text]   "Orcha"     x:24 y:16   18px/700 #EEEEF2
    [Ellipse] Accent dot     6×6   x:152 y:25   fill:#00C8E8
    [Frame]  My Workflows Btn 148×34  x:1252 y:11  r:7
        fill:#1A1A28  border:1px #252535
        layout: H-center
        [Text] "⚡  My Workflows"  13px/500 #C4C4D4
    [Frame]  Sign In Btn     88×34   x:1328 y:11  r:7
        fill:#3B6EF8
        layout: H-center
        [Text] "Sign In"  13px/600 #FFFFFF
  [Frame]  Icon Badge        64×64   x:688 y:200  r:16
      fill:#0A1F3D  border:1px rgba(59,110,248,0.35)
    [Text]   "◈"             30px/700 #3B6EF8  x:16 y:14
  [Text]   Headline          760×52  x:340 y:286
      "What can I help you orchestrate?"
      38px/700 #EEEEF2  align:center
  [Text]   Subheadline       560×48  x:440 y:350
      "I'm your SuperAgent — I discover, compose, and run agents
       to complete complex tasks end-to-end."
      16px/400 #8888AA  align:center
  [Frame]  Prompt Input      680×56  x:380 y:428  r:12
      fill:#13131E  border:1px #333348
    [Text]   Placeholder     x:18 y:19   15px/400 #4A4A6A
        "Describe a task for your agent hive..."
    [Frame]  Send Btn        40×40   x:630 y:8   r:8
        fill:#3B6EF8  layout:H-center
      [Text] "↑"  18px/700 #FFFFFF
  [Frame]  Sample Prompt ×4  166×36 each  y:508  r:8  gap:10px
      fill:#1A1A28  border:1px #252535  layout:H-center  px:10
      x positions: 380, 556, 732, 908
      texts (12px/400 #8888AA):
        "Check inbox for urgent emails"
        "Find senior engineer roles"
        "Research AI agent trends"
        "Security scan on my domain"
  [Text]   Gate note         280×20  x:580 y:562
      "Sign in required to start a session"
      12px/400 #4A4A6A  align:center
```

---

## 4. PENDING SCREENS — Full Build Specifications

---

### SCREEN C — Active Chat Session
**Frame:** 1440 × 960px, fill #07070C

#### 4.1 Left Sidebar — x:0, w:64, h:960
```
fill: #0D0D14
border-right: 1px #252535

[Text] "◈"           22px/700 #3B6EF8   x:20 y:18

[Frame] Nav icon × 3   40×40 each  x:12  r:8  gap:16
  y positions: 70, 126, 182
  [0] Chat  — fill:#0A1F3D  border:1px rgba(59,110,248,0.30)  [ACTIVE]
  [1] Workflows — fill:transparent
  [2] Settings  — fill:transparent
  icon emoji (18px) centred inside each
```

#### 4.2 Chat Header — x:64, y:0, w:1056, h:56
```
fill: #0D0D14
border-bottom: 1px #252535

[Text] "Gmail Inbox Management"   x:20 y:18   15px/600 #EEEEF2

[Frame] Status badge   76×24   x:226 y:16   r:6
    fill:#0A1F3D  border:1px rgba(59,110,248,0.30)
    layout:H-center
  [Text] "● running"   11px/500 #6B93FA

[Frame] Credentials Btn  124×32   x:912 y:12   r:7
    fill:#1A1A28  border:1px #333348
    layout:H-center
  [Text] "🔑  Credentials"   12px/500 #C4C4D4
```

#### 4.3 Chat Messages — x:84, y:72, gap:12
```
── Message 1 · User bubble ──
  x: 1056−560−20 = 476   w:560   r:12
  fill:#0A1F3D  border:1px rgba(59,110,248,0.25)
  padding: 14px 16px
  [Text] 14px/400 #6B93FA
  "Check my inbox for urgent emails, draft GitHub/Discord
   replies, and mark them as read."

── Message 2 · Agent bubble ──
  x:84  w:560   r:12
  fill:#13131E  padding:14px 16px
  [Text] 14px/400 #C4C4D4
  "Understood. I'm orchestrating a 4-step pipeline:
   1. Fetch emails (Gmail MCP)
   2. Classify urgency (SuperAgent LLM)
   3. Draft replies with context
   4. Mark as read
   Discovering agents now..."

── Message 3 · System event ──
  x:84  w:chatW−48(=1008)  h:auto  r:6
  fill:#1A1A28  border:1px #252535  padding:10px 14px
  [Text] 12px/500 #8888AA
  "✦  fetch_emails agent invoked — fetching 1 page from Gmail (max 100)"

── Message 4 · Agent bubble ──
  x:84  w:560   r:12
  fill:#13131E  padding:14px 16px
  [Text] 14px/400 #C4C4D4
  "Fetched 47 emails. Found 3 urgent threads: ..."

── Streaming indicator ──
  x:84  y:(last_msg_bottom + 16)
  layout: H, align-center, gap:8
  3× ellipse 7×7:  fill #3B6EF8 @ opacity 0.4 / 0.6 / 0.8
  [Text] "SuperAgent is thinking..."   13px/400 #4A4A6A
```

#### 4.4 Input Bar — x:84, y:896, w:1016, h:52
```
fill:#13131E  border:1px #333348  r:12
[Text placeholder] x:18 y:16   14px/400 #4A4A6A
    "Continue the conversation..."
[Frame] Send btn  36×36  x:970 y:8  r:8  fill:#3B6EF8
  [Text] "↑"  16px/700 #FFFFFF
```

#### 4.5 Right Panel — x:1120, w:320, h:960
```
fill:#0D0D14  border-left:1px #252535

── Panel header ──
  h:56  fill:#13131E  border-bottom:1px #252535
  [Text] "Session Details"   x:16 y:20   13px/600 #EEEEF2

── Tab bar ──
  y:56  h:40  fill:#13131E  border-bottom:1px #252535
  layout: H  px:8  gap:4
  5 tabs × 50px wide, h:32, r:6, layout:H-center
  Labels: Agents / Tasks / Logs / Meta / Artifacts
  Active (Agents): fill:#0A1F3D  text:#6B93FA  11px/500
  Inactive:        fill:none     text:#8888AA  11px/400

── Section label ──
  [Text] "ACTIVE AGENTS"  10px/600 #4A4A6A  letter-spacing:+1.2px
  x:16  y:108

── Agent cards (y:132, gap:8, mx:12) ──
  Card 1: fetch_emails   · MCP · status=running
  Card 2: classify_urgency · A2A · status=pending
  Card 3: draft_reply    · MCP · status=pending
  (see component spec 2.5 for card anatomy)

── Section label ──
  [Text] "TASK CHECKLIST"  10px/600 #4A4A6A  letter-spacing:+1.2px
  y: (last_agent_card_bottom + 16)

── Checklist rows (gap:6, mx:12) ──
  ✓ Fetch emails       — state: done
  ◐ Classify urgency   — state: running
  ○ Draft replies      — state: pending
  ○ Mark as read       — state: pending
  (see component spec 2.6 for row anatomy)

── Meta stats ──
  y: (last_task_row_bottom + 16)
  (see component spec 2.7)
  Values: Tokens:"1,842/8k"  Elapsed:"14s"  Credits:"$0.0024"  Model:"claude-sonnet"

── Save Workflow button ──
  [Frame] w:296  h:40  x:12  y:908  r:8  fill:#3B6EF8
  layout:H-center
  [Text] "💾  Save as Workflow"  13px/600 #FFFFFF
```

---

### SCREEN D — My Workflows
**Frame:** 1440 × 960px, fill #07070C

```
── Same left sidebar as Screen C ──

── Page header (x:64, y:0, w:1376, h:64) ──
  fill:#0D0D14  border-bottom:1px #252535
  [Text] "My Workflows"  x:24 y:20   24px/700 #EEEEF2
  [Frame] Search input  280×36  x:right−300 y:14  r:8
      fill:#13131E  border:1px #252535
    [Text] "Search workflows..."  13px/400 #4A4A6A  x:12 y:10

── Status tab bar (y:64, h:40) ──
  fill:#13131E  border-bottom:1px #252535  layout:H  px:16  gap:4
  Tabs: All | Active | Inactive | Scheduled
  Active tab: fill:#0A1F3D  text:#6B93FA  border-bottom:2px #3B6EF8
  Inactive: text:#8888AA

── Workflow cards grid (y:120, px:24, gap:12) ──
  Each card: w:100%−48px  h:72px  r:8
  fill:#13131E  border:1px #252535
  layout: H  align-center  padding:16px

  Card anatomy:
    [Left pulse dot]  8×8  fill:#22C55E (active) or #4A4A6A (inactive)
    [Workflow name]   14px/600 #EEEEF2  ml:12
    [Tag chips]       12px badges ml:8  (e.g. "Gmail" "MCP")
    [Last run]        12px/400 #8888AA  ml:auto
    [Status badge]    (Active/Inactive/Scheduled)
    [Actions]         icon buttons: View Logs | Run Again | Delete
                      16px icons  #8888AA  hover:#EEEEF2

  Sample cards:
    1. "Gmail Inbox Management"  Active    last run: 2 hrs ago
    2. "Weekly Security Scan"    Scheduled last run: Yesterday
    3. "Job Search Monitor"      Active    last run: 5 min ago
    4. "Competitor Research"     Inactive  last run: 3 days ago
```

---

### SCREEN E — Dev · Agent Library
**Frame:** 1440 × 960px, fill #07070C
**Access:** Dev mode only (gated in settings)

```
── Left sidebar (same as C) ──

── Page header (x:64, y:0, w:1376, h:64) ──
  [Text] "My Agents"  24px/700 #EEEEF2  x:24 y:20
  [Frame] "Register Agent" btn  148×36  x:right−164 y:14
      fill:#3B6EF8  r:8  layout:H-center
    [Text] "+ Register Agent"  13px/600 #FFFFFF

── Filter bar (y:64, h:48) ──
  fill:#13131E  border-bottom:1px #252535  layout:H  px:16  gap:12  align-center
  [Search input] 240×32  r:8  fill:#1A1A28  border:1px #252535
  [Filter chip] "Type: All"  ghost btn
  [Filter chip] "Status: All"  ghost btn

── Table header (y:112, h:44) ──
  fill:#07070C  border-bottom:1px #252535  layout:H  px:24  gap:0
  Columns with flex widths:
    Agent Name (flex:2)  |  Type (100px)  |  Status (100px)  |
    Tags (flex:1)  |  Registered (120px)  |  Actions (100px)
  Text: 11px/600 #4A4A6A  letter-spacing:+1.2px

── Table rows (y:156, h:56 each) ──
  border-bottom:1px #252535  layout:H  px:24  align-center
  Hover: fill:#13131E

  Row anatomy:
    Agent Name: [icon 24px circle fill:#0A1F3D] + name 14px/500 #EEEEF2 ml:10
    Type: [Badge MCP|A2A|Native]
    Status: [Badge Active|Pending|Failed]
    Tags: flex chips 11px #8888AA bg:#1A1A28 r:4 px:6
    Registered: 12px/400 #8888AA
    Actions: [Edit icon] [Metrics icon] [Deactivate icon]  gap:12  #4A4A6A

  Sample rows:
    1. gmail-mcp-agent    MCP    Active    ["email","gmail","oauth"]    2026-03-15
    2. web-scraper-a2a    A2A    Active    ["scraping","research"]      2026-03-20
    3. pdf-generator-mcp  MCP    Pending   ["docs","pdf"]               2026-03-30
```

---

### SCREEN F — Dev · Register Agent
**Frame:** 1440 × 960px, fill #07070C

```
── Left sidebar (same as C) ──

── Page header (x:64, y:0, w:1376, h:64) ──
  [Text] "Register Agent"  24px/700 #EEEEF2  x:24 y:20
  [Breadcrumb] "My Agents  /  Register"  12px/400 #8888AA  y:44

── Two-column layout (y:80) ──
  Left col:   w:540  x:88   (form)
  Right col:  w:540  x:688  (live preview card)
  Gap:        60px

  ── LEFT: Form ──
    Step indicator: "Step 1 of 2 — Upload emerge.yaml"
    12px/500 #8888AA  y:80

    [Frame] File drop zone  540×140  y:108  r:12
        fill:#13131E  border:2px dashed #333348
        layout: V-center  gap:8
      [Text] "📎"  32px
      [Text] "Drop emerge.yaml here or click to browse"  14px/400 #8888AA
      [Frame] Browse btn  120×34  r:8  fill:#1A1A28  border:1px #333348
        [Text] "Browse"  13px/500 #C4C4D4

    ── After file selected (state 2): ──
    [Frame] Selected file chip  540×44  y:108  r:8
        fill:#052E16  border:1px #0A4A26  layout:H  align-center  px:12
      [Text] "📄 gmail-mcp-agent.yaml"  13px/500 #22C55E
      [Text] "×"  18px #4A4A6A  ml:auto

    [Text] "Agent Information"  16px/600 #EEEEF2  y:168
    Form fields (each: label 12px/500 #8888AA + input 40px fill:#13131E border:1px #252535 r:8):
      - Agent Name     (readonly, parsed from yaml)
      - Description    (textarea h:72, readonly)
      - Protocol Type  (readonly, badge rendered)
      - Version        (readonly)
      - Auth Required  (readonly, Yes/No chip)

    [Frame] "Register Agent" CTA  540×44  y:bottom  r:8  fill:#3B6EF8
      layout:H-center
      [Text] "Register Agent"  14px/600 #FFFFFF

  ── RIGHT: Preview card ──
    [Frame] Agent preview card  540×auto  r:12
        fill:#13131E  border:1px #252535  padding:24px

      [Top row: icon + name + type badge]
        [Frame] icon bg  44×44  r:10  fill:#0A1F3D
          [Text] "⬡"  22px #3B6EF8
        [Text] agent name  16px/600 #EEEEF2  ml:12
        [Badge] MCP/A2A   ml:auto

      [Text] description  14px/400 #8888AA  mt:12

      [Divider] 1px #252535  my:16

      [Section] "Capabilities"  12px/600 #4A4A6A  letter-spacing+1.2px
        Tool chips (12px badges, fill:#1A1A28, border:#252535)
        e.g. "bulk_fetch_emails" "send_email" "mark_as_read"

      [Divider] 1px #252535  my:16

      [Section] "Auth Requirements"  12px/600 #4A4A6A
        [Row] "Google OAuth2"  12px/400 #8888AA  + required chip

      [Section] "emerge.yaml snippet" (collapsible)  mt:16
        [Code block] fill:#07070C  r:8  padding:12  font:mono 12px #6B93FA
```

---

### SCREEN G — Settings
**Frame:** 1440 × 960px, fill #07070C

```
── Left sidebar (same as C) ──

── Settings layout: Left nav (240px) + Content area (1136px) ──

  Left nav (x:64, w:240, h:960):
    fill:#0D0D14  border-right:1px #252535  pt:24  px:12

    Section label: "ACCOUNT"  10px/600 #4A4A6A  letter-spacing+1.2px  px:8
    Nav items (h:36, r:6, px:8, mb:2):
      Profile / API Keys / Billing
    Section label: "PLATFORM"  mt:16
      General / Appearance
    Section label: "DEVELOPER"  mt:16
      Developer Mode / Agent Registry
    Section label: "DANGER ZONE"  mt:16
      Delete Account (text:#EF4444)

    Active item: fill:#0A1F3D  text:#6B93FA
    Inactive: text:#8888AA  hover:fill:#1A1A28

  Content area (x:304, w:1112, pt:40, px:48):

    [Text] "Settings"  28px/700 #EEEEF2

    ── Profile section ──
      [Text] "Profile"  18px/600 #EEEEF2  mt:32
      [Divider] 1px #252535  mb:24
      [Avatar circle] 64×64  fill:#0A1F3D  border:2px #252535
        [Text] initials  22px/700 #3B6EF8
      Form fields: Display Name / Email (readonly) / each 440px wide

    ── Developer Mode section ──
      [Frame] dev mode card  100%  h:80  r:8  fill:#13131E  border:1px #252535  layout:H  align-center  px:20
        [Left]
          [Text] "Developer Mode"  14px/600 #EEEEF2
          [Text] "Register and host agents on Orcha"  12px/400 #8888AA  mt:4
        [Right, ml:auto]
          [Toggle] 44×24  r:12
            Off: fill:#252535  knob:#8888AA
            On:  fill:#3B6EF8  knob:#FFFFFF
      [Frame] warning chip  visible when toggled on  mt:8  r:6
          fill:#1C1400  border:1px #2D2000  layout:H  align-center  px:12  h:34
        [Text] "⚠  Developer mode grants access to agent registration and hosting."
               12px/400 #F59E0B

    ── Billing section ──
      [Frame] credits card  440×88  r:8  fill:#13131E  border:1px #252535  padding:20px
        [Text] "Credits Balance"  12px/500 #8888AA
        [Text] "$12.48"  32px/700 #EEEEF2  mt:4
        [Frame] "Top Up" btn  96×32  r:8  fill:#3B6EF8  layout:H-center  ml:auto
          [Text] "Top Up"  13px/600 #FFFFFF
```

---

### SCREEN H — Credentials Modal
**Frame:** 480 × auto (modal overlay over active session)
**Overlay:** #07070C @ 70% opacity covering full viewport

```
[Frame] Modal  480×auto  centered  r:12
    fill:#13131E  border:1px #252535
    shadow.lg: 0 8px 32px rgba(0,0,0,0.6)

  ── Modal header ──
    layout:H  align-center  px:20  h:56  border-bottom:1px #252535
    [Frame] icon bg  36×36  r:8  fill:#0A1F3D
      [Text] "🔑"  16px
    [Text block] ml:12
      [Text] "Credentials"  15px/600 #EEEEF2
      [Text] "Email Inbox Management"  12px/400 #8888AA  mt:2
    [Text] "×"  18px/400 #8888AA  ml:auto  cursor:pointer

  ── Status banner ──
    mx:16  mt:16  h:40  r:8
    fill:#052E16  border:1px #0A4A26  layout:H  align-center  px:12
    [Dot] 8×8 fill:#22C55E
    [Text] "All required credentials connected (2/2 total)"  13px/500 #22C55E  ml:8

  ── Credential rows (mx:16 mt:12 gap:10) ──
    Each row: w:448  h:72  r:8  fill:#1A1A28  border:1px #252535  padding:14px 16px

    Row anatomy:
      [Row 1] Top line: layout:H align-center
        [Text] credential name  13px/600 #EEEEF2
        [Frame] "REQUIRED" badge  h:20  r:4  fill:#1A1A28  border:1px #333348
          [Text] "REQUIRED"  10px/600 #8888AA  letter-spacing+0.8px
        [ml:auto, layout:H gap:8]
          [Frame] status btn  88×28  r:6
              Connected: fill:#052E16  border:#0A4A26  text:#22C55E
              Missing:   fill:#2D0A0A  border:#3D1212  text:#EF4444
            [Text] "✓ Connected" or "✗ Missing"  11px/600
          [Icon] edit pencil   16px #4A4A6A  hover:#C4C4D4
          [Icon] trash bin     16px #4A4A6A  hover:#EF4444
      [Row 2] description text  11px/400 #8888AA  mt:6

    Credential 1: "Aden Platform"  REQUIRED
        desc: "API key from the Developers tab in Settings"
        status: Connected ✓
    Credential 2: "google"  REQUIRED
        desc: "Google OAuth2 access token — used for Gmail, Calendar, Sheets, and Docs"
        status: Connected ✓

  ── Input area (shown when status=Missing) ──
    mx:16  mt:4
    [Input] 448×40  r:8  fill:#0D0D14  border:1px #333348  pl:12
        placeholder: "Paste API key..."  13px/400 #4A4A6A
    [Toggle row] layout:H align-center mt:8
      [Toggle] 36×20
      [Text] "Save permanently for all sessions"  12px/400 #8888AA  ml:8

  ── Footer ──
    px:16  py:16  border-top:1px #252535  mt:16
    [Frame] Done btn  w:100%  h:44  r:8  fill:#3B6EF8  layout:H-center
      [Text] "Done"  14px/600 #FFFFFF
```

---

## 5. NEXT STEPS — Active Chat Session (Screen C)

The Active Chat Session is the most complex screen and is the immediate priority.
Build order within the frame:

```
Step 1  Root frame          1440×960  fill:#07070C
Step 2  Left sidebar        x:0   w:64   h:960  (spec §4.1)
Step 3  Chat area root      x:64  w:1056 h:960
Step 4    Chat header       x:0   h:56   (spec §4.2)
Step 5    Message bubble 1  User — right-aligned (spec §4.3)
Step 6    Message bubble 2  Agent — left-aligned
Step 7    Message bubble 3  System event — full-width
Step 8    Message bubble 4  Agent — left-aligned
Step 9    Streaming dots    3 ellipses + label (spec §4.3)
Step 10   Input bar         x:20 y:H−72 (spec §4.4)
Step 11 Right panel root    x:1120 w:320 h:960 (spec §4.5)
Step 12   Panel header      h:56
Step 13   Tab bar           h:40, 5 tabs, active=Agents
Step 14   "ACTIVE AGENTS" label
Step 15   Agent card × 3   (fetch_emails, classify_urgency, draft_reply)
Step 16   "TASK CHECKLIST" label
Step 17   Checklist rows × 4  (done/running/pending/pending)
Step 18   Meta stats grid
Step 19   Save Workflow CTA  pinned to panel bottom
```

SSE event → UI mutation map (wire after static layout is built):
```
agent_start      → add agent card, dot=#3B6EF8 pulsing
agent_complete   → dot → #22C55E, badge state → Active
tool_call        → append entry to Logs tab
tool_result      → append result preview to Logs tab
checklist_update → mutate row state (pending→running→done/failed)
interrupt        → add card to Interrupts tab + warning badge on tab pill
token_usage      → update Meta grid live
artifact         → add file card to Artifacts tab
message          → stream chars into agent bubble
session_end      → header status badge → "complete"/"failed"
```

Gateway API calls from this screen:
```
POST   /api/v1/sessions                     ← on mount
GET    /api/v1/sessions/:id/stream          ← EventSource, persistent
POST   /api/v1/sessions/:id/message         ← on send
POST   /api/v1/sessions/:id/interrupt/:iid  ← on interrupt resolve
POST   /api/v1/credentials                  ← from credentials modal
POST   /api/v1/workflows                    ← on Save Workflow click
```

---

## 6. PENPOT MIGRATION NOTES

Penpot equivalents for Figma concepts used in this spec:

| Figma concept          | Penpot equivalent                          |
|------------------------|--------------------------------------------|
| Auto layout            | Flex layout (Grid/Flex in Penpot design)   |
| Fill container         | "Fill" sizing mode on flex children        |
| Hug contents           | "Fit content" sizing mode                  |
| Stroke (inside)        | Border with inside alignment               |
| Opacity on fill        | Fill opacity slider per fill stop          |
| Radial gradient fill   | Radial gradient fill (same concept)        |
| Frame clip content     | "Clip content" toggle on container         |
| Component              | Main component (Penpot 2.x)               |
| Variant                | Component variant in Penpot 2.x            |
| Local style            | Design token / shared library in Penpot    |

Font note: If 'Geist' is unavailable in your Penpot instance,
use 'Inter' as the direct substitute across all type styles.
All weight/size/tracking values remain identical.
````

