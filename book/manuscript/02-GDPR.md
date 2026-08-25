# 02-GDPR.md
# GDPR: What Every Website Actually Needs

The General Data Protection Regulation (GDPR) has been in effect since May 2018.
By now, everyone has heard of it. But confusion remains about what a small business
actually needs to do.

## Does GDPR Apply to You?

GDPR applies if you:

- **Are based in the EU** — any business, any size, any website
- **Are outside the EU but sell to or monitor EU residents** — yes, it applies
  to you too

The common myth that "GDPR only applies to companies with 250+ employees" is wrong.
That threshold only affects *record-keeping requirements* (Article 30), not whether
GDPR applies at all.

## The 5 Things Your Website Must Have

### 1. A Privacy Policy

This is the most basic requirement. Your privacy policy must tell visitors:

- What data you collect (name, email, IP address, cookies, etc.)
- Why you collect it (order processing, analytics, marketing)
- How long you keep it
- Who you share it with (payment processors, hosting, analytics tools)
- What rights the visitor has (access, deletion, portability)
- How to contact you

**Practical tip:** Do not copy-paste a generic privacy policy template. It is
obvious to regulators and does not protect you. Customize it to your actual
data practices. If you only collect email addresses for a newsletter, say that.
If you use Google Analytics, say that.

### 2. Cookie Consent (Consent Banner)

If your website uses cookies for anything other than "strictly necessary" functions
(like session management), you need a consent banner that:

- Blocks non-essential cookies **before** consent is given
- Lets users accept or reject specific categories
- Records the consent (for your own documentation)
- Is as easy to reject as to accept (the "cookie wall" approach is illegal)

**What changed in 2026:** The ePrivacy Regulation continues to tighten. Pre-ticked
boxes have been illegal since 2018. The current standard is that rejecting must be
as easy as accepting — no more hidden "Reject" buttons in tiny grey text.

### 3. Contact Information

You must provide a way for data subjects to reach you about their data. This can be
an email address, a contact form, or a physical address. For EU-based businesses,
it is common to include your VAT number and company registration.

### 4. Data Processing Records (if 250+ employees or high-risk processing)

If you have more than 250 employees, or if you process special categories of data
(health, biometrics, political opinions, etc.), you must maintain a Record of
Processing Activities (ROPA). This is a document listing every data processing
activity in your organization.

### 5. Data Processing Agreement with Vendors

If you use third-party services that process data on your behalf — email marketing,
hosting, analytics, payment processing — you need a Data Processing Agreement (DPA)
with each vendor. Many vendors (Shopify, Google, Mailchimp) offer standard DPAs
that you can accept in their dashboard.

## Common GDPR Pitfalls for Small Businesses

| Pitfall | Why It's a Problem | How to Fix |
|---------|-------------------|------------|
| No privacy policy | Basic violation, starting fines | Write one (see Chapter 8 for templates) |
| No cookie consent | Very common, actively enforced | Add a consent banner |
| Data stored forever | Violates storage limitation | Delete old customer data annually |
| Using Google Fonts without hosting locally | German courts have fined for this | Self-host fonts or use system fonts |
| Contact form without HTTPS | Data in transit is unprotected | Check your site has HTTPS |
| Email list without consent records | Cannot prove opt-in | Use a double opt-in system |

## GDPR Fine Levels

GDPR fines are structured in two tiers:

- **Lower tier:** Up to €10 million or 2% of annual global turnover
- **Upper tier:** Up to €20 million or 4% of annual global turnover

In practice, fines for small businesses are rarely at these maximum levels. The
first step from a data protection authority is almost always a warning and a
demand to fix the issue. But fines do happen, and the cost of non-compliance
(including lost business from customers who check) often exceeds the cost of
getting compliant.

## What You Can Do Right Now (5 Minutes)

1. Go to your website. Is there a privacy policy link in the footer? If not, make
   a note to add one.
2. Check if your site has HTTPS (look for the padlock in the address bar). If not,
   fix this immediately — it is free with Cloudflare or Let's Encrypt.
3. Open your browser's developer tools and check for cookies. If you see tracking
   cookies but no consent banner, that is a violation.
4. Look at your email list. Can you prove when and how each person signed up?

**Next chapter:** NIS2 — the security regulation that expands the scope of who
must have documented security measures.