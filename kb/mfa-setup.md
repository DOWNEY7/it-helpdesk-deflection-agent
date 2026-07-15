# MFA Setup and Troubleshooting

## Overview
Multi-Factor Authentication (MFA) is mandatory for all corporate accounts. This article covers initial setup, adding/removing methods, and common troubleshooting.

## Initial MFA Setup

1. Sign in to **https://aka.ms/mfasetup** with your work account
2. You will be prompted: "More information required" — click **Next**
3. Download **Microsoft Authenticator** on your mobile device
4. Click **Set up Authenticator app** and scan the QR code shown on screen
5. Approve the test notification on your phone
6. Set a backup method (SMS to mobile number) — click **Add method**
7. Click **Done**

## Registering Additional Methods

Visit **https://myaccount.microsoft.com** → **Security info** → **Add method**

Available methods:
- **Authenticator app** (recommended — most secure)
- **Phone (SMS)** — receives a 6-digit code
- **Email** — backup email address
- **FIDO2 security key** — physical USB/NFC key (contact IT)

## Troubleshooting Common Issues

### "I didn't receive the SMS code"
1. Check signal — SMS codes require mobile signal, not Wi-Fi
2. Check the registered number is correct at myaccount.microsoft.com
3. Request a new code (valid for 10 minutes)
4. If still not received, use the Authenticator app instead

### "Authenticator app says the code is wrong"
- Ensure your phone's time is set to **automatic (network time)**
- Go to Authenticator → ⋮ menu → **Refresh accounts**
- If still failing, remove and re-add the account

### "I got a new phone and lost my authenticator codes"
1. Contact IT immediately — account access must be suspended temporarily
2. IT will clear your MFA methods
3. You will be re-enrolled on your new device
4. Never share MFA codes with anyone, including IT staff

### "I keep getting MFA prompts when I'm already signed in"
- Check for multiple signed-in sessions on different devices
- Review sign-in activity at **https://myaccount.microsoft.com/sign-ins**
- If there are unfamiliar locations, escalate to Security immediately

## Temporary Access Pass (for new starters)

IT can issue a **Temporary Access Pass (TAP)** — a time-limited code that bypasses MFA once, allowing initial setup:
1. TAP is valid for 1 hour
2. Use it to sign in and register your permanent MFA method
3. TAPs expire and cannot be reused

## When to Escalate
- User lost all MFA methods and cannot receive a TAP
- Suspicious MFA activity detected (unexpected prompts)
- User reports MFA approval requests they did not initiate (potential account compromise)

## Related Articles
- password-reset.md
- sso-issues.md
- phishing-report.md
