# Quick Start - Connect Your Xiaomi Mi Band / Amazfit

You can now pull **real data** from your Xiaomi Mi Band or Amazfit watch!

## Option 1: Zepp API (Automatic) ⚡ - **RECOMMENDED**

This is the easiest method - just login once and sync anytime.

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

## Option 2: Manual Upload (Privacy-First) 📁

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

| Feature | Zepp API | Manual Upload |
|---------|----------|---------------|
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Privacy | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Automation | Yes | No |
| Offline | No | Yes |
| Setup time | 30 seconds | 2-3 minutes |

**Recommendation:** Start with Zepp API for convenience. Switch to Manual Upload if you have privacy concerns.

---

## Next Steps

Once your data is loaded:

1. **Check Dashboard** - See your recovery score and strain
2. **View Sleep Analysis** - Deep dive into sleep quality
3. **Track Workouts** - Auto-detected exercise sessions
4. **Monitor Trends** - Long-term progress tracking

Need more help? See [DEVICE_INTEGRATION.md](DEVICE_INTEGRATION.md) for detailed guides.
