# Shared Mailbox Access

## Overview
Shared mailboxes allow multiple employees to send and receive from a single email address (e.g., `support@company.com`). This article covers access setup and common issues.

## Requesting Access to a Shared Mailbox

1. Raise a request via the **IT Service Desk** (https://servicedesk.company.internal)
2. Category: **Email → Shared Mailbox Access**
3. Provide: mailbox address, your name, access level needed (Read / Send As / Full Access)
4. **Manager approval required** for Send As and Full Access
5. Access is provisioned within **1 business day**

## Adding the Shared Mailbox in Outlook (Auto-mapping)

If you have Full Access, the shared mailbox may appear automatically in Outlook within 30 minutes. If not:

### Outlook Desktop
1. File → **Account Settings** → Account Settings
2. Select your email account → **Change**
3. More Settings → **Advanced** tab → **Add**
4. Type the shared mailbox address → **OK** → **Apply**
5. Restart Outlook

### Outlook Web (OWA)
1. Go to **https://outlook.office.com**
2. Right-click **Folders** in the left panel → **Add shared folder**
3. Type the shared mailbox address → **Add**

## Sending From the Shared Mailbox

### In Outlook Desktop:
1. Open a new email → click the **From** field
2. Select **Other email address**
3. Type the shared mailbox address
4. Click **OK** — the email will appear to come from the shared mailbox

### In OWA:
1. New message → click **...** next to the From field
2. Select the shared mailbox from the list (if you have Send As permission)

## Common Issues

| Issue | Fix |
|-------|-----|
| "You don't have permission to send from this mailbox" | Request Send As access via IT (Full Access ≠ Send As) |
| Mailbox not appearing after access granted | Wait up to 30 minutes; restart Outlook |
| Sent items not showing in shared mailbox | Outlook → File → Options → Mail → tick "Save copies to Sent Items folder of shared mailbox" |
| Cannot delete emails in shared mailbox | Requires Delete Items permission — request via IT |

## Removing Access

When an employee leaves or no longer needs access, the manager must raise an IT request to remove their access immediately.

## When to Escalate
- Shared mailbox has not been created yet
- Mailbox size limit reached (50GB default)
- External email not reaching the shared mailbox

## Related Articles
- distribution-list.md
- out-of-office.md
- mail-flow-rules.md
