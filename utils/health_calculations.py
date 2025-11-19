"""
============================================================================
HEALTH_CALCULATIONS.PY - Advanced health metrics and calculations
============================================================================
Contains functions for:
- Max heart rate calculations (personalized with age/weight)
- BMI and body composition
- Metabolic calculations (BMR, TDEE)
- Unit conversions
============================================================================
"""


# ============================================================================
# MAX HEART RATE CALCULATIONS
# ============================================================================

def calculate_max_heart_rate(age, weight_kg=None, method="tanaka"):
    """
    Calculate maximum heart rate using various formulas.
    More customized than the simple "220 - age" formula.

    Parameters:
    -----------
    age : int
        Age in years
    weight_kg : float, optional
        Weight in kilograms (used for advanced methods)
    method : str
        Calculation method:
        - "tanaka": More accurate than 220-age (default)
        - "inbar": Accounts for weight (requires weight_kg)
        - "gulati": Optimized for women
        - "simple": Classic 220-age formula

    Returns:
    --------
    int : Maximum heart rate in BPM

    Examples:
    ---------
    >>> calculate_max_heart_rate(30)
    191  # Tanaka formula
    >>> calculate_max_heart_rate(30, weight_kg=70, method="inbar")
    189  # Weight-adjusted
    """

    if method == "simple":
        # Classic formula (least accurate)
        # Max HR = 220 - age
        return int(220 - age)

    elif method == "tanaka":
        # Tanaka formula (more accurate for all ages)
        # Max HR = 208 - (0.7 × age)
        # More accurate than 220-age, especially for older adults
        return int(208 - (0.7 * age))

    elif method == "gulati":
        # Gulati formula (optimized for women)
        # Max HR = 206 - (0.88 × age)
        return int(206 - (0.88 * age))

    elif method == "inbar":
        # Inbar formula (accounts for weight)
        # Max HR = 205.8 - (0.685 × age) + (0.05 × weight_kg)
        # Provides personalized estimate based on body composition
        if weight_kg is None:
            # Fall back to Tanaka if weight not provided
            return int(208 - (0.7 * age))
        return int(205.8 - (0.685 * age) + (0.05 * weight_kg))

    else:
        # Default to Tanaka
        return int(208 - (0.7 * age))


def calculate_heart_rate_zones(max_hr):
    """
    Calculate training heart rate zones based on max HR.

    Parameters:
    -----------
    max_hr : int
        Maximum heart rate in BPM

    Returns:
    --------
    dict : Heart rate zones with descriptions

    Zones:
    ------
    - Zone 1 (50-60%): Recovery, warm-up
    - Zone 2 (60-70%): Fat burn, endurance base
    - Zone 3 (70-80%): Aerobic fitness
    - Zone 4 (80-90%): Anaerobic threshold
    - Zone 5 (90-100%): Max effort, VO2 max
    """

    return {
        "zone_1": {
            "name": "Recovery / Warm-up",
            "range": (int(max_hr * 0.50), int(max_hr * 0.60)),
            "description": "Very light, conversational pace",
            "benefit": "Active recovery, warm-up"
        },
        "zone_2": {
            "name": "Fat Burn / Endurance",
            "range": (int(max_hr * 0.60), int(max_hr * 0.70)),
            "description": "Can maintain conversation",
            "benefit": "Build aerobic base, burn fat"
        },
        "zone_3": {
            "name": "Aerobic / Tempo",
            "range": (int(max_hr * 0.70), int(max_hr * 0.80)),
            "description": "Somewhat hard, short sentences",
            "benefit": "Improve cardiovascular efficiency"
        },
        "zone_4": {
            "name": "Threshold",
            "range": (int(max_hr * 0.80), int(max_hr * 0.90)),
            "description": "Hard, can only speak few words",
            "benefit": "Increase lactate threshold, speed"
        },
        "zone_5": {
            "name": "Max Effort",
            "range": (int(max_hr * 0.90), max_hr),
            "description": "Maximum effort, can't talk",
            "benefit": "Increase VO2 max, peak power"
        }
    }


def get_current_zone(current_hr, max_hr):
    """
    Determine which heart rate zone you're currently in.

    Parameters:
    -----------
    current_hr : int
        Current heart rate in BPM
    max_hr : int
        Maximum heart rate in BPM

    Returns:
    --------
    tuple : (zone_number, zone_dict)
        Zone number (1-5) and zone information
    """
    zones = calculate_heart_rate_zones(max_hr)

    for i, (zone_key, zone_info) in enumerate(zones.items(), 1):
        min_hr, max_zone_hr = zone_info["range"]
        if min_hr <= current_hr <= max_zone_hr:
            return (i, zone_info)

    # If below zone 1 or above zone 5
    if current_hr < zones["zone_1"]["range"][0]:
        return (0, {"name": "Below Zone 1", "description": "Resting"})
    else:
        return (6, {"name": "Above Max HR", "description": "Exceeding max!"})


# ============================================================================
# UNIT CONVERSIONS
# ============================================================================

def cm_to_inches(cm):
    """Convert centimeters to inches"""
    return cm / 2.54


