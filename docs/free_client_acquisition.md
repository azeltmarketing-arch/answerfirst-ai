# Free Client Acquisition Methods — AnswerFirst AI

This document details every free method being used to acquire clients, with setup instructions, automation potential, and expected results.

---

## ACTIVE FREE CHANNELS

### 1. Google Maps Scraping ✅ LIVE
**Status:** Active  
**Cost:** $0  
**Automation:** 95%

**What it does:**
- Scrapes HVAC and roofing contractors from Google Maps in target cities
- Extracts business name, phone, website, address, rating, review count
- Enriches with owner names and personalization hooks via AI

**Setup:**
1. Run `python leads/google_maps_scraper.py`
2. Leads are saved to CSV in `leads/` folder
3. Dashboard automatically imports leads

**Expected Results:**
- 50-100 leads per city per query
- 5-10% response rate from cold outreach
- 2-5% conversion to demo
- 1-3% close rate

---

### 2. Yelp Fusion API ✅ READY
**Status:** Ready, needs API key  
**Cost:** $0 (5,000 calls/day free tier)  
**Automation:** 90%

**What it does:**
- Searches Yelp for HVAC, plumbing, electrical contractors
- Extracts business info, ratings, review counts
- Enriches leads with AI-generated personalization

**Setup:**
1. Get free API key at https://www.yelp.com/developers/v3/manage_app
2. Set `YELP_API_KEY` in `leads/yelp_lead_scraper.py`
3. Run `python leads/yelp_lead_scraper.py`

**Expected Results:**
- 100-200 leads per city
- Higher quality than Google Maps (verified businesses)
- 5-8% response rate

---

### 3. Cold Email Outreach ✅ LIVE
**Status:** Active  
**Cost:** $0 (GMass free tier: 50 emails/day)  
**Automation:** 85%

**What it does:**
- Sends personalized cold emails to qualified leads
- 3 email sequences: high-intent, medium-intent, low-intent
- 5-touch follow-up cadence over 30 days
- Personalization based on business-specific hooks

**Setup:**
1. Install GMass on Gmail (azelt.marketing@gmail.com)
2. Export outreach batch from dashboard
3. Upload to GMass and schedule campaigns

**Expected Results:**
- 25-35% open rate
- 8-15% reply rate
- 5-10% demo booking rate
- 20-30% close rate from demos

---

### 4. LinkedIn Outreach ✅ READY
**Status:** Ready, manual + semi-automated  
**Cost:** $0 (free LinkedIn tier)  
**Automation:** 70%

**What it does:**
- Finds decision makers on LinkedIn
- Sends personalized connection requests and DMs
- Follow-up sequences based on responses

**Setup:**
1. Optimize LinkedIn profile for B2B outreach
2. Use LinkedIn Sales Navigator free trial (first month free)
3. Send 10-20 connection requests per day manually
4. Follow up with personalized DMs

**Expected Results:**
- 10-20% response rate
- 3-5% demo booking rate
- Higher quality leads than cold email

---

### 5. Cold Calling ✅ READY
**Status:** Ready, manual  
**Cost:** $0 (using existing phone)  
**Automation:** 30%

**What it does:**
- Calls qualified leads directly
- Uses proven discovery call script
- Handles objections and books demos

**Setup:**
1. Use existing phone or free VoIP app
2. Load top 50 leads by score
3. Follow cold call script from `outreach/sequences.md`
4. Log outcomes in dashboard

**Expected Results:**
- 15-25% connect rate
- 30-40% positive response from connected calls
- 5-10% demo booking rate

---

### 6. Referral Program ✅ PLANNED
**Status:** Planned, launch after 3 clients  
**Cost:** $0 (commission-based)  
**Automation:** 60%

**What it does:**
- Existing clients refer new clients
- 10% discount for referring client
- 10% discount for referred client

**Setup:**
1. Launch after 3 paying clients
2. Add referral tracking to dashboard
3. Automate discount application via Stripe

**Expected Results:**
- 20% of new business from referrals by month 6
- Lower CAC than paid channels
- Higher quality leads (pre-vetted)

---

