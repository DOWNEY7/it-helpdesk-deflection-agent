# OneDrive Sync Issues

## Overview
OneDrive for Business syncs your files between your device and the cloud. This article covers how to fix sync errors, stuck files, and OneDrive setup.

## Checking Sync Status

Click the **OneDrive cloud icon** in the system tray:
- **Blue spinning arrows** — syncing in progress
- **Green tick** — all files synced
- **Red X** — sync error (click for details)
- **Pause icon** — sync paused manually

## Fixing Common Sync Errors

### "Processing changes" stuck for over 10 minutes
1. Right-click OneDrive icon → **Pause syncing** → **Resume syncing**
2. If still stuck, reset OneDrive:
   - Press **Win + R**, paste: `%localappdata%\Microsoft\OneDrive\onedrive.exe /reset`
   - Wait 2 minutes, then start OneDrive from Start menu

### "Files on demand" — files show as cloud icons
Files are stored in the cloud only. To download locally:
- Right-click the file → **Always keep on this device**
- Or: OneDrive Settings → tick **"Make all files available offline"** (uses more disk space)

### "There isn't enough space on your PC"
OneDrive cannot sync because the disk is nearly full:
1. Open **Storage Sense** (Settings → System → Storage)
2. Review large files in Documents and Downloads
3. Move old files to SharePoint team libraries

### "Sorry, OneDrive can't add your folder right now"
1. Sign out of OneDrive (right-click icon → Settings → Account → **Unlink this PC**)
2. Sign back in with your work email

### File name or path errors
OneDrive does not sync files with:
- Names containing: `" * : < > ? / \ |`
- Names starting or ending with a space or period
- Paths longer than 400 characters
- Files named `desktop.ini`, `thumbs.db`, or starting with `~`

Rename or move affected files.

## Known File Types Not Synced
- `.tmp` files
- Files in Recycle Bin
- OneNote notebooks (synced separately by OneNote app)

## Reinstalling OneDrive

Only if all above steps fail:
1. Win + R → `winget uninstall Microsoft.OneDrive`
2. Restart
3. Win + R → `winget install Microsoft.OneDrive`
4. Sign in with work account

## When to Escalate
- OneDrive storage quota exceeded (1TB for E3, 2GB for F3)
- Sync error mentioning "SharePoint site has been deleted"
- Files deleted from OneDrive and not in Recycle Bin (possible data loss)

## Related Articles
- m365-licensing.md
- sharepoint-access.md
