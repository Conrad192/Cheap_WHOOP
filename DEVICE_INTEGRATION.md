# Device Integration Guide

This guide explains how to connect your Xiaomi Mi Band or Amazfit watch to Cheap WHOOP.

## Available Integration Methods

### 1. Zepp/Mi Fit API (Automatic Sync) ⚡

**Best for:** Daily automatic syncing
**Supports:** All Xiaomi Mi Band and Amazfit watches

#### Setup Steps:

1. Open Cheap WHOOP app
2. Go to **Settings** in the sidebar
3. Select **"Zepp/Mi Fit API"** as your data source
4. Enter your Zepp/Mi Fit account credentials:
   - Email address
   - Password
5. Click **Login**
6. Once connected, click **"Refresh Data"** to sync your watch data

#### What Gets Synced:
- ✅ Heart rate (BPM)
- ✅ Sleep stages (light, deep, REM)
- ✅ Step count
- ✅ Blood oxygen (SpO2)
- ✅ Historical data

#### Troubleshooting:
- **Login failed**: Check your email and password
- **No data**: Make sure your watch has synced to the Zepp/Mi Fit app first
- **Old data**: Open Zepp app and sync your watch, then refresh in Cheap WHOOP

---

### 2. Manual File Upload (One-Time Import) 📁

**Best for:** Privacy-conscious users or one-time imports
**Supports:** CSV, JSON, XML exports from various apps

#### How to Export from Zepp/Mi Fit App:

**On Android:**
1. Open Zepp/Mi Fit app
2. Go to **Profile** → **Settings**
3. Tap **"Export Data"** or **"Download My Data"**
4. Select date range
5. Choose **CSV** or **JSON** format
6. Save file to your device

**On iPhone:**
1. Open Zepp/Mi Fit app
2. Go to **Profile** → **Settings**
3. Tap **"Export Health Data"**
4. Select export format (CSV recommended)
5. Share file via AirDrop, email, or save to Files

#### Import to Cheap WHOOP:

1. In Cheap WHOOP, go to **Settings**
2. Select **"Manual Upload"** as data source
3. Click **"Choose a file"**
4. Select your exported CSV/JSON file
5. Click **"Import File"**
6. Data will be processed and displayed

---

### 3. Mock Data (Demo Mode) 🎭

**Best for:** Testing and demos
**Generates:** Simulated realistic data

This is the default mode. It generates fake data to demonstrate the app's features without needing a real device.

---

## Supported Export Formats

### Zepp/Mi Fit Exports
- **CSV**: Heart rate, steps, sleep, SpO2
- **JSON**: All metrics with timestamps

### Apple Health
- **XML**: export.xml from Health app
- Includes heart rate, steps, oxygen saturation

### Google Fit
- **CSV**: Activity data, heart rate, steps

### Generic CSV
- Must include a timestamp column
- Recognized column names:
  - Heart rate: `bpm`, `heart_rate`, `heartrate`, `hr`
  - Steps: `steps`, `step_count`
  - SpO2: `spo2`, `oxygen`, `blood_oxygen`
  - Sleep: `sleep_stage`, `sleep`

---

## Privacy & Security

### Zepp API Method
- Credentials are stored locally in `data/zepp_credentials.json`
- Passwords are hashed before sending to Zepp servers
- No data is sent to third parties
- You can disconnect anytime in Settings

### Manual Upload Method
- Files are processed locally
- No cloud uploads
- Original files are deleted after import
- Complete privacy control

---

## Frequently Asked Questions

### Can I switch between data sources?
Yes! You can change your data source anytime in Settings. Previous data will be preserved.

### How often should I sync?
- **Zepp API**: Once per day (recommended after your watch syncs)
- **Manual Upload**: Whenever you export new data

### Will this drain my phone battery?
No. The app only syncs when you click "Refresh Data" - it doesn't run in the background.

### Is my watch data secure?
Yes. All data is stored locally on your device. The app never uploads your data to external servers (except Zepp's official API when using that method).

### My watch isn't listed. Can I still use this?
If your watch can export data as CSV, JSON, or syncs to Google Fit/Apple Health, you can use the Manual Upload feature.

### Does this work offline?
- **Zepp API**: Requires internet to sync
- **Manual Upload**: Works completely offline
- **Mock Data**: Works offline

---

## Getting Help

If you encounter issues:

1. Check that your watch has synced to its companion app first
2. Verify your credentials if using Zepp API
3. Try the Manual Upload method as an alternative
4. Check the exported file format matches the examples above

---

## Data Privacy Notice

Cheap WHOOP is a local-first application:
- All your health data stays on your device
- No telemetry or tracking
- No ads or data collection
- Open source and transparent

When using the Zepp API integration, you're connecting directly to Zepp's servers using your credentials. We never see or store your password.
