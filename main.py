"""Volvere.io — AI Business Platform. Landing + Waitlist + Auth + Dashboard."""

import os
from fastapi import FastAPI, Request, Form, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv
from database import init_db, add_waitlist, get_waitlist_count, create_user, get_user, get_users_count, get_all_waitlist
from auth import hash_password, verify_password, create_token, decode_token

load_dotenv()

PORT = int(os.environ.get("PORT", 8080))
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "badrennakkach1@gmail.com")
FINANCE_AGENT_URL = os.environ.get("FINANCE_AGENT_URL", "https://volvere-finance-agent-production.up.railway.app")
ENTREPRENEUR_URL = os.environ.get("ENTREPRENEUR_URL", "")
EMAIL_AGENT_URL = os.environ.get("EMAIL_AGENT_URL", "")
SALES_AGENT_URL = os.environ.get("SALES_AGENT_URL", "")
MARKETING_URL = os.environ.get("MARKETING_URL", "https://volvere-marketing-agent-production.up.railway.app")
GTM_URL = os.environ.get("GTM_URL", "https://web-production-75ae7.up.railway.app")


def _fetch_finance_stats() -> dict:
    """Pull real live stats from the finance agent."""
    try:
        import requests
        r = requests.get(f"{FINANCE_AGENT_URL}/stats", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

app = FastAPI(title="Volvere.io")


@app.on_event("startup")
async def startup():
    init_db()
    # Auto-create admin account
    if not get_user(ADMIN_EMAIL):
        admin_pass = os.environ.get("ADMIN_PASSWORD", "volvere2025!")
        create_user(ADMIN_EMAIL, hash_password(admin_pass), name="Badr", is_admin=True)


def _current_user(token: str = None) -> dict | None:
    if not token:
        return None
    email = decode_token(token)
    if not email:
        return None
    return get_user(email)


CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#04040a;--s:#0a0a15;--b:#14142a;--b2:#1e1e38;--p:#7c3aed;--p2:#9f67ff;--g:#06b6d4;--text:#f0f0ff;--m:#6b6b8a;--m2:#9898b8;--r:14px;--green:#10b981;--red:#ef4444;--gold:#f59e0b}
body{font-family:-apple-system,BlinkMacSystemFont,'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:15px}
a{color:inherit;text-decoration:none}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 28px;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;border:none;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,var(--p),var(--g));color:#fff;box-shadow:0 0 32px rgba(124,58,237,.35)}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 0 48px rgba(124,58,237,.5)}
.btn-outline{background:transparent;color:var(--text);border:1px solid var(--b2)}
.btn-outline:hover{border-color:var(--p2);color:var(--p2)}
.btn-sm{padding:8px 18px;font-size:13px}
nav{position:fixed;top:0;left:0;right:0;z-index:100;padding:0 5%;height:68px;display:flex;align-items:center;justify-content:space-between;background:rgba(4,4,10,.85);backdrop-filter:blur(20px);border-bottom:1px solid rgba(255,255,255,.05)}
.logo{font-size:20px;font-weight:800;background:linear-gradient(135deg,var(--p2),var(--g));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-links{display:flex;align-items:center;gap:32px}
.nav-links a{color:var(--m2);font-size:14px;font-weight:500;transition:color .2s}
.nav-links a:hover{color:var(--text)}
main{padding-top:68px}
section{padding:80px 5%}
.hero{min-height:90vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:120px 5% 80px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-200px;left:50%;transform:translateX(-50%);width:800px;height:800px;background:radial-gradient(circle,rgba(124,58,237,.15) 0%,transparent 70%);pointer-events:none}
.badge{display:inline-flex;align-items:center;gap:8px;background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.3);border-radius:999px;padding:6px 16px;font-size:13px;color:var(--p2);margin-bottom:28px}
.badge-dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
h1{font-size:clamp(36px,6vw,72px);font-weight:800;line-height:1.1;margin-bottom:24px;max-width:900px}
h1 span{background:linear-gradient(135deg,var(--p2),var(--g));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-sub{font-size:clamp(16px,2vw,20px);color:var(--m2);max-width:600px;line-height:1.6;margin-bottom:40px}
.hero-btns{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;margin-bottom:60px}
.stats-row{display:flex;gap:48px;flex-wrap:wrap;justify-content:center}
.stat{text-align:center}
.stat-val{font-size:32px;font-weight:800;background:linear-gradient(135deg,var(--p2),var(--g));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-lbl{font-size:12px;color:var(--m);text-transform:uppercase;letter-spacing:.8px;margin-top:4px}
.agents{background:var(--s)}
h2{font-size:clamp(28px,4vw,42px);font-weight:800;margin-bottom:12px}
.section-sub{color:var(--m2);font-size:16px;margin-bottom:52px;max-width:520px}
.agents-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}
.agent-card{background:var(--bg);border:1px solid var(--b);border-radius:var(--r);padding:28px;transition:all .2s;position:relative;overflow:hidden}
.agent-card:hover{border-color:var(--p);transform:translateY(-3px);box-shadow:0 16px 48px rgba(124,58,237,.15)}
.agent-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--p),var(--g));opacity:0;transition:opacity .2s}
.agent-card:hover::before{opacity:1}
.agent-icon{font-size:32px;margin-bottom:16px}
.agent-name{font-size:18px;font-weight:700;margin-bottom:8px}
.agent-desc{color:var(--m2);font-size:14px;line-height:1.6;margin-bottom:16px}
.agent-tags{display:flex;flex-wrap:wrap;gap:8px}
.tag{background:var(--b);border-radius:999px;padding:4px 12px;font-size:11px;color:var(--m2)}
.live-badge{position:absolute;top:20px;right:20px;background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);border-radius:999px;padding:3px 10px;font-size:11px;color:var(--green);font-weight:600}
.soon-badge{position:absolute;top:20px;right:20px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);border-radius:999px;padding:3px 10px;font-size:11px;color:var(--gold);font-weight:600}
.how{text-align:center}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:32px;margin-top:52px;max-width:900px;margin-left:auto;margin-right:auto}
.step{position:relative}
.step-num{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--g));display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;margin:0 auto 20px}
.step-title{font-size:18px;font-weight:700;margin-bottom:8px}
.step-desc{color:var(--m2);font-size:14px;line-height:1.6}
.pricing{background:var(--s);text-align:center}
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;max-width:900px;margin:52px auto 0}
.plan{background:var(--bg);border:1px solid var(--b);border-radius:var(--r);padding:32px;text-align:left;position:relative}
.plan.featured{border-color:var(--p);box-shadow:0 0 48px rgba(124,58,237,.2)}
.plan-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,var(--p),var(--g));border-radius:999px;padding:4px 16px;font-size:12px;font-weight:700;white-space:nowrap}
.plan-name{font-size:18px;font-weight:700;margin-bottom:4px}
.plan-price{font-size:36px;font-weight:800;margin:16px 0 4px}
.plan-price span{font-size:16px;font-weight:400;color:var(--m2)}
.plan-desc{color:var(--m2);font-size:13px;margin-bottom:24px}
.plan-features{list-style:none;margin-bottom:28px}
.plan-features li{padding:8px 0;font-size:14px;color:var(--m2);border-bottom:1px solid rgba(255,255,255,.04);display:flex;align-items:center;gap:10px}
.plan-features li::before{content:'✓';color:var(--green);font-weight:700}
.waitlist{text-align:center;padding:100px 5%}
.wl-box{background:var(--s);border:1px solid var(--b);border-radius:20px;padding:60px;max-width:600px;margin:0 auto;position:relative;overflow:hidden}
.wl-box::before{content:'';position:absolute;top:-100px;right:-100px;width:300px;height:300px;background:radial-gradient(circle,rgba(124,58,237,.2),transparent 70%);pointer-events:none}
.wl-form{display:flex;gap:12px;margin-top:28px;flex-wrap:wrap}
.wl-input{flex:1;min-width:200px;background:var(--b);border:1px solid var(--b2);border-radius:10px;padding:13px 18px;color:var(--text);font-size:14px;outline:none;transition:border-color .2s}
.wl-input:focus{border-color:var(--p)}
.alert-success{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:10px;padding:14px 20px;color:var(--green);font-size:14px;margin-top:16px}
.alert-error{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:10px;padding:14px 20px;color:var(--red);font-size:14px;margin-top:16px}
footer{border-top:1px solid var(--b);padding:40px 5%;text-align:center;color:var(--m);font-size:13px}
.auth-page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:80px 20px}
.auth-box{background:var(--s);border:1px solid var(--b);border-radius:20px;padding:48px;width:100%;max-width:420px}
.auth-title{font-size:28px;font-weight:800;margin-bottom:8px}
.auth-sub{color:var(--m2);font-size:14px;margin-bottom:32px}
.form-group{margin-bottom:20px}
.form-label{display:block;font-size:13px;font-weight:600;color:var(--m2);margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}
.form-input{width:100%;background:var(--b);border:1px solid var(--b2);border-radius:10px;padding:13px 16px;color:var(--text);font-size:14px;outline:none;transition:border-color .2s}
.form-input:focus{border-color:var(--p)}
.form-btn{width:100%;padding:14px;font-size:15px}
.dash-layout{display:flex;min-height:100vh;padding-top:68px}
.sidebar{width:240px;background:var(--s);border-right:1px solid var(--b);padding:28px 0;position:fixed;top:68px;bottom:0;overflow-y:auto}
.sidebar-item{display:flex;align-items:center;gap:12px;padding:12px 24px;font-size:14px;color:var(--m2);transition:all .2s;cursor:pointer}
.sidebar-item:hover,.sidebar-item.active{background:rgba(124,58,237,.1);color:var(--text);border-right:2px solid var(--p)}
.sidebar-icon{font-size:18px}
.dash-main{margin-left:240px;flex:1;padding:40px}
.dash-header{margin-bottom:36px}
.dash-title{font-size:28px;font-weight:800;margin-bottom:6px}
.dash-sub{color:var(--m2);font-size:14px}
.dash-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:36px}
.dash-card{background:var(--s);border:1px solid var(--b);border-radius:var(--r);padding:24px}
.dash-card-val{font-size:32px;font-weight:800;margin-bottom:4px}
.dash-card-lbl{font-size:11px;color:var(--m);text-transform:uppercase;letter-spacing:.5px}
.agent-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.agent-item{background:var(--s);border:1px solid var(--b);border-radius:var(--r);padding:24px;display:flex;align-items:center;gap:18px;transition:all .2s}
.agent-item:hover{border-color:var(--p);transform:translateX(4px)}
.agent-item-icon{font-size:28px;width:52px;height:52px;display:flex;align-items:center;justify-content:center;background:var(--b);border-radius:12px}
.agent-item-info{flex:1}
.agent-item-name{font-size:16px;font-weight:700;margin-bottom:4px}
.agent-item-desc{font-size:12px;color:var(--m2)}
.status-live{color:var(--green);font-size:11px;font-weight:600}
@media(max-width:768px){.sidebar{display:none}.dash-main{margin-left:0}.hero-btns{flex-direction:column;align-items:center}.wl-form{flex-direction:column}.plans{grid-template-columns:1fr}}
"""


def _nav(user=None):
    if user:
        return f"""<nav>
  <a class="logo" href="/">Volvere.io</a>
  <div class="nav-links">
    <a href="/dashboard">Dashboard</a>
    <a href="/logout" class="btn btn-outline btn-sm">Log out</a>
  </div>
