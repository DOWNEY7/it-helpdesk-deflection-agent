# Printer Mapping

## Overview
Network printers can be mapped using the automated print script or manually. This article covers both methods.

## Method 1: Print Script (Recommended)

Run the corporate print mapping script — this maps all printers for your office location automatically:

1. Press **Win + R**, type `\\printserver\scripts` and press **Enter**
2. Double-click **MapPrinters.bat**
3. A command window will briefly open and close — this is normal
4. Your printers will now appear in **Settings → Bluetooth & devices → Printers & scanners**

If the script fails with "Access denied", run it as administrator: right-click → **Run as administrator**

## Method 2: Manual Mapping

### Add by printer name (recommended):
1. Press **Win + R**, type `\\printserver` and press **Enter**
2. Browse the list of printers — printers are named by location (e.g., `\\printserver\Floor2-HP-LaserJet`)
3. Double-click the printer you want → Windows installs the driver automatically
4. Optionally, right-click → **Set as default printer**

### Add by IP address (if name resolution fails):
1. Settings → Bluetooth & devices → **Printers & scanners** → **Add device**
2. Click **Add manually** → **Add a printer using an IP address or hostname**
3. Enter the printer's IP address (ask IT for the IP list)
4. Click **Next** and follow the wizard

## Setting a Default Printer

1. Settings → Bluetooth & devices → **Printers & scanners**
2. Untick **"Let Windows manage my default printer"**
3. Click your preferred printer → **Set as default**

## Common Issues

| Issue | Fix |
|-------|-----|
| Printer shows as offline | Right-click → See what's printing → Printer menu → **Use Printer Online** |
| "Driver not available" error | Run script as administrator; if persists, contact IT for driver package |
| Document stuck in print queue | Open print queue → Cancel all documents → restart Print Spooler service |
| Can't see the print server | Ensure you are connected to VPN or on-site network |
| Wrong paper size printed | Check printer properties → **Printing Preferences** → Paper/Quality tab |

## Restarting the Print Spooler (clears stuck jobs)

```powershell
Stop-Service -Name Spooler -Force
Start-Service -Name Spooler
```

## When to Escalate
- Printer not listed on the print server at all
- Driver installation fails with error codes
- Printing to a remote office printer across WAN link
- Printer is new and needs to be added to the print server

## Related Articles
- printer-driver-install.md
- scan-to-email.md
