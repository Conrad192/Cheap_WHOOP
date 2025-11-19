# 💪 Cheap WHOOP - Advanced Health & Fitness Tracker

A comprehensive, low-cost alternative to WHOOP using affordable hardware (Xiaomi Mi Band + Coospo HR Monitor). Track your heart rate, HRV, sleep, blood sugar, and get personalized training recommendations - all without the $30/month subscription!

## 🌟 Features

### ❤️ Heart Rate Monitoring
- **Real-time heart rate tracking** from Xiaomi Mi Band and Coospo devices
- **Personalized max heart rate calculation** based on age and weight (Inbar formula)
- **5 Training zones** (Recovery, Fat Burn, Aerobic, Threshold, Max Effort)
- **HRV (Heart Rate Variability)** analysis for recovery assessment
- **Resting heart rate** tracking and trends

### 😴 Sleep Analysis
- Automatic sleep stage detection (Deep, REM, Light sleep)
- Sleep duration and efficiency tracking
- Sleep quality metrics for recovery calculation

### 🧠 Advanced Metrics
- **Recovery Score** (0-100%) - overnight recovery assessment
- **Strain Score** (0-21) - daily cardiovascular load
- **Training Readiness** - personalized workout recommendations
- **Stress Level** (0-10) - nervous system tension monitoring
- **Respiratory Rate** estimation from HRV patterns

### 🩸 Blood Sugar Tracking (NEW!)
- **Pre/Post-meal glucose monitoring**
- **Insulin sensitivity assessment** with 0-100 score
- **Glucose spike analysis** for meal optimization
- **Risk evaluation** (diabetes, prediabetes screening)
- **Personalized recommendations** for improving metabolic health
- **Historical tracking** with trend visualization

### ⚖️ Body Metrics & Metabolism
- **BMI calculator** with visual gauge and categories
- **BMR (Basal Metabolic Rate)** using Mifflin-St Jeor equation
- **TDEE (Total Daily Energy Expenditure)** with activity adjustment
- **Calorie goals** for weight loss, maintenance, or gain
- **Weight tracking** over time
- Support for both metric and imperial units

### 📈 Historical Trends
- Track all metrics over time (7, 30, 90 days, or all time)
- Visualize trends with interactive charts
- Compare against personal baselines
- Export data for further analysis

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Cheap_WHOOP.git
   cd Cheap_WHOOP
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

### First-Time Setup

1. **Complete your profile** in the "BMI & Metabolism" tab:
   - Enter age, weight, height, sex
   - Choose activity level (steps or exercise minutes)
   - Save profile to enable personalized calculations

2. **Generate initial data** by clicking "Refresh Data" in the "Heart Data" tab

3. **Start tracking!** The app will collect and analyze your metrics

## 📊 How to Use

### Heart Rate Tracking
- View real-time heart rate data in the "Heart Data" tab
- Check your personalized training zones based on your profile
- Monitor recovery and strain to optimize training

### Blood Sugar Monitoring
1. Measure fasting glucose (before eating)
2. Eat your meal
3. Wait 1-2 hours
4. Measure post-meal glucose
5. Enter both values in the "Blood Sugar" tab
6. Get instant insulin sensitivity assessment

**Healthy Ranges:**
- Fasting: 70-99 mg/dL (normal)
- Post-meal (1-2h): < 140 mg/dL (normal)
- Glucose spike: < 30-40 mg/dL (excellent control)

### Training Recommendations
Based on your recovery score:
- 🟢 **67-100%**: Ready for hard training
- 🟡 **34-66%**: Moderate recovery, light workout recommended
- 🔴 **0-33%**: Poor recovery, prioritize rest

## 📁 Project Structure

```
Cheap_WHOOP/
├── app.py                          # Main Streamlit application
├── metrics.py                      # Core fitness metrics calculations
├── utils/
│   ├── health_calculations.py      # Max HR, BMI, BMR, TDEE calculations
│   └── blood_sugar.py              # Blood glucose and insulin sensitivity
├── pull_xiaomi.py                  # Xiaomi Mi Band data generation
├── pull_coospo.py                  # Coospo HR monitor data generation
├── merge.py                        # Merge data from multiple sources
├── calibration.py                  # Device calibration utilities
├── data/                           # Data storage directory
│   ├── merged/                     # Merged heart rate data
│   ├── history.csv                 # Historical metrics
│   ├── glucose_history.csv         # Blood sugar tracking
│   └── user_profile.json           # User profile data
└── requirements.txt                # Python dependencies
```

## 🔬 Technical Details

### Max Heart Rate Calculation
Uses the **Inbar formula** for personalized max HR:
```
Max HR = 205.8 - (0.685 × age) + (0.05 × weight_kg)
```
More accurate than the classic "220 - age" formula, especially when accounting for body composition.

### Insulin Sensitivity Score
Calculated from:
- **40%** Fasting glucose (ideal < 90 mg/dL)
- **30%** Post-meal glucose (ideal < 120 mg/dL)
- **30%** Glucose spike (ideal < 30 mg/dL)

Score interpretation:
- 80-100: Excellent sensitivity
- 60-79: Good sensitivity
- 40-59: Reduced sensitivity (warning)
- 0-39: Poor sensitivity (consult doctor)

### Recovery Score
Based on:
- HRV (Heart Rate Variability)
- Resting heart rate
- Sleep quality

### Strain Score
Combines:
- Heart rate elevation above resting
- Step count (10,000 steps ≈ 3 strain points)

## 💡 Tips for Best Results

### General
- Wear your device 24/7 for accurate data
- Update your profile when your weight changes
- Track consistently for at least 7 days to establish baselines

### Blood Sugar Tracking
- Test at consistent times for comparable results
- Track what you eat to identify problem foods
- Aim for minimal glucose spikes (< 30 mg/dL)
- Test different meals to optimize your diet

### Training
- Respect your recovery score - rest when needed
- Use training zones to optimize workout intensity
- Monitor HRV trends for overtraining detection

## 🛠️ Hardware Requirements

### Minimum Setup ($75)
- **Xiaomi Mi Band 6/7** (~$30) - Sleep, steps, basic HR
- **Coospo H6/H7 HR Monitor** (~$45) - Accurate workout HR

### Optional Upgrades
- **Continuous Glucose Monitor** (e.g., Freestyle Libre) - Automated blood sugar tracking
- **Smart scale** - Automated weight tracking

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Machine learning for better predictions
- Integration with more devices
- Advanced analytics and insights
- Mobile app companion

## 📝 License

MIT License - feel free to use and modify!

## ⚠️ Disclaimer

This app is for **educational and fitness tracking purposes only**. It is NOT a medical device and should NOT be used for medical diagnosis or treatment. Always consult healthcare professionals for medical advice, especially regarding diabetes, heart conditions, or other health concerns.

## 🙏 Acknowledgments

Inspired by WHOOP's comprehensive health tracking approach, made accessible and customizable for everyone.

---

**Made with ❤️ for the fitness and health tracking community**