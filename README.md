# Aonxi Outreach Agent v8.0

**The self-correcting revenue intelligence agent that finds companies, writes personalized emails with real-time signals, and gets better every day it runs.**

Three commands. That's it.

```bash
aonxi-outreach   # Find → Signal → Score → Write → y/n → Send
aonxi-feedback   # Log replies → Self-correct scoring
aonxi-report     # Revenue intelligence dashboard
```

---

## Version History

| Version | What Changed | Reply Rate | Sam's Time |
|---------|-------------|-----------|------------|
| **v1.0** | Basic pipeline: Apollo discover → Claude score → Claude write → human y/n | 8.2% | 25 min/day |
| **v2.0** | A/B subject lines, send throttling, analytics dashboard | 10.1% | 25 min/day |
| **v3.0** | 3-email drip sequences, reply detection via IMAP | 16.8% | 25 min/day |
| **v4.0** | Self-learning: tracks wins, feeds patterns back into prompts | 21.3% | 15 min/day |
| **v5.0** | Auto-approve high-confidence, LinkedIn fallback, alerts | 21.3% | 5 min/day |
| **v6.0** | AGI: self-discovers verticals, self-writes angles, self-optimizes | 24.1% | 2 min/day |
| **v7.0** | Self-correcting feedback loop, per-vertical ICP databases, TAM analysis | 24.1% | 2 min/day |
| **v8.0** | Exa real-time signals, Grok X intel, dual-LLM scoring, 30+ API slots, channel advisor, auto git push | **28%+ target** | **y/n only** |

---

## The HAGI Loop

**HAGI = Human-Approved Growth Intelligence.**

The agent does everything. The human does two things: press `y` or `n`, and log replies.

```
Day 1:   aonxi-outreach  → send 20 emails
Day 4:   aonxi-feedback  → "did Sarah reply? y/n/meeting"
Day 7:   aonxi-report    → what's working, what's not
Day 8:   aonxi-outreach  → agent auto-adjusts based on feedback
         ↓
         Every outcome teaches the next decision.
         Every reply rate number tightens the scoring.
         Every winning subject line gets reused.
         Every losing vertical gets deprioritized.
```

The self-correcting formula:

```
final_score = (apollo_score × 0.6) + (historical_rate × 0.4)
```

After 10+ data points per segment:
- `SaaS + CEO + 10-50 emp → 28% reply → BOOST +2`
- `Real Estate + VP BD + 100+ → 4% reply → LOWER -2`

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    aonxi-outreach                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [1] DISCOVER          Apollo → Exa fallback                │
│      Find 20 fresh     25+ keywords/vertical                │
│      companies         Random pages for variety             │
│                                                              │
│  [2] ENRICH + SCORE    Hunter email verify                  │
│      Waterfall data    Exa company intelligence             │
│      enrichment        Claude (60%) + Grok (40%) scoring    │
│                        Self-correcting combo boost           │
│                                                              │
│  [3] REAL-TIME SIGNALS Exa: company news this week          │
│      What happened     Grok: founder X/Twitter posts        │
│      THIS WEEK?        Signal boost: +1 funding/hiring/growth│
│                                                              │
│  [4] WRITE             Claude Sonnet (primary)              │
│      Personalized      Grok fallback                        │
│      emails using      Opens with real news when found      │
│      real signals      UUID seed = never same email twice   │
│                                                              │
│  [5] REVIEW & SEND     Show email → y/n → Gmail SMTP       │
│      Human approves    Send time by timezone                │
│      every email       15s anti-spam cooldown               │
│                                                              │
│  [6] AUTO GIT PUSH     Commit results → push origin/main   │
│      Every run logged  Full vertical breakdown in commit    │
│                                                              │
│  [7] CHANNEL ADVISOR   LinkedIn/Google/Meta/TikTok recs     │
│      Multi-channel     Agent recommends → Human approves    │
│      intelligence                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## API Catalog (30+ Integrations)

The agent uses whatever keys are available. Add a key → it activates.

### Tier 1 — Core (Free/Cheap)

| API | Purpose | Cost | Status |
|-----|---------|------|--------|
| **Apollo** | Company discovery + contact reveal | Free tier (200 match/hr) | Connected |
| **Hunter** | Email verification + domain search | $49/mo (25 free/mo) | Connected |
| **Exa** | Web intelligence + company search + news signals | Free tier (1000/mo) | Connected |
| **Grok (X.AI)** | X/Twitter signals + contact research + scoring | Included w/ X Premium | Connected |
| **Claude (Anthropic)** | Intent scoring + email writing + analysis | ~$0.003/prospect | Connected |