def inches_to_cm(inches):
    """Convert inches to centimeters"""
    return inches * 2.54


def kg_to_lbs(kg):
    """Convert kilograms to pounds"""
    return kg * 2.20462


def lbs_to_kg(lbs):
    """Convert pounds to kilograms"""
    return lbs / 2.20462


def mg_dl_to_mmol_l(mg_dl):
    """
    Convert blood glucose from mg/dL (US) to mmol/L (international)

    Parameters:
    -----------
    mg_dl : float
        Blood glucose in mg/dL

    Returns:
    --------
    float : Blood glucose in mmol/L
    """
    return mg_dl / 18.0


def mmol_l_to_mg_dl(mmol_l):
    """
    Convert blood glucose from mmol/L (international) to mg/dL (US)

    Parameters:
    -----------
    mmol_l : float
        Blood glucose in mmol/L

    Returns:
    --------
    float : Blood glucose in mg/dL
    """
    return mmol_l * 18.0


# ============================================================================
# BMI AND BODY COMPOSITION
# ============================================================================

def calculate_bmi(weight_kg, height_cm):
    """
    Calculate Body Mass Index

    Parameters:
    -----------
    weight_kg : float
        Weight in kilograms
    height_cm : float
        Height in centimeters

    Returns:
    --------
    float : BMI value
    """
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def get_bmi_category(bmi):
    """
    Return BMI category and color for visualization

    Parameters:
    -----------
    bmi : float
        BMI value

    Returns:
    --------
    tuple : (category_name, color)
    """
    if bmi < 18.5:
        return "Underweight", "blue"
    elif bmi < 25:
        return "Normal weight", "green"
    elif bmi < 30:
        return "Overweight", "orange"
    else:
        return "Obese", "red"


# ============================================================================
# METABOLIC CALCULATIONS
# ============================================================================

def calculate_bmr(weight_kg, height_cm, age, sex):
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation.

    This is the most accurate modern formula for BMR.
    Returns calories burned per day at complete rest.

    Parameters:
    -----------
    weight_kg : float
        Weight in kilograms
    height_cm : float
        Height in centimeters
    age : int
        Age in years
    sex : str
        "Male" or "Female"

    Returns:
    --------
    float : BMR in calories/day
    """
    if sex.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return bmr


def calculate_tdee(bmr, activity_minutes_per_week=None, avg_steps_per_day=None):
    """
    Calculate Total Daily Energy Expenditure.
    Uses either activity minutes OR step count for activity multiplier.

    Parameters:
    -----------
    bmr : float
        Basal Metabolic Rate
    activity_minutes_per_week : int, optional
        Weekly exercise minutes
    avg_steps_per_day : int, optional
        Average daily steps

    Returns:
    --------
    float : TDEE in calories/day

    Activity Factors:
    ----------------
    - 1.2: Sedentary (little or no exercise)
    - 1.375: Lightly active (light exercise 1-3 days/week)
    - 1.55: Moderately active (moderate exercise 3-5 days/week)
    - 1.725: Very active (hard exercise 6-7 days/week)
    - 1.9: Extremely active (hard exercise & physical job)
    """
    # Prefer steps if both are provided (more accurate)
    if avg_steps_per_day:
        if avg_steps_per_day < 3000:
            activity_factor = 1.2  # Sedentary
        elif avg_steps_per_day < 5000:
            activity_factor = 1.375  # Lightly active
        elif avg_steps_per_day < 7500:
            activity_factor = 1.55  # Moderately active
        elif avg_steps_per_day < 10000:
            activity_factor = 1.725  # Very active
        else:
            activity_factor = 1.9  # Extremely active
    elif activity_minutes_per_week:
        if activity_minutes_per_week < 30:
            activity_factor = 1.2
        elif activity_minutes_per_week < 150:
            activity_factor = 1.375
        elif activity_minutes_per_week < 300:
            activity_factor = 1.55
        elif activity_minutes_per_week < 420:
            activity_factor = 1.725
        else:
            activity_factor = 1.9
    else:
        activity_factor = 1.2  # Default to sedentary

    return bmr * activity_factor


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test max heart rate calculations
    print("=== MAX HEART RATE CALCULATIONS ===")
    age = 30
    weight = 70

    print(f"\nFor a {age}-year-old weighing {weight} kg:")
    print(f"Simple (220-age): {calculate_max_heart_rate(age, method='simple')} BPM")
    print(f"Tanaka (recommended): {calculate_max_heart_rate(age, method='tanaka')} BPM")
    print(f"Inbar (weight-adjusted): {calculate_max_heart_rate(age, weight, method='inbar')} BPM")

    # Test heart rate zones
    max_hr = calculate_max_heart_rate(age, weight, method="inbar")
    print(f"\n=== HEART RATE ZONES (Max HR: {max_hr}) ===")
    zones = calculate_heart_rate_zones(max_hr)
    for zone_name, zone_info in zones.items():
        print(f"{zone_info['name']}: {zone_info['range'][0]}-{zone_info['range'][1]} BPM - {zone_info['benefit']}")
