# Account Lockout

## Overview
An account becomes locked after too many failed login attempts. This article explains how to unlock accounts and prevent future lockouts.

## Lockout Policy

- **Threshold:** 5 failed attempts within 10 minutes
- **Lockout duration:** 30 minutes (auto-unlocks)
- **Reset observation window:** 10 minutes after last failed attempt

## Self-Unlock Options

### Option 1: Wait
The account automatically unlocks after **30 minutes**. No action needed.

### Option 2: Self-Service Password Reset
1. Go to **https://aka.ms/sspr**
2. Follow the identity verification steps
3. Reset your password — this also unlocks the account

### Option 3: Contact IT Helpdesk
Call or chat the IT helpdesk who can unlock in under 2 minutes.

## IT Team: How to Unlock an Account

**Via Active Directory:**
1. Open **Active Directory Users and Computers**
2. Search for the user's username or email
3. Double-click the account → **Account** tab
4. Tick **Unlock Account** → click **OK**

**Via PowerShell:**
```powershell
Unlock-ADAccount -Identity "username"
Get-ADUser -Identity "username" -Properties LockedOut | Select LockedOut
```

## Common Lockout Causes

| Cause | Solution |
|-------|----------|
| Cached credentials on old device | Remove saved credentials from Windows Credential Manager |
| Mobile device with old password | Update Exchange account password on phone |
| Mapped drive with old credentials | Update or remap the network drive |
| Service running under user account | Update service credentials in Services console |
| VPN client using old credentials | Update VPN profile credentials |

## Identifying the Lockout Source

Run this to find the device causing repeated lockouts:

```powershell
Get-WinEvent -ComputerName DC01 -FilterHashtable @{
    LogName='Security'; Id=4740
} | Select TimeCreated, Message | Format-List
```

Look for `Caller Computer Name` in the event message.

## When to Escalate
- Account locked repeatedly (3+ times in one day) — may indicate a security incident
- Account disabled (not locked) — requires management approval to re-enable
- Lockout source is an unknown device — escalate to Security team

## Related Articles
- password-reset.md
- mfa-setup.md
