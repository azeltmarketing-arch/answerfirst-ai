"""
Cold email outreach system for AnswerFirst AI.
Generates personalized 5-touch sequences per niche.
"""

NICHE_PAIN_POINTS = {
    "hvac": {
        "name": "HVAC",
        "pain_points": [
            "Missed calls",
            "After-hours inquiries",
            "Emergency inquiries",
            "Estimate requests",
            "Slow response",
            "Follow-up",
            "Scheduling",
            "Leads generated while technicians are busy",
        ],
        "core_message": "HVAC companies can lose valuable opportunities when leads cannot immediately reach someone.",
        "services": ["AC repair", "furnace repair", "installation", "maintenance", "emergency service"],
    },
    "roofing": {
        "name": "Roofing",
        "pain_points": [
            "Estimate requests",
            "Storm-related inquiries",
            "Homeowners comparing multiple roofers",
            "Slow follow-up",
            "Missed calls",
            "Inspection scheduling",
            "Lead qualification",
        ],
        "core_message": "Roofing prospects frequently contact multiple companies, making response speed and follow-up important.",
        "services": ["roof replacement", "roof repair", "storm damage", "inspection", "new roof"],
    },
    "solar": {
        "name": "Solar",
        "pain_points": [
            "Consultation requests",
            "Qualification",
            "Follow-up",
            "Prospects comparing providers",
            "Appointment booking",
            "After-hours inquiries",
            "Long sales cycles",
        ],
        "core_message": "Solar businesses can benefit from consistent follow-up throughout a longer buying process.",
        "services": ["solar panels", "solar installation", "solar consultation", "residential solar"],
    },
    "landscaping": {
        "name": "Landscaping",
        "pain_points": [
            "Quote requests",
            "Missed inquiries",
            "Recurring service inquiries",
            "Estimate scheduling",
            "Follow-up",
            "Seasonal demand",
            "Administrative workload",
        ],
        "core_message": "Landscaping companies can recover opportunities by consistently following up with people who requested information or quotes.",
        "services": ["lawn care", "landscape design", "irrigation", "tree trimming", "hardscaping"],
    },
    "general contractors": {
        "name": "General Contractors",
        "pain_points": [
            "Project inquiries",
            "Estimate requests",
            "Qualification",
            "Missed calls",
            "Follow-up",
            "Scheduling",
            "Long consideration periods",
        ],
        "core_message": "Contractors can lose potential projects when inquiries aren't consistently handled and followed up with.",
        "services": ["remodeling", "construction", "renovation", "home addition", "commercial construction"],
    },
    "nail salons": {
        "name": "Nail Salons",
        "pain_points": [
            "Appointment inquiries",
            "Instagram/website messages",
            "Availability questions",
            "Pricing questions",
            "Abandoned bookings",
            "Reminders",
            "After-hours inquiries",
        ],
        "core_message": "Salons can recover appointments by responding and following up automatically while staff focus on clients.",
        "services": ["manicure", "pedicure", "gel nails", "acrylic nails", "nail art"],
    },
    "hair salons": {
        "name": "Hair Salons",
        "pain_points": [
            "DMs",
            "Appointment requests",
            "Availability",
            "Pricing questions",
            "Follow-up",
            "Booking reminders",
            "Client communication",
        ],
        "core_message": "Stylists should be focused on clients rather than constantly monitoring incoming messages.",
        "services": ["haircut", "coloring", "styling", "highlights", "hair treatment"],
    },
    "dentists": {
        "name": "Dentists",
        "pain_points": [
            "New patient inquiries",
            "Appointment requests",
            "Missed calls",
            "Front-desk workload",
            "Follow-up",
            "Scheduling",
            "After-hours inquiries",
            "Common questions",
        ],
        "core_message": "Dental practices can reduce front-desk workload while improving consistency in new-patient communication.",
        "services": ["general dentistry", "cleaning", "cosmetic dentistry", "implants", "orthodontics"],
    },
    "med spas": {
        "name": "Med Spas",
        "pain_points": [
            "Treatment inquiries",
            "Consultation requests",
            "Pricing questions",
            "Appointment booking",
            "Follow-up",
            "DMs",
            "After-hours inquiries",
        ],
        "core_message": "Med spas can improve inquiry follow-up and appointment conversion by automating repetitive communication.",
        "services": ["Botox", "filler", "laser treatment", "IV therapy", "skin rejuvenation"],
    },
    "barbers": {
        "name": "Barbers",
        "pain_points": [
            "DMs",
            "Appointment requests",
            "Availability questions",
            "Missed inquiries",
            "Follow-up",
            "Booking reminders",
            "After-hours messages",
        ],
        "core_message": "Barbers should be cutting hair rather than constantly checking messages and chasing bookings.",
        "services": ["haircut", "beard trim", "fade", "hot towel shave", "line up"],
    },
}

