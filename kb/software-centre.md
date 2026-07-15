# Software Centre

## Overview
Software Centre is the self-service application store for corporate-approved software. All standard software should be installed from here without requiring IT assistance.

## Opening Software Centre

- **Windows 11/10:** Start → search **"Software Centre"** → open
- Or: `C:\Windows\CCM\SCClient.exe`

## Installing Software

1. Open Software Centre
2. Browse the **Applications** tab or use the search bar
3. Click the software you need → **Install**
4. Installation runs in the background — you can continue working
5. Some software requires a restart — you will be prompted

## Available Software Categories

| Category | Examples |
|----------|---------|
| Productivity | Microsoft Office, Adobe Reader, 7-Zip |
| Communication | Cisco AnyConnect VPN, Teams, Zoom |
| Browsers | Google Chrome, Mozilla Firefox |
| Developer Tools | Visual Studio Code, Git, Python |
| Security | CrowdStrike Falcon, Qualys Agent |
| Utilities | NotePad++, WinRAR, TreeSize |

## Requesting Software Not in the Catalogue

If you need software that isn't available:
1. Raise an **IT Service Desk** request: category **Software → New Software Request**
2. Include: software name, version, business justification, licence information
3. IT will assess security, licence compliance, and compatibility
4. Approved software is added to the catalogue within **5–10 business days**

## Troubleshooting

### Software Centre is not opening
1. Restart the **SMS Agent Host** service:
   ```
   services.msc → SMS Agent Host → Restart
   ```
2. If still not opening, contact IT — the SCCM/ConfigMgr agent may need reinstalling

### Software shows "Installation failed"
1. Check disk space (minimum 2GB free required)
2. Check you are not running on battery only (some installs require AC power)
3. Re-try the installation
4. If it fails again, note the error code and contact IT

### "You don't have permission to install this software"
Certain software requires IT approval first. Raise a service desk request.

### Software not appearing in Software Centre
Software is deployed to your machine based on your AD group membership. Contact IT to verify your group membership is correct.

## Updates

The **Updates** tab in Software Centre shows pending Windows and application updates:
- Updates install automatically outside business hours
- If an urgent update is flagged, click **Install All** — a restart may be required

## When to Escalate
- Multiple applications failing to install
- Software Centre completely missing from the device
- Licence activation errors for Adobe/Microsoft products

## Related Articles
- java-versions.md
- adobe-licensing.md
- chrome-edge-policy.md
