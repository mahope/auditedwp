# Monetization Research — Mads-independent revenue paths

Researched 2026-08-25. Goal: find ANY path to first $1 that doesn't require
Mads to unlock Bitwarden, set up new accounts, or perform "udadvendte handlinger
i Mads' navn uden hans ja."

## Executive summary

**No path is 100% Mads-independent** because every monetization channel needs
a real human to register as the payee (tax identity, payout account). However,
the ask varies dramatically:

| Path | What Mads must do | Time | Can I do the rest? |
|------|------------------|------|-------------------|
| Affiliate programs | Sign up (name + email + PayPal) — personal, not business | 5 min | ✅ Everything |
| LS manual fallback | Log into existing LS account, create 6 products | 20 min | ✅ After product URLs |
| Polar.sh | Create account + 1 product in dashboard | 10 min | ✅ Embed + deploy |
| Carbon Ads | Register as publisher | 10 min | ✅ Integrate code |

The hard block (Bitwarden/LS API key) only blocks the *automated* LS setup.
**Plan B (manual LS dashboard)** is fully viable if Mads spends 20 minutes.
Affiliate paths need 5 minutes of Mads' time and zero build work from me.

---

## Ranked options

### 🥇 Option 1: Affiliate links on the existing free scanner (Fastest)

**How it works:**
1. Mads signs up for Cookiebot, Complianz, and/or iubenda affiliate programs
   (5 min each: name, email, PayPal via Impact or their own dashboard).
2. I add affiliate disclosure + referral links to the existing free EUComply
   scanner at auditedwp.pages.dev — specifically:
   - When scan result says "No CMP detected" → recommend Cookiebot with affiliate link
   - On the /template/ (NIS2 checklist) page → sidebar "Get fully compliant" link
   - In the free compliance book manuscript → resource section
3. First commission arrives when someone scans, clicks through, and purchases.

**Commission rates researched:**
- **Cookiebot** (Usercentrics): 30% recurring for 12 months. Premium ~€17/mo →
  ~€5/mo per referral, 12 months. Market leader: 2.4M websites. Via Impact platform.
- **Complianz** (WordPress): 30% on first purchase. Personal €59/yr → ~€17.70
  per referral. Payout via PayPal. Easiest signup: name + email + PayPal.
- **iubenda**: Up to 40% (Impact, application) OR 30% direct referral
  (no application, via ReferralCandy). Plans $5.99-$99/mo. 6-8 week payout.
- **CookieYes**: Checked — affiliate program exists, ~20-30% commission.

**Mads dependency:** ✅ Minimal — 5 min to sign up each program. Just needs
a personal PayPal account (which he likely already has).

**Time to first $1:** Days to weeks (depends on scanner traffic converting).

**Cost:** $0. No build work needed. Affiliate links go into existing pages.

**Risk:** Low. Even if no one buys immediately, the links cost nothing.
Disclosure requirement: add "We earn a commission if you purchase through
this link" — standard FTC compliance.

---

### 🥈 Option 2: Lemon Squeezy manual fallback (Madsen allerede har en konto)

**What's actually blocked:**
The LS API key in Bitwarden. This blocks *automated product creation via script*.

**What's NOT blocked:**
Mads already has a Lemon Squeezy account (`mads@mahope.dk`). LS-MIGRATION.md
Plan B says: log into LS dashboard and create products manually (~20 min).

**The handoff:**
1. Mads logs into app.lemonsqueezy.com (30 sec)
2. Creates 6 products (5 min each, but first one sets pattern — total ~20 min)
   - GDPR DPA Template ($59), NIS2 Clauses ($49), NDA Clauses ($29),
     EAA Statement ($39), Report Kit ($69), Complete Bundle ($149)
3. Copies the 6 checkout URLs into a note or sends them to me
4. I replace the waitlist banners on /store/ with live checkout buttons, deploy
5. First sale goes through LS's Merchant of Record — tax handled, no Stripe/PayPal
   needed from our side

**Mads dependency:** Medium — needs his active participation for ~20 minutes.
But: no unlocking Bitwarden, no new accounts, just using an existing one.

**Time to first $1:** Hours after Mads provides checkout URLs. Products are
already built and the store page exists.

**Cost:** $0. LS takes ~8% fee from each sale (MoR service).

**Note:** This was already the plan before Bitwarden blocked the API key.
Plan B exists in LS-MIGRATION.md — it's just not been actioned because Mads
hasn't done the 20-minute manual step yet.

---

### 🥉 Option 3: Polar.sh — Clean slate, no Bitwarden dependency

**Why this is #3 (not #2):** New account needed. But lower friction than
any other new-account path because Polar.sh is developer-first.

**How it works:**
1. Mads signs up at polar.sh (GitHub OAuth, 30 sec)
2. Creates one product (the Complete Bundle at $149, or any single template)
3. I embed Polar checkout links on the store page
4. Polar acts as Merchant of Record (handles VAT/sales tax globally)
5. Payout: 4% + $0.40 per transaction (cheaper than LS's ~8%)

**Mads dependency:** Medium — needs to create a new account (~3 min) and one
product (5 min). But this is a fresh account with no Bitwarden dependency.

**Time to first $1:** Same-day after Mads creates the account and product.
Even faster than LS manual if Mads acts now, because Polar has fewer steps.

**Why not higher:** It's a new account (which the constraint flags). But the
constraint is about "udadvendte handlinger i Mads' navn" — signing up for
a payment platform to receive your own revenue is arguably an *inward* action.
If Mads is OK with this, it's the cleanest long-term option.

---

## What was ruled out

| Path | Why it doesn't work |
|------|-------------------|
| CodeCanyon/Envato | Author applications CLOSED. Requires gov't ID + tax info when open. |
| Etsy | Requires seller account with ID verification. |
| Gumroad | Already explored, Mads never created account. Uses LS now. |
| Carbon Ads / EthicalAds | Need decent traffic first (chicken-and-egg). Also needs publisher account. |
| "Build something new to sell" | Same account problem — any sales platform needs a seller. |
| Stripe/PayPal direct | Mads would need to set up merchant accounts (harder than LS). |
| Crypto/token | Prohibited by rules ("sketchy"). Volatile. |

## Critical insight

**The manual Lemon Squeezy fallback is probably the actual answer.**
It was documented in LS-MIGRATION.md as Plan B. It needs nothing from
Bitwarden — just 20 minutes of Mads clicking buttons in a dashboard he
already has access to. The 6 products exist, the store page exists, the
descriptions are written. The ONLY missing piece is Mads typing in
6 titles, uploading 6 PDFs, and copying 6 URLs.

If Mads truly won't spend 20 minutes, the affiliate path becomes the
fastest runner-up — and I can do nearly all the work myself (only need
him for the 5-minute signup and his PayPal email).