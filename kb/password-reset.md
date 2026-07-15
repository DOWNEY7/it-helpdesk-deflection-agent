# Password Reset

## Overview
This article covers how employees can reset their Windows domain password, Microsoft 365 password, and related account credentials.

## Self-Service Password Reset (SSPR)

Most employees can reset their own password without contacting IT:

1. Visit the SSPR portal: **https://aka.ms/sspr**
2. Enter your work email address and click **Next**
3. Verify your identity using one of the registered methods:
   - **Authenticator app** (preferred) — approve the notification
   - **SMS code** — sent to your registered mobile number
   - **Backup email** — link sent to your personal email
4. Enter your new password twice
5. Click **Finish** — your password is changed immediately

> **Password requirements:** Minimum 12 characters, must include uppercase, lowercase, a number, and a symbol. Cannot reuse your last 10 passwords.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Account not enabled for SSPR" | SSPR not registered | Contact IT to register, or use below |
| "Too many attempts" | Locked out of SSPR | Wait 30 minutes or call IT |
| "Authentication method not found" | No methods registered | IT must perform manual reset |
| "New password doesn't meet requirements" | Policy violation | Check requirements above |

## Manual Reset (IT Team Only)

If SSPR is unavailable or the employee is not registered:

1. Verify the employee's identity (employee ID + manager confirmation)
2. In Active Directory Users and Computers, locate the user account
3. Right-click → **Reset Password**
4. Set a temporary password and tick **User must change password at next logon**
5. Communicate the temporary password via a secure channel (phone, not email)

## When to Escalate

Escalate to Level 2 if:
- The account is disabled (not just locked)
- The user reports they never set up SSPR and cannot verify identity
- The reset affects a service account or shared account
- The account is in a domain trust relationship

## Related Articles
- account-lockout.md
- mfa-setup.md
- sso-issues.md
