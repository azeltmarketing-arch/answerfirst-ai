"""
AnswerFirst AI — Public Website (Stripe Design System)
Design source: C:\\Users\\azelt\\repos\\awesome-design-md\\design-md\\stripe\\DESIGN.md
"""

from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

SITE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnswerFirst AI — 15+ Appointments Per Month Guaranteed</title>
    <meta name="description" content="AI-powered appointment setting for HVAC and roofing contractors. 24/7 call answering, SMS follow-up, and lead nurturing. 10-appointment guarantee or your money back.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #533afd;
            --primary-deep: #4434d4;
            --primary-press: #2e2b8c;
            --primary-soft: #665efd;
            --primary-bg-subdued-hover: #b9b9f9;
            --brand-dark-900: #1c1e54;
            --ink: #0d253d;
            --ink-secondary: #273951;
            --ink-mute: #64748d;
            --ink-mute-2: #61718a;
            --on-primary: #ffffff;
            --canvas: #ffffff;
            --canvas-soft: #f6f9fc;
            --canvas-cream: #f5e9d4;
            --hairline: #e3e8ee;
            --hairline-input: #a8c3de;
            --ruby: #ea2261;
            --magenta: #f96bee;
            --lemon: #9b6829;
            --shadow-blue: #003770;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--ink);
            background: var(--canvas);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        a { color: var(--primary); text-decoration: none; }
        a:hover { color: var(--primary-deep); }

        /* Hero with gradient mesh */
        .hero {
            position: relative;
            background: linear-gradient(135deg, #f8f9ff 0%, #eef0ff 50%, #f5f3ff 100%);
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            inset: 0;
            background:
                radial-gradient(ellipse 80% 60% at 20% 30%, rgba(83,58,253,0.08) 0%, transparent 60%),
                radial-gradient(ellipse 60% 80% at 80% 70%, rgba(102,94,253,0.06) 0%, transparent 60%),
                radial-gradient(ellipse 50% 50% at 50% 50%, rgba(233,226,230,0.25) 0%, transparent 70%);
            pointer-events: none;
        }
        .hero-band {
            position: relative;
            max-width: 1200px;
            margin: 0 auto;
            padding: 64px 24px 80px;
            text-align: center;
        }
        .hero-band .eyebrow {
            display: inline-block;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.6px;
            color: var(--primary);
            text-transform: uppercase;
            margin-bottom: 20px;
        }
        .hero-band h1 {
            font-size: 56px;
            font-weight: 300;
            line-height: 1.08;
            letter-spacing: -1.4px;
            color: var(--ink);
            max-width: 900px;
            margin: 0 auto 24px;
        }
        .hero-band h1 span {
            font-weight: 600;
            background: linear-gradient(135deg, var(--primary), var(--magenta));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero-band p {
            font-size: 17px;
            font-weight: 400;
            line-height: 1.5;
            color: var(--ink-mute);
            max-width: 680px;
            margin: 0 auto 36px;
        }
        .hero-actions {
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px 32px;
            border-radius: 9999px;
            font-family: 'Inter', sans-serif;
            font-size: 15px;
            font-weight: 500;
            line-height: 1;
            letter-spacing: 0;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn-primary {
            background: var(--primary);
            color: var(--on-primary);
        }
        .btn-primary:hover {
            background: var(--primary-deep);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(83,58,253,0.3);
        }
        .btn-outline {
            background: transparent;
            color: var(--ink);
            border: 1px solid var(--hairline);
        }
        .btn-outline:hover {
            background: var(--canvas-soft);
            border-color: var(--primary);
            color: var(--primary);
        }

        /* Sections */
        .section {
            padding: 80px 24px;
        }
        .section-band {
            max-width: 1200px;
            margin: 0 auto;
        }
        .section-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.8px;
            color: var(--primary);
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .section-title {
            font-size: 32px;
            font-weight: 300;
            line-height: 1.2;
            letter-spacing: -0.64px;
            color: var(--ink);
            margin-bottom: 16px;
        }
        .section-subtitle {
            font-size: 16px;
            color: var(--ink-mute);
            max-width: 640px;
            line-height: 1.6;
        }

        /* Problem cards */
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-top: 48px;
        }
        .card {
            background: var(--canvas);
            border: 1px solid var(--hairline);
            border-radius: 8px;
            padding: 32px;
            transition: all 0.3s ease;
        }
        .card:hover {
            border-color: var(--primary-soft);
            box-shadow: 0 8px 32px rgba(83,58,253,0.08);
            transform: translateY(-2px);
        }
        .card-icon {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: var(--canvas-soft);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 20px;
        }
        .card h3 {
            font-size: 20px;
            font-weight: 500;
            color: var(--ink);
            margin-bottom: 12px;
            letter-spacing: -0.22px;
        }
        .card p {
            font-size: 15px;
            color: var(--ink-mute);
            line-height: 1.6;
        }

        /* Steps */
        .steps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 24px;
            margin-top: 48px;
        }
        .step {
            text-align: center;
            padding: 32px 24px;
            background: var(--canvas);
            border: 1px solid var(--hairline);
            border-radius: 8px;
        }
        .step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .step h3 {
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 10px;
        }
        .step p {
            font-size: 14px;
            color: var(--ink-mute);
            line-height: 1.6;
        }

        /* Pricing */
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-top: 48px;
        }
        .pricing-card {
            background: var(--canvas);
            border: 1px solid var(--hairline);
            border-radius: 8px;
            padding: 40px 32px;
            text-align: center;
            position: relative;
            transition: all 0.3s ease;
        }
        .pricing-card:hover {
            border-color: var(--primary-soft);
            box-shadow: 0 12px 40px rgba(83,58,253,0.1);
        }
        .pricing-card.featured {
            border-color: var(--primary);
            background: linear-gradient(180deg, rgba(83,58,253,0.02) 0%, var(--canvas) 100%);
        }
        .pricing-card .badge {
            position: absolute;
            top: -12px;
            right: 32px;
            background: var(--primary);
            color: white;
            padding: 6px 16px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.4px;
        }
        .pricing-card h3 {
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 8px;
        }
        .price {
            font-size: 48px;
            font-weight: 300;
            letter-spacing: -1px;
            color: var(--ink);
            margin: 20px 0;
        }
        .price span {
            font-size: 16px;
            color: var(--ink-mute);
            font-weight: 400;
        }
        .pricing-card ul {
            list-style: none;
            margin: 32px 0;
            text-align: left;
        }
        .pricing-card ul li {
            padding: 10px 0;
            font-size: 14px;
            color: var(--ink-secondary);
            border-bottom: 1px solid var(--hairline);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .pricing-card ul li:last-child {
            border-bottom: none;
        }
        .pricing-card ul li::before {
            content: "✓";
            color: var(--primary);
            font-weight: 700;
            font-size: 14px;
        }

        /* Guarantee */
        .guarantee {
            background: linear-gradient(135deg, var(--brand-dark-900) 0%, #1a1c4a 100%);
            color: white;
            padding: 80px 24px;
            text-align: center;
        }
        .guarantee h2 {
            font-size: 32px;
            font-weight: 300;
            letter-spacing: -0.64px;
            margin-bottom: 20px;
        }
        .guarantee p {
            font-size: 16px;
            color: #cbd5e1;
            max-width: 680px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* CTA */
        .cta-section {
            background: var(--canvas);
            padding: 80px 24px;
            text-align: center;
        }
        .cta-section h2 {
            font-size: 32px;
            font-weight: 300;
            letter-spacing: -0.64px;
            margin-bottom: 20px;
        }
        .cta-section p {
            font-size: 16px;
            color: var(--ink-mute);
            max-width: 640px;
            margin: 0 auto 32px;
        }

        /* Footer */
        footer {
            background: var(--ink);
            color: #cbd5e1;
            padding: 40px 24px;
            text-align: center;
            font-size: 14px;
        }
        footer a {
            color: var(--primary-soft);
        }

        @media (max-width: 768px) {
            .hero-band h1 {
                font-size: 32px;
            }
            .section-title {
                font-size: 24px;
            }
            .hero-actions {
                flex-direction: column;
            }
            .pricing-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header style="background: rgba(255,255,255,0.92); backdrop-filter: blur(20px); border-bottom: 1px solid var(--hairline); padding: 20px 0; position: sticky; top: 0; z-index: 100;">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 20px; font-weight: 600; color: var(--ink); letter-spacing: -0.3px;">
                Answer<span style="color: var(--primary);">First</span> AI
            </div>
            <nav style="display: flex; gap: 32px; list-style: none;">
                <a href="#how-it-works" style="color: var(--ink-secondary); font-size: 14px; font-weight: 500;">How It Works</a>
                <a href="#pricing" style="color: var(--ink-secondary); font-size: 14px; font-weight: 500;">Pricing</a>
                <a href="https://arg-lifestyle-eggs-trailer.trycloudflare.com/products" style="color: var(--ink-secondary); font-size: 14px; font-weight: 500;">Products</a>
                <a href="https://arg-lifestyle-eggs-trailer.trycloudflare.com/portal" style="color: var(--ink-secondary); font-size: 14px; font-weight: 500;">Client Portal</a>
                <a href="#guarantee" class="btn btn-primary" style="padding: 10px 24px; font-size: 14px;">Get Started</a>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="hero-band">
            <div class="eyebrow">AI Appointment Setting</div>
            <h1>Never miss another <span>appointment</span> for your HVAC or roofing business.</h1>
            <p>AI-powered call answering and lead recovery that books qualified appointments while you're on the job. 24/7 coverage, SMS follow-up, and a 10-appointment guarantee.</p>
            <div class="hero-actions">
                <a href="#pricing" class="btn btn-primary">Start Free Trial</a>
                <a href="#how-it-works" class="btn btn-outline">See How It Works</a>
            </div>
        </div>
    </section>

    <section class="section" id="how-it-works">
        <div class="section-band">
            <span class="section-label">How It Works</span>
            <h2 class="section-title">From missed calls to booked appointments in 4 simple steps.</h2>
            <p class="section-subtitle">We handle the phone, you show up to the job.</p>
            <div class="steps-grid">
                <div class="step">
                    <div class="step-number">1</div>
                    <h3>We Set Up Your AI Receptionist</h3>
                    <p>Customized for your business, services, and schedule. Takes 7 days or less.</p>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <h3>Calls Get Answered Instantly</h3>
                    <p>AI answers within 1 ring with your business name. Sounds natural, professional.</p>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <h3>Leads Get Qualified & Booked</h3>
                    <p>AI asks the right questions, checks your calendar, and books the appointment.</p>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <h3>You Get More Jobs</h3>
                    <p>Every call becomes a booked appointment. You focus on the work. We handle the phone.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="section" style="background: var(--canvas-soft);">
        <div class="section-band">
            <span class="section-label">Why AnswerFirst AI</span>
            <h2 class="section-title">The problem every contractor faces is solved by AI.</h2>
            <div class="grid-2">
                <div class="card">
                    <div class="card-icon">📞</div>
                    <h3>Missed Calls = Lost Revenue</h3>
                    <p>The average contractor misses 20-30% of incoming calls. Each missed call is a potential $3,000-$8,000 job walking to your competitor.</p>
                </div>
                <div class="card">
                    <div class="card-icon">⏰</div>
                    <h3>Voicemail Doesn't Cut It</h3>
                    <p>85% of customers with an urgent need won't leave a voicemail. They'll call the next company on Google—and you'll never hear from them again.</p>
                </div>
                <div class="card">
                    <div class="card-icon">💰</div>
                    <h3>Marketing Without Backend</h3>
                    <p>You're spending money on ads and marketing, but 30-40% of new leads are lost because you can't answer the phone fast enough.</p>
                </div>
                <div class="card">
                    <div class="card-icon">🤖</div>
                    <h3>AI Solves This</h3>
                    <p>Our AI answers every call within 1 ring, qualifies the lead, and books the appointment directly onto your calendar—24/7, no staff required.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="section" id="pricing">
        <div class="section-band">
            <span class="section-label">Pricing</span>
            <h2 class="section-title">Simple, flat pricing.</h2>
            <p class="section-subtitle">No hidden fees. No long-term contracts. Cancel anytime.</p>
            <div class="pricing-grid">
                <div class="pricing-card">
                    <h3>Basic</h3>
                    <div class="price">$1,500<span>/month</span></div>
                    <ul>
                        <li>AI call answering</li>
                        <li>SMS follow-up</li>
                        <li>Calendar integration</li>
                        <li>Basic analytics</li>
                        <li>Email support</li>
                    </ul>
                    <a href="/products" class="btn btn-outline" style="width: 100%;">Get Started</a>
                </div>
                <div class="pricing-card featured">
                    <div class="badge">MOST POPULAR</div>
                    <h3>Premium</h3>
                    <div class="price">$2,500<span>/month</span></div>
                    <ul>
                        <li>Everything in Basic</li>
                        <li>24/7 coverage</li>
                        <li>Google Maps optimization</li>
                        <li>Bi-weekly strategy call</li>
                        <li>Priority support</li>
                    </ul>
                    <a href="/products" class="btn btn-primary" style="width: 100%;">Get Started</a>
                </div>
                <div class="pricing-card">
                    <h3>Enterprise</h3>
                    <div class="price">$4,000<span>/month</span></div>
                    <ul>
                        <li>Everything in Premium</li>
                        <li>Multi-location support</li>
                        <li>Full local SEO</li>
                        <li>Paid ads management</li>
                        <li>Dedicated account manager</li>
                    </ul>
                    <a href="/products" class="btn btn-outline" style="width: 100%;">Get Started</a>
                </div>
            </div>
        </div>
    </section>

    <section class="guarantee" id="guarantee">
        <div style="max-width: 900px; margin: 0 auto;">
            <h2>Our 30-Day Performance Guarantee</h2>
            <p>If we don't book at least 10 qualified appointments in your first 30 days, you get a full refund. No hoops. No fine print. No "account manager will call you" guilt trips.</p>
        </div>
    </section>

    <section class="cta-section">
        <div class="section-band">
            <h2>Ready to Fill Your Calendar?</h2>
            <p>Book a free 15-minute demo to see exactly how we can recover your missed calls and fill your schedule.</p>
            <a href="mailto:azelt.marketing@gmail.com?subject=AnswerFirst AI Demo Request" class="btn btn-primary">Book Your Free Demo</a>
            <p style="margin-top: 20px; font-size: 14px; color: var(--ink-mute);">Or email us directly at azelt.marketing@gmail.com</p>
        </div>
    </section>

    <footer>
        <div>
            <p>© 2026 AnswerFirst AI. All rights reserved.</p>
            <p style="margin-top: 10px;">
                <a href="https://arg-lifestyle-eggs-trailer.trycloudflare.com/products">Products</a> · <a href="https://arg-lifestyle-eggs-trailer.trycloudflare.com/portal">Client Portal</a> · <a href="mailto:azelt.marketing@gmail.com">Contact</a>
            </p>
        </div>
    </footer>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(SITE_HTML)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5070, debug=False)
