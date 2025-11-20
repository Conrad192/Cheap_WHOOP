# 💪 Cheap WHOOP Pro

A comprehensive fitness tracking application that rivals premium services like WHOOP, but without the $30/month subscription. Built with affordable hardware ($75) and Python + Streamlit.

## 🌟 Features Overview

### Core Metrics
- **HRV (Heart Rate Variability)** - RMSSD method for accurate recovery assessment
- **Resting Heart Rate** - Tracks your cardiovascular fitness
- **Strain Score (0-21)** - WHOOP-style cardiovascular load measurement
- **Recovery Score (0-100%)** - Overnight recovery assessment
- **Training Readiness** - Should you train hard today?
- **Stress Level (0-10)** - Nervous system tension monitoring

### 🆕 New Advanced Features (v2.0)

#### Sleep Analysis
- **Sleep Performance Score** - Comprehensive 0-100 score based on duration, deep/REM quality, efficiency, HRV, and SpO2
- **Sleep Stage Breakdown** - Deep, REM, and Light sleep tracking with pie charts
- **Sleep Debt Tracking** - Cumulative sleep deficit over 7 days
- **Sleep Consistency Score** - Sleep schedule regularity assessment
- **Optimal Bedtime Recommendations** - Based on your best recovery days

#### Training & Performance
- **Strain Goal** - Dynamic daily goal based on your recovery score
- **Strain Coach** - Real-time coaching advice to hit your daily goals
- **Recovery Prediction** - Predicts tomorrow's recovery based on trends
- **Overtraining Alert** - Multi-factor burnout risk detection
- **Rest Day Recommendations** - Explicit guidance on when to rest
- **Training Load** - 7-day cumulative strain tracking
- **VO2 Max Estimation** - Cardio fitness estimation from HR data

#### Heart Rate Analysis
- **SpO2 Trends** - Blood oxygen tracking with automatic alerts
- **Heart Rate Zones** - Time spent in 5 training zones
- **Hourly Strain Breakdown** - Visual breakdown of strain by hour
- **Respiratory Rate Estimation** - Breathing rate from HRV patterns

#### Workout Tracking
- **Workout Auto-Detection** - Automatically detects workout periods
- **Activity Type Logging** - Tag workouts (Run, Bike, Lift, Swim, etc.)
- **Activity Log** - Complete history and distribution charts

#### Trends & Analytics
- **Weekly Strain vs Recovery Chart** - Visual comparison
- **Monthly Trends Comparison** - 30-day vs previous 30-day
- **RHR & HRV Trend Analysis** - Track fitness improvements
- **Sunday Report Card** - Weekly summary
- **Individual Metric Deep Dives** - Detailed statistics

#### Gamification & Motivation
- **Achievement Badges** - Week Warrior, Monthly Master, Century Club, Super Recovery, HRV Hero, Step Master
- **Personal Records** - Track best recovery, highest HRV, lowest RHR, max strain, max steps

#### Lifestyle Tracking
- **Daily Journal** - Log training notes and observations
- **Cycle Tracking** - Menstrual cycle correlation with training
- **Hydration Reminders** - Automatic alerts based on strain
- **Body Metrics** - BMI, BMR, TDEE, weight tracking

#### User Experience
- **Dark Mode** - Toggle between light and dark themes
- **CSV Data Export** - Download all your data
- **8 Comprehensive Tabs** - Dashboard, Heart & Training, Sleep, Workouts, Trends, Achievements, Journal, Body Metrics
- **Interactive Charts** - Plotly-powered visualizations

## 📊 Dashboard Tabs

1. **🏠 Dashboard** - Overview with key metrics, strain goal, coaching, alerts
2. **❤️ Heart & Training** - Detailed heart metrics, SpO2, HR zones, live charts
3. **😴 Sleep Analysis** - Sleep score, stage breakdown, SpO2 during sleep
4. **🏋️ Workouts** - Auto-detected workouts, activity logging
5. **📈 Trends & Analytics** - Long-term trends, comparisons, insights
6. **🏆 Achievements & Records** - Badges and personal bests
7. **📝 Journal** - Daily notes and cycle tracking
8. **⚖️ Body Metrics** - BMI, BMR, TDEE, weight trends

## 🚀 Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Cheap_WHOOP.git
cd Cheap_WHOOP

# Install dependencies
pip install streamlit plotly pandas numpy

# Run application
streamlit run app.py
```

### First Time Setup
1. Navigate to **Body Metrics** tab
2. Enter your physical stats (age, weight, height, sex)
3. Set activity level
4. Click "Calculate & Save"

### Daily Usage
1. Click **"Refresh Data"** each morning
2. Review recovery score and recommendations
3. Check strain goal and coaching
4. Log journal notes
5. Tag workouts

## 🎯 Metric Interpretations

### Recovery Score
- 🟢 **67-100**: Ready for hard training
- 🟡 **34-66**: Light workout recommended
- 🔴 **0-33**: Rest day advised

### Strain Score
- **0-7**: Light day
- **7-14**: Moderate activity
- **14-21**: Hard training

### Training Readiness
- 💪 **70-100**: GO HARD
- 😐 **40-69**: Light workout
- 😴 **0-39**: REST DAY

### Sleep Performance Score
- 🌟 **80-100**: Excellent
- 👍 **65-79**: Good
- 😐 **50-64**: Fair
- 😴 **<50**: Poor

## 💡 Pro Tips

1. Track daily for best insights
2. Trust your recovery score
3. Focus on long-term trends
4. Use adaptive strain goals
5. Log workouts for insights
6. Journal regularly
7. Check SpO2 trends
8. Heed overtraining warnings
9. Export data regularly
10. Review weekly summaries

## 🔧 Technical Details

### Architecture
```
Raw Data → Calibration → Merging → Metrics → Streamlit UI
```

### Key Files
- **app.py** - Main UI (1400+ lines, 8 tabs)
- **metrics.py** - Calculations (800+ lines, 25+ functions)
- **merge.py** - Data pipeline
- **calibration.py** - HR calibration

### Data Storage
- `data/merged/daily_merged.csv` - Current data
- `data/history.csv` - Historical summaries
- `data/user_profile.json` - User stats
- `data/journal.json` - Daily notes
- `data/activity_log.json` - Workout tags

## 🐛 Troubleshooting

**No Data?**
- Click "Refresh Data"
- Check `data/merged/daily_merged.csv` exists

**Metrics Wrong?**
- Fill out user profile
- Track for 7+ days
- Review raw data

**App Won't Start?**
```bash
pip install --upgrade streamlit plotly pandas numpy
streamlit run app.py --logger.level=debug
```

## 📈 Roadmap

### Completed ✅
- Sleep Performance Score
- SpO2 Trends
- Workout Auto-Detection
- Heart Rate Zones
- Training Load
- Recovery Prediction
- Overtraining Alerts
- Achievement Badges
- Personal Records
- Activity Logging
- Journal System
- Cycle Tracking
- Dark Mode
- CSV Export

### Planned 🔜
- PDF Export (Monthly Reports)
- Sleep Consistency Visualization
- Optimal Bedtime Calculator
- Mobile App (Flutter)
- Real Device Integration
- Multi-user Support
- Cloud Sync

## 📄 License

MIT License

## 🙏 Acknowledgments

- Inspired by WHOOP
- Built with Streamlit
- Charts by Plotly
- Data science with pandas & numpy

---

**Built with ❤️ to make fitness tracking accessible to everyone, without expensive subscriptions.**

*Version 2.0 - Now with 29+ advanced features!*