</nav>"""
    return """<nav>
  <a class="logo" href="/">Volvere.io</a>
  <div class="nav-links">
    <a href="/#agents">Agents</a>
    <a href="/#pricing">Pricing</a>
    <a href="/login" class="btn btn-outline btn-sm">Log in</a>
    <a href="/#waitlist" class="btn btn-primary btn-sm">Join Waitlist</a>
  </div>
</nav>"""


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request, token: str = Cookie(default=None), msg: str = ""):
    user = _current_user(token)
    wl_count = get_waitlist_count()

    success_msg = ""
    if msg == "joined":
        success_msg = '<div class="alert-success">🎉 You\'re on the list! We\'ll notify you when early access opens.</div>'
    elif msg == "exists":
        success_msg = '<div class="alert-error">This email is already on the waitlist.</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Volvere.io — AI Agents That Work While You Sleep</title>
<style>{CSS}</style>
</head>
<body>
{_nav(user)}
<main>

<!-- HERO -->
<section class="hero">
  <div class="badge"><span class="badge-dot"></span> Now in Early Access · {wl_count} people waiting</div>
  <h1>Your AI Business Team.<br><span>Always On.</span></h1>
  <p class="hero-sub">A complete suite of AI agents — financial analyst, entrepreneur advisor, sales intelligence & automated outreach — running 24/7 so you don't have to.</p>
  <div class="hero-btns">
    <a href="#waitlist" class="btn btn-primary">🚀 Join the Waitlist</a>
    <a href="#agents" class="btn btn-outline">See All Agents →</a>
  </div>
  <div class="stats-row">
    <div class="stat"><div class="stat-val">7</div><div class="stat-lbl">AI Agents</div></div>
    <div class="stat"><div class="stat-val">24/7</div><div class="stat-lbl">Monitoring</div></div>
    <div class="stat"><div class="stat-val">3</div><div class="stat-lbl">Markets</div></div>
    <div class="stat"><div class="stat-val">∞</div><div class="stat-lbl">Automations</div></div>
  </div>
</section>

<!-- AGENTS -->
<section class="agents" id="agents">
  <h2>Every agent you need.</h2>
  <p class="section-sub">Each agent runs independently, alerts you on Telegram, and handles its job without you.</p>
  <div class="agents-grid">
    <div class="agent-card">
      <span class="live-badge">● LIVE</span>
      <div class="agent-icon">🌍</div>
      <div class="agent-name">Financial Intelligence</div>
      <div class="agent-desc">Monitors UAE/MENA, Morocco & Global markets. FinBERT + Claude sentiment scoring. BUY/SELL signals, volume spikes, profit alerts on Telegram.</div>
      <div class="agent-tags"><span class="tag">DFM · ADX</span><span class="tag">Morocco CSE</span><span class="tag">Crypto</span><span class="tag">Gold · Oil</span></div>
    </div>
    <div class="agent-card">
      <span class="live-badge">● LIVE</span>
      <div class="agent-icon">🧠</div>
      <div class="agent-name">Entrepreneur Advisor</div>
      <div class="agent-desc">Upload PDFs, paste URLs, chat with your AI business advisor. Get a 3×3 strategy matrix with GO/NO-GO decisions for any venture.</div>
      <div class="agent-tags"><span class="tag">PDF Analysis</span><span class="tag">URL Scraping</span><span class="tag">Strategy</span></div>
    </div>
    <div class="agent-card">
      <span class="live-badge">● LIVE</span>
      <div class="agent-icon">📧</div>
      <div class="agent-name">Email & Outreach</div>
      <div class="agent-desc">Finds prospects, writes personalised emails, sends auto follow-up sequences on Day 3/7/14/21. Injects your Calendly link automatically.</div>
      <div class="agent-tags"><span class="tag">5-Touch Sequence</span><span class="tag">Calendly</span><span class="tag">Auto Follow-up</span></div>
    </div>
    <div class="agent-card">
      <span class="live-badge">● LIVE</span>
      <div class="agent-icon">💼</div>
      <div class="agent-name">Sales Intelligence</div>
      <div class="agent-desc">Scores inbound leads 0–100. Telegram alerts for hot leads. Tier detection (T1/T2/T3/DQ) with next action recommendations.</div>
      <div class="agent-tags"><span class="tag">Lead Scoring</span><span class="tag">Telegram Alerts</span><span class="tag">Pipeline</span></div>
    </div>
    <div class="agent-card">
      <span class="live-badge">● LIVE</span>
      <div class="agent-icon">📣</div>
      <div class="agent-name">Marketing Agent</div>
      <div class="agent-desc">13-skill SEO and ads intelligence agent. Content strategy, keyword research, ad copy, competitive analysis — all automated.</div>
      <div class="agent-tags"><span class="tag">SEO</span><span class="tag">Ad Copy</span><span class="tag">Content</span></div>
    </div>
    <div class="agent-card">
      <span class="live-badge">● LIVE</span>
      <div class="agent-icon">🚀</div>
      <div class="agent-name">GTM Engineer</div>
      <div class="agent-desc">Go-to-market strategy, HubSpot integration, ICP definition, channel prioritisation. Your AI head of growth.</div>
      <div class="agent-tags"><span class="tag">HubSpot</span><span class="tag">ICP</span><span class="tag">GTM</span></div>
    </div>
    <div class="agent-card">
      <span class="soon-badge">COMING SOON</span>
      <div class="agent-icon">🤖</div>
      <div class="agent-name">Crypto Trading Bot</div>
      <div class="agent-desc">Automated spot trading on LBank and Binance. Technical analysis, entry/exit signals, risk management — running 24/7.</div>
      <div class="agent-tags"><span class="tag">LBank</span><span class="tag">Binance</span><span class="tag">Spot Trading</span></div>
    </div>
  </div>
</section>

<!-- HOW IT WORKS -->
<section class="how" id="how">
  <h2>How it works.</h2>
  <p class="section-sub" style="margin:0 auto 0">Simple setup. Immediate results.</p>
  <div class="steps">
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-title">Join & Configure</div>
      <div class="step-desc">Sign up, connect your Telegram, set your markets and preferences. Takes 5 minutes.</div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div class="step-title">Agents Go to Work</div>
      <div class="step-desc">All 7 agents activate immediately — scanning news, scoring leads, sending outreach, monitoring prices.</div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div class="step-title">You Get Alerts</div>
      <div class="step-desc">Receive Telegram alerts for BUY signals, hot leads, take-profit levels, and new opportunities. You decide, agents execute.</div>
    </div>
  </div>
</section>

<!-- PRICING -->
<section class="pricing" id="pricing">
  <h2>Simple pricing.</h2>
  <p class="section-sub" style="margin:0 auto 12px">Start free. Scale when you grow.</p>
  <div class="plans">
    <div class="plan">
      <div class="plan-name">Starter</div>
      <div class="plan-price">Free <span>/ forever</span></div>
      <div class="plan-desc">For individuals getting started</div>
      <ul class="plan-features">
        <li>Financial Intelligence Agent</li>
        <li>Entrepreneur Advisor</li>
        <li>50 Telegram alerts / month</li>
        <li>1 market (UAE or Global)</li>
      </ul>
      <a href="#waitlist" class="btn btn-outline" style="width:100%;justify-content:center">Join Waitlist</a>
    </div>
    <div class="plan featured">
      <div class="plan-badge">Most Popular</div>
      <div class="plan-name">Pro</div>
      <div class="plan-price">$49 <span>/ month</span></div>
      <div class="plan-desc">For founders & active investors</div>
      <ul class="plan-features">
        <li>All 7 AI Agents</li>
        <li>All 3 markets (UAE + Morocco + Global)</li>
        <li>Unlimited Telegram alerts</li>
        <li>Email outreach sequences</li>
        <li>Volume spike + profit tracking</li>
        <li>Priority support</li>
      </ul>
      <a href="#waitlist" class="btn btn-primary" style="width:100%;justify-content:center">Join Waitlist</a>
    </div>
    <div class="plan">
      <div class="plan-name">Agency</div>
      <div class="plan-price">$199 <span>/ month</span></div>
      <div class="plan-desc">For teams & agencies</div>
      <ul class="plan-features">
        <li>Everything in Pro</li>
        <li>5 team seats</li>
        <li>Custom agent configuration</li>
        <li>White-label dashboard</li>
        <li>Dedicated onboarding</li>
      </ul>
      <a href="#waitlist" class="btn btn-outline" style="width:100%;justify-content:center">Contact Us</a>
    </div>
  </div>
</section>

<!-- WAITLIST -->
<section class="waitlist" id="waitlist">
  <div class="wl-box">
    <div style="font-size:40px;margin-bottom:16px">🚀</div>
    <h2>Get early access.</h2>
    <p style="color:var(--m2);font-size:15px;margin-top:8px;line-height:1.6">Join {wl_count} founders and investors waiting for launch. Early members get Pro free for 3 months.</p>
    <form action="/waitlist" method="post">
      <div class="wl-form">
        <input class="wl-input" type="text" name="name" placeholder="Your name" required/>
        <input class="wl-input" type="email" name="email" placeholder="Your email" required/>
      </div>
      <input class="wl-input" type="text" name="company" placeholder="Company / project (optional)" style="width:100%;margin-top:12px"/>
      <button class="btn btn-primary" type="submit" style="width:100%;margin-top:16px;justify-content:center;font-size:15px;padding:15px">Join the Waitlist →</button>
    </form>
    {success_msg}
  </div>
</section>

</main>
<footer>
  <div class="logo" style="margin-bottom:12px">Volvere.io</div>
  <p>AI agents that work while you sleep. Built for founders, investors, and operators.</p>
  <p style="margin-top:8px"><a href="/login" style="color:var(--m2)">Log in</a> · <a href="mailto:badrennakkach1@gmail.com" style="color:var(--m2)">Contact</a></p>
</footer>
</body>
</html>"""


