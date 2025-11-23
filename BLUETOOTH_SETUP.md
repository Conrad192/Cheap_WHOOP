# Bluetooth Setup Guide - Mi Band Direct Connection

**The easiest and most automated way to sync your Mi Band!**

No internet, no cloud, no manual exports - just wear your watch and sync.

---

## ✨ Benefits

- ✅ **Fully Automated** - One-click sync when watch is nearby
- ✅ **No Internet Required** - Works completely offline
- ✅ **Private** - Data never leaves your computer
- ✅ **Fast** - Syncs in 20-30 seconds
- ✅ **Real-time** - Live heart rate monitoring

---

## 🚀 Quick Start

### 1. Install Bluetooth Library

The app will prompt you to install `bleak` if needed:

```bash
pip install bleak
```

### 2. Enable Bluetooth

Make sure Bluetooth is turned on:
- **Windows**: Settings → Bluetooth & devices → Turn on
- **Mac**: System Preferences → Bluetooth → Turn Bluetooth On
- **Linux**: `bluetoothctl power on`

### 3. Prepare Your Mi Band

**Important:** Your Mi Band must be:
- ✅ Charged (at least 20%)
- ✅ Within 10 feet / 3 meters of your computer
- ✅ **Not actively connected to your phone's Mi Fit/Zepp app**

**Tip:** Open Mi Fit/Zepp app and disconnect or close it first!

---

## 📱 How to Use

### First Time Setup:

1. **Run the app:**
   ```bash
   streamlit run app.py
   ```

2. **In Settings sidebar:**
   - Select **"Bluetooth (Auto-Sync)"**

3. **Click "🔍 Scan for Mi Band"**
   - Wait 10 seconds while it searches
   - Your Mi Band will appear in the list

4. **Click "Connect to [Your Mi Band]"**
   - It will pair and sync immediately
   - You're done! It's now paired.

### After First Pairing:

Just click **"Sync Now"** in Settings or **"Refresh Data"** on the dashboard!

Your Mi Band will connect automatically when nearby.

---

## 🔍 Troubleshooting

### "No devices found"

**Solution:**
1. Make sure Mi Band is **not connected** to your phone
2. Close Mi Fit/Zepp app completely
3. Move Mi Band closer to your computer
4. Try scanning again

### "Connection failed"

**Solution:**
1. Restart Bluetooth on your computer
2. Click "Forget Device" in app
3. Power off/on your Mi Band (hold button for 10 seconds)
4. Scan and pair again

### "Permission denied" (Linux)

**Solution:**
```bash
# Add your user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Reload groups
newgrp bluetooth
```

### Mi Band already paired to phone

**You need to:**
- **Either:** Unpair from phone temporarily (Settings → Bluetooth → Forget Mi Band)
- **Or:** Just close Mi Fit/Zepp app before syncing

After syncing to Cheap WHOOP, you can reconnect to your phone.

---

## 📊 What Data Gets Synced

When you sync via Bluetooth:

- ✅ **Heart Rate** - Real-time BPM (20-30 readings)
- ✅ **Steps** - Current day's step count
- ✅ **Battery Level** - Watch battery status
- ✅ **RR Intervals** - Calculated from heart rate

**Note:** Bluetooth provides *current* data, not historical sleep/activity logs. For full historical data, use Zepp API or Manual Upload methods.

---

## ⚙️ Advanced Options

### Customize Sync Duration

Edit `pull_bluetooth.py` and change the duration parameter:

```python
# Sync for 60 seconds instead of 20
await quick_sync(duration=60)
```

### Use CLI Directly

You can also use the Bluetooth module from command line:

```bash
python pull_bluetooth.py
```

This gives you an interactive CLI for scanning and syncing.

---

## 🔒 Privacy & Security

**Your data is completely private:**

- ✅ No internet connection needed
- ✅ Data stays on your computer
- ✅ Direct Bluetooth LE connection
- ✅ No third-party servers
- ✅ No cloud uploads

Device pairing info is stored locally in `data/bluetooth_devices.json`.

---

## 💡 Tips

1. **Best time to sync:** After a workout or in the morning
2. **Sync regularly:** Once or twice per day for best tracking
3. **Keep watch close:** Within 10 feet for reliable connection
4. **Battery:** Syncing uses minimal watch battery (~1%)

---

## 🆘 Still Having Issues?

1. Check Bluetooth is enabled and working
2. Try the **Zepp API** method as alternative (internet required)
3. Use **Manual Upload** method for guaranteed compatibility

See [DEVICE_INTEGRATION.md](DEVICE_INTEGRATION.md) for alternative methods.

---

## Supported Devices

✅ Mi Band 2, 3, 4, 5, 6, 7
✅ Amazfit Band 5, 7
✅ Mi Smart Band 4, 5, 6, 7, 8

Most Xiaomi/Amazfit devices with Bluetooth LE work!
