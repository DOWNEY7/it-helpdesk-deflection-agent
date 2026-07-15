# Slow Computer

## Overview
A slow computer affects productivity. This article covers self-service steps to diagnose and fix performance issues before raising a support ticket.

## Quick Wins (Try First)

1. **Restart your computer** — clears memory leaks and applies pending updates (most effective fix)
2. **Check disk space** — low disk space severely impacts performance:
   - Settings → System → Storage
   - Minimum 10GB free on the C: drive
   - Run **Storage Sense** to automatically clean up temp files
3. **Check for Windows Updates** — outdated drivers and OS cause slowdowns:
   - Settings → Windows Update → Check for updates
4. **Close unused apps** — too many apps in the background consume RAM

## Diagnosing with Task Manager

Press **Ctrl + Shift + Esc** → click **More details**

| Tab | What to look for |
|-----|-----------------|
| **CPU** | Sustained usage above 80% — identifies the offending process |
| **Memory** | Above 90% usage — indicates RAM shortage |
| **Disk** | Sustained 100% — disk bottleneck |
| **Network** | Unexpected high usage — may indicate malware or a runaway sync |

### High CPU / Memory process
1. In Task Manager → right-click the heavy process → **End task**
2. If it's a system process (svchost, SearchIndexer), do not end it — restart instead
3. Report persistent issues to IT with the process name

## Cleaning Up Disk Space

```
Win + R → cleanmgr → Select C: → Check all options → Clean up system files
```

Also clean:
- **Downloads** folder — delete files older than 3 months
- **Teams cache**: `%appdata%\Microsoft\Teams` — delete `Cache` and `tmp` folders
- **Outlook cache**: File → Account Settings → Data Files — compact your .ost file

## Startup Programs

Many apps set themselves to start automatically:
1. Task Manager → **Startup** tab
2. Disable any non-essential apps (e.g., Spotify, Steam, personal cloud backup)
3. Only disable apps you recognise — leave corporate security tools alone

## Scheduled Maintenance

For persistent slowness after the above steps:
1. IT runs a monthly maintenance scan via **CrowdStrike** and **SCCM**
2. Ensure your device is on the network at least once a week to receive patches
3. Devices older than 4 years may need a hardware upgrade — raise via IT Service Desk

## When to Escalate
- Slowness began after a specific Windows update
- Task Manager shows `System` process at 100% disk for more than 30 minutes
- Computer is hot to the touch and the fan is always running at max
- Slowness is accompanied by blue screens or crash errors

## Related Articles
- windows-updates.md
- software-centre.md
- teams-issues.md