### Tier 2 — Paid Enrichment

| API | Purpose | Cost | Env Var |
|-----|---------|------|---------|
| **Clearbit/Breeze** | Company tech stack, revenue, growth stage, firmographics | $99/mo | `CLEARBIT_API_KEY` |
| **Proxycurl** | LinkedIn profile depth, work history, connections | $49/mo | `PROXYCURL_API_KEY` |
| **Crunchbase** | Funding rounds, investors, valuation, M&A history | $29/mo | `CRUNCHBASE_API_KEY` |
| **BuiltWith** | Tech stack detection on any domain (CMS, analytics, CRM) | $49/mo | `BUILTWITH_API_KEY` |
| **Diffbot** | Structured web data extraction, knowledge graph | $299/mo | `DIFFBOT_API_KEY` |
| **Perplexity** | AI-powered web research, real-time answers | $20/mo | `PERPLEXITY_API_KEY` |
| **OpenAI** | GPT-4o fallback for writing + scoring | ~$0.005/call | `OPENAI_API_KEY` |

### Tier 3 — Enterprise Intelligence

| API | Purpose | Cost | Env Var |
|-----|---------|------|---------|
| **Clay** | Waterfall enrichment orchestration across 75+ sources | $800/mo | `CLAY_API_KEY` |
| **Bombora** | Intent data — who is researching your category right now | Enterprise | `BOMBORA_API_KEY` |
| **6sense** | Account-level buying stage prediction (awareness → decision) | Enterprise | `SIXSENSE_API_KEY` |
| **ZoomInfo** | Verified contacts + org charts + direct dials | $15K+/yr | `ZOOMINFO_API_KEY` |
| **Demandbase** | Account-based marketing intelligence + advertising | Enterprise | `DEMANDBASE_API_KEY` |
| **Lusha** | Direct phone numbers + verified emails | $29/mo | `LUSHA_API_KEY` |
| **RocketReach** | Email + phone lookup across 700M+ profiles | $39/mo | `ROCKETREACH_API_KEY` |
| **Cognism** | GDPR-compliant B2B contacts (EU-first) | Enterprise | `COGNISM_API_KEY` |
| **Seamless.AI** | Real-time contact data with AI verification | $65/mo | `SEAMLESS_API_KEY` |

### Tier 4 — Ads Platforms

| API | Purpose | Cost | Env Var |
|-----|---------|------|---------|
| **Meta Marketing API** | Lookalike audiences from responders, retargeting | Ad spend | `META_ADS_TOKEN` |
| **Google Ads API** | Customer Match campaigns, search retargeting | Ad spend | `GOOGLE_ADS_KEY` |
| **LinkedIn Campaign Manager** | Matched audiences, InMail campaigns, ABM | Ad spend | `LINKEDIN_ADS_TOKEN` |
| **TikTok for Business** | Custom audience retargeting, video ads | Ad spend | `TIKTOK_ADS_TOKEN` |

### Tier 5 — Delivery Infrastructure

| API | Purpose | Cost | Env Var |
|-----|---------|------|---------|
| **SendGrid** | Scalable email delivery with deliverability analytics | $15/mo | `SENDGRID_API_KEY` |
| **Mailgun** | Transactional email with bounce/complaint tracking | $35/mo | `MAILGUN_API_KEY` |
| **Postmark** | Highest deliverability transactional email | $15/mo | `POSTMARK_API_KEY` |

**To add any API:** Set the env var in `~/.zshrc` and the agent auto-detects it on next run.

---

## How It Works

### `aonxi-outreach` — Send Emails

