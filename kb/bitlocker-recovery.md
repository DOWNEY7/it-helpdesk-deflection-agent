# BitLocker Recovery

## Overview
BitLocker encrypts your hard drive. If BitLocker asks for a recovery key at startup, this article explains how to retrieve it.

## Why BitLocker Recovery Key is Requested

- Hardware change detected (new motherboard, TPM chip replaced)
- Too many wrong PIN/password attempts
- System integrity check failed (possible firmware or boot file change)
- Boot order changed in BIOS
- TPM disabled or cleared in BIOS

## Getting Your Recovery Key

Recovery keys are backed up to Azure AD automatically. Retrieve yours in under 2 minutes:

### Option 1: Self-Service (Microsoft Account / Azure AD)
1. Visit **https://aka.ms/myrecoverykey** on another device
2. Sign in with your work email
3. Your recovery key will be displayed — it's a 48-digit number
4. Enter this key at the BitLocker screen to unlock your device

### Option 2: IT Helpdesk
1. Contact IT with your device serial number (printed on a sticker on the laptop base)
2. IT will look up the recovery key in Azure AD
3. IT will read the key to you — **never ask IT to email it unencrypted**

### Option 3: Active Directory (Corporate IT Only)
For domain-joined devices: recovery keys are stored in ADDS.
- Open ADUC → find the computer object → Attribute Editor → `msFVE-RecoveryPassword`
- Requires Domain Admin or delegated BitLocker recovery role

## After Entering the Recovery Key

Once unlocked, investigate the root cause:
1. Open **BitLocker Management** (search in Start menu)
2. Check the **Protection Status** — if suspended, re-enable
3. If TPM-related: Trusted Platform Module Management → **Clear TPM** (only if directed by IT)
4. Restart the device to confirm it boots normally

## BitLocker Not Enabled on My Device

BitLocker is mandatory on all corporate laptops. If it is not enabled:
1. IT will enable it remotely via Intune within 24 hours of device enrolment
2. To manually enable: Settings → Privacy & Security → **Device Encryption** → Turn on
3. Ensure you are signed in with your work account (not a local account) for key backup

## When to Escalate
- Recovery key is not found in Azure AD or ADUC (key not backed up — data may be unrecoverable)
- Device fails to boot even after entering the correct recovery key
- Recovery key was entered but hardware fault suspected

## Related Articles
- phishing-report.md
- usb-block-policy.md