@app.post("/waitlist")
async def join_waitlist(email: str = Form(...), name: str = Form(""), company: str = Form("")):
    ok = add_waitlist(email, name, company)
    redirect = "/?msg=joined" if ok else "/?msg=exists"
    return RedirectResponse(redirect + "#waitlist", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(error: str = "", token: str = Cookie(default=None)):
    if _current_user(token):
        return RedirectResponse("/dashboard")
    err = f'<div class="alert-error">{error}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Log in — Volvere.io</title><style>{CSS}</style></head>
<body>
{_nav()}
<div class="auth-page">
  <div class="auth-box">
    <div class="logo" style="margin-bottom:24px;font-size:24px">Volvere.io</div>
    <div class="auth-title">Welcome back</div>
    <div class="auth-sub">Log in to your agent dashboard</div>
    <form action="/login" method="post">
      <div class="form-group">
        <label class="form-label">Email</label>
        <input class="form-input" type="email" name="email" placeholder="you@example.com" required autofocus/>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input class="form-input" type="password" name="password" placeholder="••••••••" required/>
      </div>
      {err}
      <button class="btn btn-primary form-btn" type="submit" style="margin-top:8px">Log in →</button>
    </form>
    <p style="text-align:center;margin-top:20px;font-size:14px;color:var(--m2)">Don't have an account? <a href="/register" style="color:var(--p2)">Sign up</a></p>
  </div>
</div>
</body></html>"""


@app.post("/login")
async def do_login(response: Response, email: str = Form(...), password: str = Form(...)):
    user = get_user(email)
    if not user or not verify_password(password, user["password_hash"]):
        return RedirectResponse("/login?error=Invalid+email+or+password", status_code=303)
    token = create_token(email)
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie("token", token, max_age=86400 * 7, httponly=True, samesite="lax")
    return resp


@app.get("/register", response_class=HTMLResponse)
async def register_page(error: str = "", token: str = Cookie(default=None)):
    if _current_user(token):
        return RedirectResponse("/dashboard")
    err = f'<div class="alert-error">{error}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Sign up — Volvere.io</title><style>{CSS}</style></head>
<body>
{_nav()}
<div class="auth-page">
  <div class="auth-box">
    <div class="logo" style="margin-bottom:24px;font-size:24px">Volvere.io</div>
    <div class="auth-title">Create account</div>
    <div class="auth-sub">Join the Volvere platform</div>
    <form action="/register" method="post">
      <div class="form-group">
        <label class="form-label">Name</label>
        <input class="form-input" type="text" name="name" placeholder="Your name" required autofocus/>
      </div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input class="form-input" type="email" name="email" placeholder="you@example.com" required/>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input class="form-input" type="password" name="password" placeholder="Min. 8 characters" required/>
      </div>
      {err}
      <button class="btn btn-primary form-btn" type="submit" style="margin-top:8px">Create Account →</button>
    </form>
    <p style="text-align:center;margin-top:20px;font-size:14px;color:var(--m2)">Already have an account? <a href="/login" style="color:var(--p2)">Log in</a></p>
  </div>
</div>
</body></html>"""


@app.post("/register")
async def do_register(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if len(password) < 8:
        return RedirectResponse("/register?error=Password+must+be+at+least+8+characters", status_code=303)
    ok = create_user(email, hash_password(password), name)
    if not ok:
        return RedirectResponse("/register?error=Email+already+registered", status_code=303)
    resp = RedirectResponse("/dashboard", status_code=303)
    token = create_token(email)
    resp.set_cookie("token", token, max_age=86400 * 7, httponly=True, samesite="lax")
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("token")
    return resp


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(token: str = Cookie(default=None)):
    user = _current_user(token)
    if not user:
        return RedirectResponse("/login")

    name = user.get("name") or user.get("email", "").split("@")[0]
    is_admin = user.get("is_admin") or user.get("is_admin") == 1
    wl_count = get_waitlist_count()
    users_count = get_users_count()

    # Real live stats from finance agent
    finance_stats = _fetch_finance_stats()
    fin_total = finance_stats.get("total", "—")
    fin_buys = finance_stats.get("buys", "—")
    fin_alerts = finance_stats.get("alerts_sent", "—")

    agents = [
        {"icon": "🌍", "name": "Financial Intelligence", "desc": "Market signals, BUY/SELL alerts, volume spikes", "url": FINANCE_AGENT_URL, "live": True},
        {"icon": "🧠", "name": "Entrepreneur Advisor", "desc": "PDF analysis, URL scraping, strategy matrix", "url": ENTREPRENEUR_URL or None, "live": bool(ENTREPRENEUR_URL)},
        {"icon": "📧", "name": "Email & Outreach", "desc": "Auto follow-up sequences, Calendly integration", "url": EMAIL_AGENT_URL or None, "live": bool(EMAIL_AGENT_URL)},
        {"icon": "💼", "name": "Sales Intelligence", "desc": "Lead scoring 0–100, hot lead Telegram alerts", "url": SALES_AGENT_URL or None, "live": bool(SALES_AGENT_URL)},
        {"icon": "📣", "name": "Marketing Agent", "desc": "SEO, ad copy, content strategy", "url": MARKETING_URL or None, "live": bool(MARKETING_URL)},
        {"icon": "🚀", "name": "GTM Engineer", "desc": "Go-to-market strategy, HubSpot integration", "url": GTM_URL or None, "live": bool(GTM_URL)},
        {"icon": "🤖", "name": "Crypto Trading Bot", "desc": "LBank & Binance spot trading", "url": None, "live": False},
    ]

    live_count = sum(1 for a in agents if a["live"])

    agent_rows = ""
    for a in agents:
        status = '<span class="status-live">● LIVE</span>' if a["live"] else '<span style="color:var(--gold);font-size:11px;font-weight:600">COMING SOON</span>'
        if a["url"]:
            agent_rows += f"""<a href="{a['url']}" target="_blank">
            <div class="agent-item">
              <div class="agent-item-icon">{a['icon']}</div>
              <div class="agent-item-info">
                <div class="agent-item-name">{a['name']}</div>
                <div class="agent-item-desc">{a['desc']}</div>
              </div>
              {status}
            </div></a>"""
        else:
            agent_rows += f"""<div class="agent-item" style="opacity:.6;cursor:default">
              <div class="agent-item-icon">{a['icon']}</div>
              <div class="agent-item-info">
                <div class="agent-item-name">{a['name']}</div>
                <div class="agent-item-desc">{a['desc']}</div>
              </div>
              {status}
            </div>"""

    admin_section = ""
    if is_admin:
        waitlist = get_all_waitlist()
        wl_rows = "".join([
            f"<tr><td style='padding:8px 12px;font-size:13px'>{w['email']}</td>"
            f"<td style='padding:8px 12px;font-size:13px;color:var(--m2)'>{w.get('name','')}</td>"
            f"<td style='padding:8px 12px;font-size:13px;color:var(--m2)'>{w.get('company','')}</td>"
            f"<td style='padding:8px 12px;font-size:11px;color:var(--m)'>{(w.get('created_at') or '')[:16]}</td></tr>"
            for w in waitlist
        ])
        admin_section = f"""
        <div style="margin-top:40px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
            <h3 style="font-size:18px;font-weight:700">👑 Waitlist — {wl_count} signups</h3>
            <a href="/admin/waitlist.csv" class="btn btn-outline btn-sm">⬇ Export CSV</a>
          </div>
          <div style="background:var(--s);border:1px solid var(--b);border-radius:var(--r);overflow:hidden">
            <table style="width:100%;border-collapse:collapse">
              <thead><tr style="background:var(--b)">
                <th style="padding:10px 12px;text-align:left;font-size:11px;color:var(--m);text-transform:uppercase">Email</th>
                <th style="padding:10px 12px;text-align:left;font-size:11px;color:var(--m);text-transform:uppercase">Name</th>
                <th style="padding:10px 12px;text-align:left;font-size:11px;color:var(--m);text-transform:uppercase">Company</th>
                <th style="padding:10px 12px;text-align:left;font-size:11px;color:var(--m);text-transform:uppercase">Joined</th>
              </tr></thead>
              <tbody>{wl_rows if wl_rows else '<tr><td colspan="4" style="padding:20px;text-align:center;color:var(--m)">No waitlist entries yet</td></tr>'}</tbody>
            </table>
          </div>
        </div>"""

    sidebar_links = [
        ("⚡", "Dashboard", "/dashboard"),
        ("🌍", "Finance Agent", FINANCE_AGENT_URL),
        ("🧠", "Entrepreneur", ENTREPRENEUR_URL or "/dashboard"),
        ("📧", "Email Agent", EMAIL_AGENT_URL or "/dashboard"),
        ("💼", "Sales Agent", SALES_AGENT_URL or "/dashboard"),
        ("📣", "Marketing", MARKETING_URL or "/dashboard"),
        ("🚀", "GTM Agent", GTM_URL or "/dashboard"),
    ]
    sidebar_html = "".join([
        f'<a href="{url}" {"target=\"_blank\"" if url.startswith("http") and url != "/dashboard" else ""}>'
        f'<div class="sidebar-item{"  active" if url == "/dashboard" else ""}"><span class="sidebar-icon">{icon}</span> {label}</div></a>'
        for icon, label, url in sidebar_links
    ])

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Dashboard — Volvere.io</title><style>{CSS}</style></head>
<body>
{_nav(user)}
<div class="dash-layout">
  <div class="sidebar">
    {sidebar_html}
    <div style="border-top:1px solid var(--b);margin:16px 0"></div>
    <a href="/logout"><div class="sidebar-item"><span class="sidebar-icon">🚪</span> Log out</div></a>
  </div>
  <div class="dash-main">
    <div class="dash-header">
      <div class="dash-title">Good day, {name} 👋</div>
      <div class="dash-sub">Your AI business team is running 24/7. Here's your live overview.</div>
    </div>
    <div class="dash-grid">
      <div class="dash-card">
        <div class="dash-card-val" style="color:var(--green)">{live_count}</div>
        <div class="dash-card-lbl">Live Agents</div>
      </div>
      <div class="dash-card">
        <div class="dash-card-val" style="color:var(--p2)">{fin_total}</div>
        <div class="dash-card-lbl">Signals Analyzed</div>
      </div>
      <div class="dash-card">
        <div class="dash-card-val" style="color:var(--green)">{fin_buys}</div>
        <div class="dash-card-lbl">BUY Signals</div>
      </div>
      <div class="dash-card">
        <div class="dash-card-val" style="color:var(--gold)">{fin_alerts}</div>
        <div class="dash-card-lbl">Telegram Alerts</div>
      </div>
      <div class="dash-card">
        <div class="dash-card-val" style="color:var(--g)">{wl_count}</div>
        <div class="dash-card-lbl">Waitlist</div>
      </div>
      <div class="dash-card">
        <div class="dash-card-val" style="color:var(--m2)">{users_count}</div>
        <div class="dash-card-lbl">Users</div>
      </div>
    </div>
    <h3 style="font-size:18px;font-weight:700;margin-bottom:16px">Your Agents</h3>
    <div class="agent-list">{agent_rows}</div>
    {admin_section}
  </div>
</div>
</body></html>"""


from fastapi.responses import PlainTextResponse

@app.get("/admin/waitlist.csv", response_class=PlainTextResponse)
async def export_waitlist(token: str = Cookie(default=None)):
    user = _current_user(token)
    if not user or not (user.get("is_admin") or user.get("is_admin") == 1):
        return RedirectResponse("/login")
    rows = get_all_waitlist()
    lines = ["email,name,company,joined"]
    for w in rows:
        lines.append(f"{w['email']},{w.get('name','')},{w.get('company','')},{(w.get('created_at') or '')[:16]}")
    return PlainTextResponse("\n".join(lines), headers={"Content-Disposition": "attachment; filename=waitlist.csv"})


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
