# 06-Scan.md
# Chapter 6: How to Scan Your Website for Compliance Gaps

Theory is useful. But what you actually need is a way to check your own website
and see what is missing. This chapter gives you a practical, repeatable process.

## The 5-Minute Quick Scan

You can do this right now, without any tools beyond a browser:

**1. Check for HTTPS**
Look at the address bar. Do you see a padlock? If not, your site is not secure.
Visit https://www.ssllabs.com/ssltest/ to check your certificate quality.

**2. Check for a Privacy Policy**
Scroll to the footer of your website. Is there a link called "Privacy Policy" or
"Privacy"? Click it. Does it contain actual information about your data practices,
or is it a generic placeholder?

**3. Check for Cookie Consent**
Open your website in an incognito/private window. Do you see a cookie banner? If
not, tracking cookies are likely being set without consent. Open Developer Tools
→ Application → Cookies and look for any third-party cookies.

**4. Check for an Accessibility Statement**
Look in the footer for "Accessibility" or "Accessibility Statement." If it exists,
does it include a contact method?

**5. Check for a Contact Method**
Is there a clear way for someone to contact you? An email, a form, or a physical
address? This is required under GDPR.

## The Automated Scan (Free)

A more thorough scan checks multiple things at once:

- HTTPS configuration and security headers
- Cookie consent presence
- Privacy policy link in common locations
- Contact information availability
- Form handling (encrypted submission)
- Third-party scripts and data flows
- Accessibility basics (alt text, contrast, keyboard navigation)

The result is a summary of what is present and what is missing, with specific
recommendations for each finding.

## The 30-Minute Compliance Audit

When you are ready for a deeper check, go through this list:

**Security:**
- [ ] SSL/TLS certificate is valid and properly configured
- [ ] All pages redirect to HTTPS
- [ ] Security headers (HSTS, X-Frame-Options, CSP) are present
- [ ] Forms submit over HTTPS

**Data & Privacy:**
- [ ] Privacy policy covers all data collection
- [ ] Cookie consent blocks tracking before consent
- [ ] Consent is recorded (date, time, what was accepted)
- [ ] Data Processing Agreements exist with vendors

**Accessibility:**
- [ ] Alt text on all meaningful images
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Website works with keyboard only (Tab through all interactive elements)
- [ ] Heading hierarchy is logical
- [ ] Forms have visible labels

**Legal:**
- [ ] Contact information is published
- [ ] Accessibility statement is published
- [ ] Terms of service (if applicable) are published
- [ ] Cookie policy is published

## How Often to Scan

- **Quick scan:** Every month (takes 5 minutes)
- **Automated scan:** Every quarter
- **Full audit:** Every 6-12 months, or when you redesign your site

## Tools Mentioned

| Tool | What It Does | Cost |
|------|-------------|------|
| EUComply (free) | Automated compliance scan | Free |
| WAVE browser extension | Accessibility check | Free |
| axe DevTools | Accessibility audit | Free / Pro |
| Lighthouse (Chrome) | Performance + accessibility | Free |
| SSL Labs | HTTPS certificate check | Free |
| Wave | Accessibility evaluation | Free |

## Key Takeaway

You do not need to be an expert to check your own compliance. The automated tools
do the heavy lifting. What matters is that you run the checks regularly and fix
what they find.

**Next chapter:** Building a compliance roadmap — how to prioritize and schedule
the work.