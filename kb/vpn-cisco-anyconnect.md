# VPN — Cisco AnyConnect

## Overview
The corporate VPN uses **Cisco AnyConnect Secure Mobility Client**. All remote workers must connect to the VPN before accessing internal resources.

## First-Time Installation

1. Open **Software Centre** (Start → search "Software Centre")
2. Search for **Cisco AnyConnect**
3. Click **Install** — takes approximately 3 minutes
4. Restart the machine if prompted

Alternatively, download directly from the IT portal: **https://itportal.company.internal/vpn**

## Connecting to the VPN

1. Open **Cisco AnyConnect** from the system tray or Start menu
2. In the server field, enter: `vpn.company.com`
3. Click **Connect**
4. Enter your **Windows username** (no @company.com suffix)
5. Enter your **Windows password**
6. Complete **MFA** when prompted (Authenticator notification or SMS code)
7. Status changes to **"Connected"** — you now have full network access

## Disconnecting

Click the AnyConnect icon in the system tray → **Disconnect**

Always disconnect when leaving the VPN, especially on public networks.

## Common Connection Errors

| Error Message | Cause | Fix |
|--------------|-------|-----|
| "Unable to contact the VPN server" | No internet connection | Check internet first, then retry |
| "Certificate validation failure" | Expired or missing certificate | Run certificate update — see below |
| "Authentication failed" | Wrong password or account locked | Check password, check account lockout |
| "AnyConnect was not able to establish a connection" | Firewall/port blocked | Check ports 443 and 10443 are open |
| "VPN connection disconnected unexpectedly" | Network instability | Switch network (3G/4G instead of public WiFi) |
| "Login denied: Maximum sessions reached" | Too many active sessions | Disconnect from other devices first |

## Certificate Update

If you see certificate errors:

1. Close AnyConnect completely
2. Run as administrator: `C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpnui.exe`
3. Disconnect then reconnect — certificate should refresh automatically
4. If not, contact IT for the certificate package

## Split Tunnelling

The VPN uses **full-tunnel mode** — all traffic routes through the corporate network. If you need split tunnel access for a specific use case, your manager must raise a request. See: split-tunneling.md

## When to Escalate
- AnyConnect is not available in Software Centre
- Error persists after password reset and reinstall
- VPN connects but no internal resources are accessible (routing issue)
- User is travelling abroad — some countries block VPN protocols

## Related Articles
- vpn-globalprotect.md
- split-tunneling.md
- wifi-certificate.md
- account-lockout.md
