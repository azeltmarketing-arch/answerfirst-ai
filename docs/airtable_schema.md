# AnswerFirst AI — Airtable Lead Database Schema

## Base Name: AnswerFirst AI Leads

### Table 1: Leads

| Field Name | Type | Description |
|------------|------|-------------|
| Business Name | Single line text | Company name |
| Owner Name | Single line text | Decision maker name |
| Email | Email | Primary contact email |
| Phone | Phone | Primary phone number |
| Website | URL | Business website |
| Address | Single line text | Physical address |
| City | Single line text | City |
| State | Single line text | State |
| Google Rating | Number | Google Maps rating (1-5) |
| Review Count | Number | Number of Google reviews |
| Services | Single line text | Comma-separated service list |
| Source | Single select | google_maps, linkedin, referral, other |
| Lead Score | Number | 0-100 qualification score |
| Status | Single select | new, researched, contacted, responded, demo_booked, proposal_sent, closed_won, closed_lost, nurture |
| Personalization Hook | Long text | AI-generated personalization hook |
| Outreach Channel | Single select | email, linkedin, phone, email+linkedin |
| Sequence Assigned | Single select | A (high-intent), B (medium-intent), C (low-intent) |
| Last Contacted | Date | Last outreach timestamp |
| Next Follow-up | Date | Scheduled follow-up date |
| Response Sentiment | Single select | positive, neutral, negative, none |
| Notes | Long text | Manual notes and observations |
| Created At | Created time | Auto-populated |
| Updated At | Last modified time | Auto-populated |

### Table 2: Outreach Activities

| Field Name | Type | Description |
|------------|------|-------------|
| Lead | Link to Leads | Associated lead |
| Activity Type | Single select | email, linkedin, phone_call, sms |
| Direction | Single select | outbound, inbound |
| Subject | Single line text | Email subject or call topic |
| Body | Long text | Message content or call notes |
| Sent At | Date | When outreach was sent |
| Opened At | Date | When email was opened |
| Clicked At | Date | When link was clicked |
| Replied At | Date | When lead replied |
| Outcome | Single select | no_response, positive, negative, info_requested, demo_booked |
| Follow-up Scheduled | Date | Next follow-up date |
| Created At | Created time | Auto-populated |

### Table 3: Deals

| Field Name | Type | Description |
|------------|------|-------------|
| Deal Name | Single line text | [Business Name] - [Package] |
| Lead | Link to Leads | Associated lead |
| Package | Single select | Basic, Premium, Enterprise |
| Monthly Value | Currency | MRR amount |
| Setup Fee | Currency | One-time setup fee |
| Stage | Single select | qualified, demo_booked, proposal_sent, closed_won, closed_lost |
| Probability | Percent | Close probability |
| Expected Close Date | Date | When deal is expected to close |
| Guarantee Accepted | Checkbox | Whether performance guarantee was accepted |
| Contract Sent | Checkbox | Whether contract was sent |
| Contract Signed | Checkbox | Whether contract is signed |
| Payment Received | Checkbox | Whether payment was received |
| Onboarding Status | Single select | not_started, in_progress, complete |
| Created At | Created time | Auto-populated |
| Updated At | Last modified time | Auto-populated |

### Table 4: Clients

| Field Name | Type | Description |
|------------|------|-------------|
| Business Name | Single line text | Company name |
| Lead | Link to Leads | Associated lead record |
| Package | Single select | Basic, Premium, Enterprise |
| Monthly Fee | Currency | MRR amount |
| Start Date | Date | Service start date |
| Contract Type | Single select | monthly, annual, enterprise |
| Google Account | Single line text | Client Google account for calendar |
| Calendar ID | Single line text | Google Calendar ID |
| Phone Number | Phone | Business phone number |
| SMS Number | Phone | SMS notifications number |
| AI Script | Long text | Custom AI call script |
| Services | Long text | Service list and pricing |
| Service Areas | Single line text | Geographic service areas |
| Business Hours | Single line text | Operating hours |
| Emergency Policy | Long text | After-hours emergency rules |
| Status | Single select | active, paused, cancelled |
| Created At | Created time | Auto-populated |

### Table 5: Performance Metrics

| Field Name | Type | Description |
|------------|------|-------------|
| Client | Link to Clients | Associated client |
| Period | Single select | daily, weekly, monthly, quarterly |
| Period Start | Date | Start of reporting period |
| Period End | Date | End of reporting period |
| Calls Answered | Number | Total calls answered |
| Calls Missed | Number | Total calls missed |
| Appointments Booked | Number | Total appointments booked |
| Appointments Confirmed | Number | Appointments confirmed by client |
| No-shows | Number | No-show appointments |
| Revenue Attributed | Currency | Revenue from booked appointments |
| Avg Job Value | Currency | Average job value |
| Booking Rate | Percent | Appointments / calls answered |
| Satisfaction Score | Number | 1-5 CSAT score |
| Notes | Long text | Observations and recommendations |
| Created At | Created time | Auto-populated |

---

## Views

### Leads Table Views
1. **All Leads** — All leads sorted by score descending
2. **Qualified Leads** — Score >= 65, status = new
3. **Contacted** — Status = contacted
4. **Responded** — Status = responded
5. **Demo Booked** — Status = demo_booked
6. **Proposal Sent** — Status = proposal_sent
7. **Closed Won** — Status = closed_won
8. **Nurture Queue** — Status = nurture, re-score in 30 days

### Deals Board View
- Kanban board with stages: Qualified → Demo Booked → Proposal Sent → Closed Won
- Cards show: business name, package, monthly value, probability

### Performance Dashboard
- Charts: calls answered, bookings, revenue by month
- Filters: by client, by period

---

## Automations

### Automation 1: New Lead → Score & Enrich
- Trigger: New record created in Leads
- Action: Run enrichment script, calculate score, update fields

### Automation 2: Qualified Lead → Assign Sequence
- Trigger: Lead score >= 65 and status = new
- Action: Assign outreach sequence, set next follow-up date

### Automation 3: Deal Stage Change → Notification
- Trigger: Deal stage changed
- Action: Send email notification to sales team

### Automation 4: Payment Received → Onboarding
- Trigger: Payment received checkbox checked
- Action: Create client record, start onboarding workflow

### Automation 5: Weekly Report → Generate
- Trigger: Every Monday at 8am
- Action: Generate weekly performance report, send to team
