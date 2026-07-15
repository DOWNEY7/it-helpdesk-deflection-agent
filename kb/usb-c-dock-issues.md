# USB-C Dock Issues

## Overview
USB-C docking stations connect your laptop to monitors, keyboards, mice, ethernet, and USB peripherals with a single cable. This article covers the most common dock issues and fixes.

## Supported Docks
- **Dell WD19S** — compatible with Dell Latitude and Precision laptops
- **CalDigit TS4** — Mac and Windows compatible
- **Lenovo ThinkPad Thunderbolt 4** — for ThinkPad users only
- Contact IT to confirm compatibility with your specific laptop model

## Common Issues and Fixes

### No Display on External Monitor(s)

1. Ensure the dock power adapter is plugged in (most docks need separate power)
2. Unplug and re-plug the USB-C cable from both the laptop and dock
3. Check the monitor cable (DisplayPort/HDMI) is firmly seated
4. Press **Win + P** → select **Extend** or **Duplicate**
5. Try a different USB-C port on the laptop (some ports are data-only, not Thunderbolt)

If still no display:
```
Device Manager → Display adapters → right-click → Update driver → Search automatically
```

### Ethernet Not Working Through Dock

1. Ensure dock driver is installed — check Software Centre for your dock model
2. Device Manager → Network adapters → look for the dock's ethernet adapter
3. If showing a yellow warning: right-click → **Update driver**
4. Try the laptop's built-in ethernet port to confirm the issue is the dock

### USB Peripherals Not Recognised

1. Unplug the USB-C cable → wait 10 seconds → re-plug
2. Try a different USB port on the dock
3. If a specific device isn't recognised: test the device directly on the laptop USB port
4. Some high-power devices need a powered USB hub

### Laptop Not Charging Through Dock

- Verify the dock power adapter is connected (check the LED on the dock)
- USB-C charging requires a dock with **Power Delivery (PD)**
- Minimum 65W required for most laptops; 90W+ for high-performance models
- Try the original laptop charger to confirm the laptop charges normally

### Dock Works on First Plug but Disconnects Randomly

- This is usually a USB-C cable fault — replace the cable
- Check for Windows Update — dock firmware updates are pushed via Windows Update
- Reduce USB bandwidth: disconnect unused high-bandwidth devices (external SSDs, webcams at 4K)

## Installing Dock Drivers

Drivers are available in Software Centre:
1. Open **Software Centre** → search your dock model name
2. Install the **Dock Firmware Update** package
3. Keep the dock connected during firmware update — do not unplug
4. Restart the laptop after firmware completes

## When to Escalate
- Dock is physically damaged
- None of the USB ports work on the dock
- Thunderbolt 4 features not working (requires Thunderbolt-certified cable)
- Multiple docks in the same office failing simultaneously (network switch/power issue)

## Related Articles
- monitor-setup.md
- software-centre.md
- laptop-build.md