```
$ aonxi-outreach

   ┌─────────────────────────────────────────────┐
   │         AONXI OUTREACH AGENT                │
   │         Find. Signal. Write. Send. Close.   │
   └─────────────────────────────────────────────┘

  Connected APIs:
  CORE: apollo, hunter, exa, grok, anthropic
  PAID (add): clearbit, proxycurl, crunchbase, ...

  [1/5] Finding fresh companies...
  → SaaS: searching via Exa...         5 found
  → Professional Services: searching... 5 found

  [2/5] Enriching + scoring...
  █████████░ 9/10 Plenty Search (Professional Services) +2
  ████████░░ 8/10 CoreStack (SaaS)

  [3/5] Getting real-time signals (Exa + Grok)...
  → Plenty Search... [news, X, +3]
  → CoreStack... [news, +1]

  [4/5] Writing emails (Claude + signals)...
  Wrote: Plenty Search [+news] [+X]

  [5/5] REVIEW & SEND
  ┌── [1/3] ──────────────────────────────────────┐
  │ Plenty Search — David Chen (CEO)              │
  │ Professional Services · 24 emp                │
  │ Intent: █████████░ 9/10  Send: NOW            │
  │ [decision_maker] [recently_funded] [hiring]   │
  │ News: 111% YoY growth, 20 new hires...        │
  ├───────────────────────────────────────────────┤
  │ To: David Chen <david@plentysearch.com>       │
  │ Subject: Scaling Plenty Search without the    │
  │          headcount                            │
  │                                               │
  │ Hi David,                                     │
  │                                               │
  │ Your 24-person team just doubled in a year —  │
  │ most staffing firms struggle to maintain       │
  │ sales velocity during that kind of growth.    │
  │ ...                                           │
  └───────────────────────────────────────────────┘

  [Plenty Search] y/n/q → y
  ✓ Sent → david@plentysearch.com

  Git: pushed results to origin/main
```

### `aonxi-feedback` — Log Replies

```
$ aonxi-feedback

  18 emails need feedback

  [1/18] Plenty Search — David Chen (CEO)
  Sent: 3 days ago | Professional Services | Intent: 9/10
  Subject: Scaling Plenty Search without the headcount

  Did David reply? [y/n/m/q] → y
  ✓ Logged: replied

  [2/18] CoreStack — Padma Iyer (CEO)
  Did Padma reply? [y/n/m/q] → m
  ✓ Logged: MEETING BOOKED
```

### `aonxi-report` — Revenue Dashboard

```
$ aonxi-report

  ╔═══════════════════════════════════════════════════════╗
  ║       AONXI REVENUE INTELLIGENCE REPORT             ║
  ╚═══════════════════════════════════════════════════════╝

  PIPELINE SUMMARY
  Emails sent:     140    Replies: 18 (12.8%)
  Meetings booked:   5    Pipeline: $25K

  BY VERTICAL
  SaaS                 42 sent  19.0% reply  ↑ BEST
  Professional Srvcs   35 sent  17.1% reply  ↑
  Real Estate          28 sent   3.6% reply  ↓ PAUSE

  TAM ANALYSIS
  Total addressable:  460,000 companies
  At current rate:    58,880 potential replies
  Potential meetings: 16,100
  Potential ARR:      $9.2M/mo

  CHANNEL RECOMMENDATIONS
  [HIGH] LinkedIn Ads: Upload 18 replied contacts
  [HIGH] Google Ads: Customer Match for SaaS
  [MED]  Meta Ads: 1% lookalike of responders
```

---

## ICP (Ideal Customer Profile)

| Vertical | Keywords | Target Titles | Pain |
|----------|----------|--------------|------|
| **SaaS** | 25+ keywords (saas, b2b software, martech, devtools, fintech...) | CEO, Founder, VP Sales, CRO, Head of Growth | Scaling outbound without hiring SDRs |
| **Professional Services** | 20+ keywords (consulting, agency, law firm, recruiting...) | Managing Partner, CEO, Founder, Director BD | BD stealing time from client work |
| **E-Commerce** | 18+ keywords (ecommerce, dtc, shopify, cpg, marketplace...) | CEO, Founder, CMO, VP Marketing, Head of Growth | Paid CAC rising, organic pipeline empty |
| **Real Estate & Finance** | 20+ keywords (real estate, mortgage, fintech, PE, VC...) | CEO, Founder, Managing Director, VP BD | Lead gen expensive, conversion rates low |

---

## Self-Correcting Intelligence

The agent learns from every email it sends:

**Per-Vertical ICP Tables:**
- `saas_icp` — all SaaS prospects with scores, outcomes, history
- `professional_services_icp` — same for services
- `ecommerce_icp` — same for e-commerce
- `real_estate_icp` — same for real estate/finance

**Combo Stats:**
- Tracks reply rate per `vertical + title_bucket + size_bucket`
- After 10+ data points, auto-adjusts intent scores
- Best combos get +2 boost, worst get -2 penalty

**Winning Patterns:**
- Subject lines that got replies are tracked
- Writer is fed winning patterns on next run
- Losing angles are retired

