# Quick Start - Connect Your Xiaomi Mi Band / Amazfit

You can now pull **real data** from your Xiaomi Mi Band or Amazfit watch!

## Option 1: Bluetooth (Direct Sync) 📡 - **RECOMMENDED**

**The most automated and private method!**

No internet, no passwords - just have your watch nearby.

### Steps:

1. **Start the app:**
   ```bash
   streamlit run app.py
   ```

2. **In Settings sidebar:**
   - Select **"Bluetooth (Auto-Sync)"**
   - Click **"🔍 Scan for Mi Band"**
   - Click your device when it appears
   - Done! It syncs automatically now.

3. **Daily use:**
   - Just click **"Sync Now"** or **"Refresh Data"**
   - Your watch connects automatically when nearby

### Requirements:
- Bluetooth enabled on your computer
- Mi Band within 10 feet
- Mi Fit/Zepp app closed (not connected to phone)

**📖 Full guide:** See [BLUETOOTH_SETUP.md](BLUETOOTH_SETUP.md)

---

## Option 2: Zepp API (Cloud Sync) ⚡

Login once and sync from anywhere with internet.

### Steps:

1. **Start the app:**
   ```bash
   streamlit run app.py
   ```

2. **In the Settings sidebar:**
   - Select **"Zepp/Mi Fit API"**
   - Enter your Zepp/Mi Fit email and password
   - Click **Login**

3. **Sync your data:**
   - Click **"Refresh Data"** in the dashboard
   - Your real watch data will appear!

### Important:
- Make sure your watch has synced to the Zepp/Mi Fit app first
- Data pulls directly from Zepp's cloud (same data you see in the app)
- Your credentials are stored locally - we never see them

---

## Option 3: Manual Upload (Privacy-First) 📁

If you prefer not to enter credentials, you can export and upload files.

### Steps:

1. **Export from Zepp/Mi Fit app:**
   - Open Zepp/Mi Fit app on your phone
   - Go to **Profile → Settings → Export Data**
   - Select CSV or JSON format
   - Save the file

2. **Upload to Cheap WHOOP:**
   - In Settings, select **"Manual Upload"**
   - Click **"Choose a file"**
   - Select your exported file
   - Click **"Import File"**

---

## What Data Gets Pulled?

✅ **Heart Rate** - Continuous BPM tracking
✅ **Sleep Stages** - Light, deep, REM sleep
✅ **Steps** - Daily step count
✅ **SpO2** - Blood oxygen levels
✅ **RR Intervals** - Heart rate variability

All the same metrics you see in the Zepp/Mi Fit app!

---

## Troubleshooting

### "Login failed"
- Double-check your email and password
- Make sure you're using your Zepp/Mi Fit account (not Xiaomi account)
- Try logging into the Zepp app first to verify credentials

### "No data available"
- Open the Zepp/Mi Fit app and sync your watch
- Wait for sync to complete (green checkmark)
- Then click "Refresh Data" in Cheap WHOOP

### "API error"
- The Zepp API is unofficial and may have rate limits
- Try again in a few minutes
- Use Manual Upload as a backup method

---

## Which Method Should I Use?

| Feature | Bluetooth | Zepp API | Manual Upload |
|---------|-----------|----------|---------------|
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Privacy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Automation | Yes | Yes | No |
| Offline | Yes | No | Yes |
| Setup time | 20 seconds | 30 seconds | 2-3 minutes |
| Historical data | No | Yes | Yes |

**Recommendation:** Use **Bluetooth** for daily syncing (easiest!). Use **Zepp API** or **Manual Upload** for initial setup to get historical data.

---

## Next Steps

Once your data is loaded:

1. **Check Dashboard** - See your recovery score and strain
2. **View Sleep Analysis** - Deep dive into sleep quality
3. **Track Workouts** - Auto-detected exercise sessions
4. **Monitor Trends** - Long-term progress tracking

Need more help? See [DEVICE_INTEGRATION.md](DEVICE_INTEGRATION.md) for detailed guides.