### 7. Content Marketing ✅ PLANNED
**Status:** Planned, launch month 2  
**Cost:** $0 (free platforms)  
**Automation:** 50%

**What it does:**
- Post helpful HVAC/roofing tips on social media
- Create simple guides and checklists
- Share on Reddit, Facebook groups, Nextdoor

**Setup:**
1. Create business social media accounts
2. Post 3x per week on LinkedIn, Facebook, Nextdoor
3. Create lead magnets: "5 Ways to Avoid HVAC Scams"
4. Drive traffic to landing page

**Expected Results:**
- 5-10 inbound leads per month by month 3
- Lower CAC
- Brand authority building

---

### 8. Community Involvement ✅ PLANNED
**Status:** Planned, ongoing  
**Cost:** $0  
**Automation:** 40%

**What it does:**
- Join local HVAC/roofing Facebook groups
- Participate in local business associations
- Attend local meetups and events
- Provide value before pitching

**Setup:**
1. Join 10+ local contractor groups
2. Comment on posts, answer questions
3. Share case studies and results
4. DM warm leads who engage

**Expected Results:**
- 3-5 warm leads per month
- Higher trust and response rate
- Long-term relationship building

---

## FREE LEAD SOURCES IN USE

| Source | Method | Automation | Cost | Lead Quality |
|--------|--------|------------|------|--------------|
| Google Maps | Scraping | 95% | $0 | Medium-High |
| Yelp | API | 90% | $0 | High |
| LinkedIn | Manual/API | 70% | $0 | High |
| Cold Email | GMass | 85% | $0 | Medium |
| Cold Calling | Manual | 30% | $0 | High |
| Referrals | Automated | 60% | $0 | Very High |
| Content | Manual | 50% | $0 | Medium |
| Community | Manual | 40% | $0 | High |

---

## AUTOMATION OPPORTUNITIES

### Immediate (Week 1)
1. **Google Maps Scraper** → Auto-import to dashboard
2. **Email Templates** → Auto-personalize via AI
3. **Follow-up Sequences** → Auto-schedule in GMass

### Short-term (Month 1)
1. **LinkedIn Automation** → Use LinkedIn API for connection requests
2. **Call Tracking** → Log call outcomes directly to dashboard
3. **Lead Scoring** → Auto-score new leads as they're added

### Medium-term (Month 2)
1. **Referral Tracking** → Auto-apply discounts via Stripe
2. **Content Calendar** → Auto-schedule social posts
3. **Community Monitoring** → Alert on new posts in target groups

---

## EXPECTED RESULTS BY CHANNEL

### Month 1
- Google Maps: 100 leads, 10 responses, 2 demos, 1 client
- Cold Email: 500 emails, 50 replies, 10 demos, 2 clients
- Cold Calling: 50 calls, 10 connections, 2 demos, 1 client
- **Total Month 1:** 4 clients, $7,500 MRR

### Month 2
- Google Maps: 200 leads, 20 responses, 5 demos, 2 clients
- Cold Email: 1,000 emails, 100 replies, 20 demos, 4 clients
- Cold Calling: 100 calls, 20 connections, 5 demos, 2 clients
- Referrals: 1 referral, 1 client
- **Total Month 2:** 9 clients, $18,000 MRR

### Month 3
- All channels scaled 2x
- Content marketing starts generating inbound
- **Total Month 3:** 15 clients, $34,000 MRR

---

## COMPETITIVE ADVANTAGE

Most agencies rely on paid ads or manual outreach. We're building:

1. **Automated lead generation** — Scrapers run 24/7
2. **AI-powered personalization** — Every message is unique
3. **Multi-channel follow-up** — Email + LinkedIn + phone
4. **Performance guarantee** — 10 appointments or refund
5. **Zero upfront cost** — All free tools until revenue

This system is designed to scale without increasing ad spend or headcount.

---

## NEXT STEPS

1. **Today:** Activate Google Maps scraper, generate 100 leads
2. **This week:** Launch cold email campaign with GMass
3. **Next week:** Start cold calling top 50 leads
4. **Month 2:** Add Yelp API, LinkedIn automation, referral program
5. **Month 3:** Launch content marketing, community outreach

All execution is autonomous. You'll see results in the dashboard.
