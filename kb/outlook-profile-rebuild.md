# Outlook Profile Rebuild

## Overview
A corrupt Outlook profile causes crashes, missing emails, and calendar issues. Rebuilding the profile resolves most persistent Outlook problems.

## Signs You Need a Profile Rebuild
- Outlook crashes repeatedly on startup
- Calendar items missing or duplicated
- Emails stuck in Outbox
- "Cannot open the Outlook window" error
- AutoComplete suggestions stopped working
- Outlook freezes when opening attachments

## Step 1: Export Your Autocomplete List (Optional)

Autocomplete (email name suggestions) is stored separately. Back it up first:
1. Outlook → File → Options → Mail → **Empty Auto-Complete List** — note: do NOT click this yet
2. Instead, find your `.NK2` file at: `%appdata%\Microsoft\Outlook\`
3. Copy it to a safe location

## Step 2: Rebuild the Profile

1. Close Outlook completely (check Task Manager — end `outlook.exe` if still running)
2. Open **Control Panel** → **Mail (Microsoft Outlook)**
3. Click **Show Profiles**
4. Select your current profile → click **Remove** → confirm
5. Click **Add** to create a new profile:
   - Profile name: your name (e.g., "John Smith")
   - Click **OK**
6. In the account setup, enter your work email address
7. Click **Next** — Outlook will auto-discover your Exchange settings
8. Enter your password when prompted
9. Click **Finish**
10. Set the new profile to **"Always use this profile"**
11. Open Outlook — allow it to sync (may take 10–30 minutes for large mailboxes)

## Step 3: Restore Autocomplete

Copy your backed-up `.NK2` file back to `%appdata%\Microsoft\Outlook\` and rename it to match your new profile name.

## Checking OST File Integrity

If Outlook still has issues after rebuild, run the Inbox Repair Tool:
1. Press **Win + R**, paste: `C:\Program Files\Microsoft Office\root\Office16\SCANPST.EXE`
2. Browse to your `.ost` file (located at `%localappdata%\Microsoft\Outlook\`)
3. Click **Start** — the scan will find and fix errors
4. Repeat until no errors are found

## When to Escalate
- Email profile rebuild does not resolve the issue
- Exchange server errors during profile setup (network/server side)
- Calendar showing another user's items (delegation issue)
- Large mailbox migration required

## Related Articles
- shared-mailbox-access.md
- teams-issues.md
- out-of-office.md