NICHE_SEQUENCES = {
    "hvac": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone contacts {business_name} after hours or while your team is busy, what happens to that lead?

That's a problem we're helping HVAC companies solve.

We build AI-powered CRM systems that can respond to leads, qualify inquiries, follow up automatically, and help get appointments onto the calendar.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "How many HVAC leads go cold?",
            "body": """Hi {first_name},

One thing we see with HVAC companies is that the lead isn't always the problem.

Speed-to-lead and follow-up can be.

Someone requests an estimate, calls after hours, or doesn't answer the first time — and the opportunity can disappear.

Our AI CRM keeps those conversations moving automatically so your team can focus on the actual jobs.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple HVAC opportunity",
            "body": """Hi {first_name},

Imagine someone requests an HVAC estimate at 9:30 PM.

Instead of waiting until the next morning, they receive an immediate response, answer a few qualifying questions, and can be guided toward booking.

That's the type of workflow we're building for service businesses.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already responding to every inbound lead quickly and following up consistently, you probably don't need what I'm offering.

But if leads sometimes wait for a callback or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving lead response and follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "roofing": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when a homeowner reaches out to {business_name} for a roof estimate or storm inspection, how quickly does someone follow up?

That's a problem we're helping roofing companies solve.

We build AI-powered CRM systems that respond to inquiries, qualify leads, and keep follow-up moving automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Roofing leads and follow-up",
            "body": """Hi {first_name},

One thing we see with roofing companies is that the inquiry isn't always the problem.

Speed and consistency are.

A homeowner compares 3-4 roofers and reaches out to all of them. The company that responds first and follows up professionally often wins the job.

Our AI CRM keeps those conversations moving automatically so your estimators can focus on inspections and jobs.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "Storm leads and follow-up",
            "body": """Hi {first_name},

After a storm, {business_name} probably gets a spike in inquiries.

The challenge isn't just getting the lead — it's following up fast enough before the homeowner calls another roofer.

We build AI systems that respond immediately, qualify the inquiry, and help schedule inspections automatically.

If I showed you a working example, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already following up with every inquiry within minutes and keeping estimators booked, you probably don't need what I'm offering.

But if leads sometimes wait or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving lead response and follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "solar": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone requests a solar consultation from {business_name}, what happens next?

That's a problem we're helping solar businesses solve.

We build AI-powered CRM systems that respond to inquiries, qualify prospects, and keep follow-up moving through a longer sales cycle.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Solar leads and long sales cycles",
            "body": """Hi {first_name},

One thing we see with solar companies is that the first conversation is just the beginning.

Prospects compare providers, delay decisions, and sometimes stop responding — and the opportunity can disappear if follow-up isn't consistent.

Our AI CRM keeps those conversations moving automatically so your team can focus on consultations and installations.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple solar opportunity",
            "body": """Hi {first_name},

Imagine someone requests a solar estimate at 8 PM.

Instead of waiting until the next morning, they receive an immediate response, answer a few qualifying questions, and can be guided toward booking a consultation.

That's the type of workflow we're building for solar businesses.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already following up with every inquiry consistently and keeping the pipeline moving, you probably don't need what I'm offering.

But if leads sometimes wait or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving lead follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "landscaping": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone requests a quote from {business_name} and doesn't get an immediate response, what happens to that lead?

That's a problem we're helping landscaping companies solve.

We build AI-powered CRM systems that respond to inquiries, qualify leads, and keep follow-up moving automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Landscaping leads and follow-up",
            "body": """Hi {first_name},

One thing we see with landscaping companies is that the inquiry isn't always the problem.

Speed and consistency are.

Someone requests a quote during the busy season and doesn't get a response until the next day — and they've already called another company.

Our AI CRM keeps those conversations moving automatically so your team can focus on the actual jobs.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple landscaping opportunity",
            "body": """Hi {first_name},

Imagine someone requests a landscaping quote on Saturday morning.

Instead of waiting until Monday, they receive an immediate response, answer a few qualifying questions, and can be guided toward booking a consultation.

That's the type of workflow we're building for service businesses.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already following up with every inquiry quickly and consistently, you probably don't need what I'm offering.

But if leads sometimes wait or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving lead response and follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "general contractors": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone reaches out to {business_name} about a project, how quickly does someone follow up?

That's a problem we're helping general contractors solve.

We build AI-powered CRM systems that respond to inquiries, qualify leads, and keep follow-up moving automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Contractor leads and follow-up",
            "body": """Hi {first_name},

One thing we see with general contractors is that the inquiry isn't always the problem.

Speed and consistency are.

Someone requests an estimate, has questions, or doesn't answer the first time — and the opportunity can disappear.

Our AI CRM keeps those conversations moving automatically so your team can focus on actual projects.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple contractor opportunity",
            "body": """Hi {first_name},

Imagine someone requests a project estimate at 7 PM.

Instead of waiting until the next morning, they receive an immediate response, answer a few qualifying questions, and can be guided toward booking a consultation.

That's the type of workflow we're building for service businesses.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already following up with every inquiry quickly and consistently, you probably don't need what I'm offering.

But if leads sometimes wait or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving lead response and follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "nail salons": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone messages {business_name} about an appointment after hours, what happens to that booking?

That's a problem we're helping salons solve.

We build AI-powered systems that respond to inquiries, confirm availability, and book appointments automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Salon bookings and follow-up",
            "body": """Hi {first_name},

One thing we see with salons is that the inquiry isn't always the problem.

Response speed and follow-up are.

Someone requests an appointment on Instagram or your website after hours, and by morning they've found another salon.

Our system keeps those conversations moving automatically so your staff can focus on clients.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple salon opportunity",
            "body": """Hi {first_name},

Imagine someone requests a nail appointment at 8 PM.

Instead of waiting until the next morning, they receive an immediate response, can see available times, and book instantly.

That's the type of workflow we're building for salons.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already responding to every inquiry and filling every opening, you probably don't need what I'm offering.

But if bookings sometimes slip through or clients wait too long for a reply, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving booking follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "hair salons": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone DMs {business_name} for an appointment while you're with a client, what happens to that lead?

That's a problem we're helping hair salons solve.

We build AI-powered systems that respond to inquiries, confirm availability, and book appointments automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Salon DMs and follow-up",
            "body": """Hi {first_name},

One thing we see with hair salons is that stylists should be focused on clients rather than constantly checking messages.

Someone requests an appointment on Instagram or your website and waits too long for a reply — and books elsewhere.

Our system keeps those conversations moving automatically so your team can focus on service.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple salon opportunity",
            "body": """Hi {first_name},

Imagine someone requests a haircut appointment at 7 PM.

Instead of waiting until the next day, they receive an immediate response, can see available times, and book instantly.

That's the type of workflow we're building for salons.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already responding to every inquiry and keeping the book full, you probably don't need what I'm offering.

But if bookings sometimes slip through or clients wait too long for a reply, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving booking follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "dentists": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when a new patient reaches out to {business_name}, how quickly does someone follow up?

That's a problem we're helping dental practices solve.

We build AI-powered systems that respond to inquiries, qualify new patients, and keep follow-up moving automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Dental leads and follow-up",
            "body": """Hi {first_name},

One thing we see with dental practices is that the inquiry isn't always the problem.

Speed and consistency are.

Someone requests an appointment for a cleaning or consultation and doesn't get a response fast enough — and they call another practice.

Our AI system keeps those conversations moving automatically so your front desk can focus on patients in the office.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple dental opportunity",
            "body": """Hi {first_name},

Imagine someone requests a new patient appointment at 8 PM.

Instead of waiting until the next morning, they receive an immediate response, can see available times, and book online.

That's the type of workflow we're building for dental practices.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already following up with every inquiry quickly and consistently, you probably don't need what I'm offering.

But if leads sometimes wait or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving new patient follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "med spas": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone inquires about a treatment at {business_name}, how quickly does someone follow up?

That's a problem we're helping med spas solve.

We build AI-powered systems that respond to inquiries, qualify prospects, and keep follow-up moving automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Med spa leads and follow-up",
            "body": """Hi {first_name},

One thing we see with med spas is that the inquiry isn't always the problem.

Speed and follow-up are.

Someone asks about Botox, pricing, or availability and doesn't get a response fast enough — and they book elsewhere.

Our AI system keeps those conversations moving automatically so your staff can focus on clients.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple med spa opportunity",
            "body": """Hi {first_name},

Imagine someone asks about treatment pricing at 8 PM.

Instead of waiting until the next day, they receive an immediate response with general information and can book a consultation.

That's the type of workflow we're building for med spas.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already following up with every inquiry quickly and consistently, you probably don't need what I'm offering.

But if leads sometimes wait or fall through the cracks, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving inquiry follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
    "barbers": [
        {
            "day": 1,
            "subject": "Quick question about {business_name}",
            "body": """Hi {first_name},

Quick question — when someone messages {business_name} for an appointment while you're cutting hair, what happens to that lead?

That's a problem we're helping barbers solve.

We build AI-powered systems that respond to inquiries, confirm availability, and book appointments automatically.

I'd be happy to show you what that could look like for {business_name}.

Would you be open to a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 3,
            "subject": "Barber bookings and follow-up",
            "body": """Hi {first_name},

One thing we see with barbers is that stylists should be cutting hair rather than constantly checking messages.

Someone requests a fade or haircut and waits too long for a reply — and books with someone else.

Our system keeps those conversations moving automatically so you can focus on clients.

Would you be open to taking a quick look?

— {sender_name}""",
        },
        {
            "day": 7,
            "subject": "A simple barber opportunity",
            "body": """Hi {first_name},

Imagine someone requests a haircut appointment at 7 PM.

Instead of waiting until the next day, they receive an immediate response, can see available times, and book instantly.

That's the type of workflow we're building for barbers.

If I showed you a working example for {business_name}, would you be open to a quick walkthrough?

— {sender_name}""",
        },
        {
            "day": 14,
            "subject": "Worth looking at?",
            "body": """Hi {first_name},

I'll keep this short.

If {business_name} is already responding to every inquiry and keeping the chair full, you probably don't need what I'm offering.

But if bookings sometimes slip through or clients wait too long for a reply, there's likely an opportunity to improve the process.

Would Thursday work for a 15-minute walkthrough?

— {sender_name}""",
        },
        {
            "day": 30,
            "subject": "Should I close this out?",
            "body": """Hi {first_name},

I haven't heard back, so I'll assume improving booking follow-up isn't a priority right now.

I'll close this out after this message.

If you'd still like to see the system, here's my calendar: {booking_link}

Either way, thanks for reading.

— {sender_name}""",
        },
    ],
}


def get_niche_key(niche: str) -> str:
    n = niche.strip().lower()
    mapping = {
        "hvac": "hvac",
        "air conditioning": "hvac",
        "heating": "hvac",
        "roofing": "roofing",
        "roofer": "roofing",
        "solar": "solar",
        "landscaping": "landscaping",
        "lawn care": "landscaping",
        "general contractor": "general contractors",
        "contractor": "general contractors",
        "construction": "general contractors",
        "nail salon": "nail salons",
        "nails": "nail salons",
        "hair salon": "hair salons",
        "salon": "hair salons",
        "hair": "hair salons",
        "dentist": "dentists",
        "dental": "dentists",
        "med spa": "med spas",
        "medical spa": "med spas",
        "barber": "barbers",
        "barbershop": "barbers",
    }
    return mapping.get(n, n)


def generate_email(niche: str, template_index: int, variables: dict) -> dict:
    """Generate a personalized email for a given niche and template index."""
    niche_key = get_niche_key(niche)
    sequence = NICHE_SEQUENCES.get(niche_key, NICHE_SEQUENCES["hvac"])
    
    if template_index >= len(sequence):
        template_index = len(sequence) - 1
    
    template = sequence[template_index]
    
    defaults = {
        "first_name": "there",
        "business_name": "your business",
        "sender_name": "AnswerFirst AI",
        "booking_link": "https://calendly.com/answerfirst-ai",
    }
    defaults.update(variables)
    
    subject = template["subject"].format(**defaults)
    body = template["body"].format(**defaults)
    
    return {
        "day": template["day"],
        "subject": subject,
        "body": body,
        "niche": niche_key,
        "template_index": template_index,
    }


def get_sequence_for_niche(niche: str) -> list:
    """Get the full 5-email sequence for a niche."""
    niche_key = get_niche_key(niche)
    return NICHE_SEQUENCES.get(niche_key, NICHE_SEQUENCES["hvac"])


def score_personalization(fact: str, offer_relevant: bool) -> int:
    """Score personalization quality 1-5."""
    if not fact or not offer_relevant:
        return 1
    if len(fact.split()) < 5:
        return 2
    if "offer" in fact.lower() or "service" in fact.lower():
        return 3
    if "website" in fact.lower() or "contact" in fact.lower() or "booking" in fact.lower():
        return 4
    return 4 if offer_relevant else 3
