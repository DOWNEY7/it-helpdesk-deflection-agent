# SSO Issues

## Overview
Single Sign-On (SSO) allows employees to authenticate once with their work account and access multiple systems. This article covers common SSO problems and fixes.

## How Corporate SSO Works
Corporate SSO is powered by **Azure AD (Entra ID)**. When you sign into your work laptop, your credentials are passed automatically to SSO-enabled apps including SharePoint, Teams, OneDrive, and internal web apps.

## Common SSO Issues

### "You're not authorised to access this application"
1. Check your M365 licence — some apps require specific licence tiers (see m365-licensing.md)
2. The application may have specific group membership requirements — contact the app owner
3. IT can check your Azure AD group memberships: IT portal → User Management

### Repeatedly asked to sign in
1. Clear browser cache and cookies for the affected site
2. In Edge/Chrome, ensure you're signed into the browser with your **work account**
3. Check that "Stay signed in" is not blocked by privacy settings
4. Go to **https://myaccount.microsoft.com** → Security info → review active sessions
5. If on a personal device: **personal devices are not domain-joined** and may not support SSO — use the web browser version

### SSO not working in a specific browser
- Preferred browser: **Microsoft Edge** (best Azure AD SSO integration)
- Chrome: ensure the **Windows Accounts** extension is enabled
- Firefox: SSO is not natively supported — use Edge or Chrome
- Safari (Mac): configure SSO via Intune Company Portal

### "AADSTS" error codes — what they mean

| Code | Meaning | Fix |
|------|---------|-----|
| AADSTS50020 | User account doesn't exist | Wrong email address — use work email |
| AADSTS50034 | Account disabled | Contact IT — account may be deactivated |
| AADSTS50057 | Account disabled | Leaver account — escalate to IT |
| AADSTS65001 | No consent for app | Admin must grant consent — raise IT request |
| AADSTS70011 | Scope/token error | App may need updating — contact app owner |
| AADSTS90072 | Guest account issue | External user needs explicit permission — IT to grant |

## Granting SSO Access to a New Application

If a business tool needs SSO integration:
1. Raise an **IT Service Desk** request: category **Security → New Application SSO**
2. Provide: application name, vendor, URL, SAML/OIDC metadata document
3. IT will register the app in Azure AD and configure attribute mapping
4. Turnaround: 3–5 business days

## When to Escalate
- SSO breaking for multiple users simultaneously (potential Azure AD outage)
- External partner needing B2B SSO access
- New application SSO integration not completing in 5 days

## Related Articles
- mfa-setup.md
- m365-licensing.md
- password-reset.md