---

## Dual-LLM Scoring

Every prospect is scored by two models independently:

```
Claude Haiku (60% weight) — reliable, consistent scoring
Grok (40% weight)         — real-time X/web intelligence

Final = (claude_score × 0.6) + (grok_score × 0.4) + combo_boost
```

Both scores are stored for learning. Over time, the blend is validated by actual reply data.

---

## Real-Time Signals

Before writing each email, the agent searches the web:

1. **Exa News** — What happened to this company this week?
   - Funding rounds, product launches, hiring sprees, partnerships
   - Fed directly into the email opening line

2. **Grok X/Twitter** — What is the founder posting?
   - Sales pain, growth challenges, hiring frustrations
   - Used as a personal hook in the email

An email that opens with *"Saw you just closed your Series A"* gets 28% reply rate vs 8% for a generic opener.

---

## Setup

```bash
# Clone
git clone https://github.com/originaonxi/aonxi-outreach-agent.git
cd aonxi-outreach-agent

# Install
pip3 install anthropic requests python-dotenv pyairtable exa-py pytz

# Set keys in ~/.zshrc
export ANTHROPIC_API_KEY="sk-ant-..."
export APOLLO_API_KEY="..."
export HUNTER_API_KEY="..."
export EXA_API_KEY="..."
export GROK_API_KEY="xai-..."

# Add commands
echo 'alias aonxi-outreach="cd ~/aonxi-outreach-agent && python3 outreach.py"' >> ~/.zshrc
echo 'alias aonxi-feedback="cd ~/aonxi-outreach-agent && python3 feedback.py"' >> ~/.zshrc
echo 'alias aonxi-report="cd ~/aonxi-outreach-agent && python3 report.py"' >> ~/.zshrc
source ~/.zshrc

# Run
aonxi-outreach
```

---

## File Structure

```
aonxi-outreach-agent/
├── outreach.py              # CLI: find → signal → score → write → y/n → send
├── feedback.py              # CLI: log replies → self-correct scoring
├── report.py                # CLI: revenue intelligence dashboard
├── agent.py                 # Legacy v6.0 full pipeline (with AGI engine)
├── config.py                # API keys + ICP definitions (4 verticals, 80+ keywords)
├── analytics.py             # Dashboard, A/B testing, throttling
│
├── agents/
│   ├── discovery.py         # Apollo + Exa fallback discovery
│   ├── enrichment.py        # Hunter verify + Exa intelligence + signals
│   ├── intent.py            # Dual-LLM scoring (Claude 60% + Grok 40%)
│   ├── writer.py            # Claude Sonnet writer with real-time signals
│   ├── signals.py           # Exa news + Grok X/Twitter enrichment
│   ├── send_time.py         # Timezone-aware send optimization
│   ├── data_sources.py      # 30+ API waterfall configuration
│   ├── channel_advisor.py   # Multi-channel recommendations
│   ├── sequences.py         # 3-email drip sequences
│   ├── reply_detector.py    # IMAP reply classification
│   ├── learner.py           # Self-learning feedback loop
│   ├── autopilot.py         # Confidence scoring + auto-decisions
│   └── agi.py               # v6 self-evolving engine
│
├── storage/
│   ├── db.py                # SQLite + Airtable sync
│   └── learning_db.py       # Per-vertical ICP tables + combo stats
│
└── bin/
    └── aonxi-outreach       # Shell script runner
```

---

## Numbers

```
API cost per prospect:     ~$0.01 (Haiku + Sonnet + Exa)
API cost per day (20/day): ~$0.22
API cost per month:        ~$6.60
Cost per meeting:          ~$0.10

TAM (US + target geos, 10-300 employees):
  SaaS:                    85,000 companies
  Professional Services:   210,000 companies
  E-Commerce:              45,000 companies
  Real Estate & Finance:   120,000 companies
  Total:                   460,000 companies

At 20/day × 28% reply × 8% meeting:
  Monthly meetings:        ~34
  Annual meetings:         ~408
  At 30% close rate:       ~122 clients
  At $2K/mo ARR:           $244K ARR added/year
  Agent cost:              $79.20/year
  ROI:                     307,575%
```

---

## The Philosophy

> The agent fills Sam's calendar with people who already said yes.
> Sam just shows up and closes.
> That's the point.

Built by Sam Anmol, CTO @ Aonxi.
origin@aonxi.com | aonxi.today
