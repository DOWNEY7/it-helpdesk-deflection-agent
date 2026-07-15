# Microsoft Teams — Troubleshooting

## Overview
This article covers the most common Microsoft Teams issues and how to resolve them, including audio/video problems, calendar sync, and application crashes.

## Teams Not Starting / Crashing on Launch

1. Right-click the Teams icon in the system tray → **Quit**
2. Open Task Manager → End any remaining `Teams.exe` processes
3. Clear the Teams cache:
   - Press **Win + R**, paste: `%appdata%\Microsoft\Teams`
   - Delete these folders: `Cache`, `blob_storage`, `databases`, `GPUCache`, `IndexedDB`, `Local Storage`, `tmp`
4. Restart Teams

> **Note:** Clearing cache will not delete your messages or files — only local temporary data.

## Audio / Video Issues

### Microphone not working in Teams
1. Teams → Settings (⋮ → Settings) → **Devices**
2. Verify the correct microphone is selected
3. Click **Make a test call** to confirm audio works
4. If not listed: Windows Settings → Privacy → Microphone → ensure Teams has permission

### Camera not showing
1. Teams → Settings → **Devices** → check Camera dropdown
2. Close other apps that may be using the camera (Zoom, Skype, etc.)
3. Device Manager → Imaging devices → right-click camera → **Update driver**
4. If still not working: uninstall camera driver and restart (reinstalls automatically)

### Echo or feedback during calls
- Use headphones instead of laptop speakers
- Ask other participants to mute when not speaking
- Check for Bluetooth latency — USB headsets recommended for calls

## Teams Calendar Not Showing Meetings

1. Ensure your mailbox is connected: Teams → Settings → **Calendar** → check account
2. If calendar tab is missing, your Teams policy may not include it — contact IT
3. Rebuild Outlook profile if calendar shows in Outlook but not Teams (see outlook-profile-rebuild.md)
4. Log out of Teams and log back in

## Teams Calls — Poor Quality / Dropping

1. Run the **Network Assessment Tool**: IT portal → Network Tools
2. Check upload speed: minimum 1.5 Mbps needed for HD video calls
3. On VPN: consider requesting split tunnel for Teams traffic (see split-tunneling.md)
4. Disable HD video temporarily: Settings → Devices → **Limit HD Video**

## Teams App vs Web

If the desktop app has issues, use Teams Web at **https://teams.microsoft.com** — identical functionality, no installation required.

## Common Error Messages

| Error | Fix |
|-------|-----|
| "You're missing out! Ask your admin to enable Teams" | Licensing issue — contact IT |
| "We couldn't connect to Teams. Refresh and try again" | Network issue — check VPN/internet |
| "Something went wrong" on login | Clear cache (steps above) |

## When to Escalate
- Teams licence is not assigned (IT must assign via M365 admin)
- Unable to create or join meetings across organisations (federation issue)
- Teams Phone (PSTN) calls not working

## Related Articles
- m365-licensing.md
- outlook-profile-rebuild.md
- onedrive-sync.md
