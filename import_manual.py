# ============================================================================
# IMPORT_MANUAL.PY - Manual data import from exported files
# ============================================================================
# Supports importing data from various export formats:
# - Zepp/Mi Fit app exports (CSV, JSON)
# - Apple Health exports (XML)
# - Google Fit exports (CSV)
# - Generic CSV files
# ============================================================================

import pandas as pd
import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET


def import_zepp_csv(file_path):
    """
    Import data from Zepp/Mi Fit CSV export.

    Expected format from Zepp app:
    - Date, Time, Heart Rate, Steps, Sleep Stage, SpO2

    Args:
        file_path: Path to the CSV file

    Returns:
        pandas.DataFrame: Standardized data
    """
    try:
        df = pd.read_csv(file_path)

        # Standardize column names (Zepp exports may vary)
        column_mapping = {
            "Date": "date",
            "Time": "time",
            "Heart Rate": "bpm",
            "Heart rate": "bpm",
            "BPM": "bpm",
            "Steps": "steps",
            "Step count": "steps",
            "Sleep": "sleep_stage",
            "Sleep Stage": "sleep_stage",
            "SpO2": "spo2",
            "Blood Oxygen": "spo2",
            "Oxygen": "spo2"
        }

        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)

        # Combine date and time into timestamp
        if "date" in df.columns and "time" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"])
            df.drop(columns=["date", "time"], inplace=True)
        elif "timestamp" not in df.columns and "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])
            df.drop(columns=["date"], inplace=True)

        # Ensure timestamp is first column
        cols = ["timestamp"] + [col for col in df.columns if col != "timestamp"]
        df = df[cols]

        return df

    except Exception as e:
        raise Exception(f"Failed to import Zepp CSV: {e}")


def import_zepp_json(file_path):
    """
    Import data from Zepp/Mi Fit JSON export.

    Args:
        file_path: Path to the JSON file

    Returns:
        pandas.DataFrame: Standardized data
    """
    try:
        with open(file_path) as f:
            data = json.load(f)

        # Zepp JSON format varies, try to extract common structures
        records = []

        # Handle different JSON structures
        if isinstance(data, list):
            # List of records
            for item in data:
                record = {
                    "timestamp": pd.to_datetime(item.get("time") or item.get("timestamp")),
                    "bpm": item.get("heart_rate") or item.get("bpm"),
                    "steps": item.get("steps"),
                    "spo2": item.get("spo2") or item.get("blood_oxygen"),
                    "sleep_stage": item.get("sleep_stage")
                }
                records.append(record)

        elif isinstance(data, dict):
            # Nested structure
            if "data" in data:
                for item in data["data"]:
                    record = {
                        "timestamp": pd.to_datetime(item.get("time") or item.get("timestamp")),
                        "bpm": item.get("heart_rate") or item.get("bpm"),
                        "steps": item.get("steps"),
                        "spo2": item.get("spo2"),
                        "sleep_stage": item.get("sleep_stage")
                    }
                    records.append(record)

        df = pd.DataFrame(records)

        # Remove None values and empty columns
        df = df.dropna(how="all", axis=1)

        return df

    except Exception as e:
        raise Exception(f"Failed to import Zepp JSON: {e}")


def import_apple_health_xml(file_path):
    """
    Import data from Apple Health export.xml.

    Args:
        file_path: Path to export.xml from Apple Health

    Returns:
        pandas.DataFrame: Standardized data
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        records = []

        # Parse health records
        for record in root.findall(".//Record"):
            record_type = record.get("type", "")
            timestamp = pd.to_datetime(record.get("startDate"))

            # Heart rate
            if "HeartRate" in record_type:
                bpm = float(record.get("value", 0))
                records.append({
                    "timestamp": timestamp,
                    "bpm": bpm
                })

            # Steps
            elif "StepCount" in record_type:
                steps = int(float(record.get("value", 0)))
                records.append({
                    "timestamp": timestamp,
                    "steps": steps
                })

            # SpO2
            elif "OxygenSaturation" in record_type:
                spo2 = float(record.get("value", 0)) * 100
                records.append({
                    "timestamp": timestamp,
                    "spo2": spo2
                })

        # Merge records by timestamp
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.groupby("timestamp").first().reset_index()

        return df

    except Exception as e:
        raise Exception(f"Failed to import Apple Health XML: {e}")


def import_google_fit_csv(file_path):
    """
    Import data from Google Fit CSV export.

    Args:
        file_path: Path to Google Fit CSV

    Returns:
        pandas.DataFrame: Standardized data
    """
    try:
        df = pd.read_csv(file_path)

        # Google Fit column names
        if "Start time" in df.columns:
            df["timestamp"] = pd.to_datetime(df["Start time"])

        if "Heart rate (bpm)" in df.columns:
            df["bpm"] = df["Heart rate (bpm)"]

        if "Step count" in df.columns:
            df["steps"] = df["Step count"]

        if "Oxygen saturation (%)" in df.columns:
            df["spo2"] = df["Oxygen saturation (%)"]

        # Keep only relevant columns
        relevant_cols = ["timestamp", "bpm", "steps", "spo2", "sleep_stage"]
        df = df[[col for col in relevant_cols if col in df.columns]]

        return df

    except Exception as e:
        raise Exception(f"Failed to import Google Fit CSV: {e}")


def import_generic_csv(file_path):
    """
    Import generic CSV with automatic column detection.

    Args:
        file_path: Path to CSV file

    Returns:
        pandas.DataFrame: Standardized data
    """
    try:
        df = pd.read_csv(file_path)

        # Try to detect timestamp column
        timestamp_candidates = ["timestamp", "date", "time", "datetime", "Date", "Time"]
        timestamp_col = None

        for candidate in timestamp_candidates:
            if candidate in df.columns:
                timestamp_col = candidate
                break

        if timestamp_col:
            df["timestamp"] = pd.to_datetime(df[timestamp_col])
            if timestamp_col != "timestamp":
                df.drop(columns=[timestamp_col], inplace=True)

        # Standardize other columns
        column_mapping = {
            "heart_rate": "bpm",
            "heartrate": "bpm",
            "hr": "bpm",
            "step_count": "steps",
            "step": "steps",
            "oxygen": "spo2",
            "blood_oxygen": "spo2",
            "sleep": "sleep_stage"
        }

        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)

        return df

    except Exception as e:
        raise Exception(f"Failed to import generic CSV: {e}")


def auto_import(file_path):
    """
    Automatically detect format and import data.

    Args:
        file_path: Path to the file

    Returns:
        pandas.DataFrame: Standardized data
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    # Try different importers based on file type
    if file_ext == ".xml":
        return import_apple_health_xml(file_path)

    elif file_ext == ".json":
        return import_zepp_json(file_path)

    elif file_ext == ".csv":
        # Try Zepp format first, fallback to generic
        try:
            df = import_zepp_csv(file_path)
            if not df.empty:
                return df
        except:
            pass

        # Try Google Fit format
        try:
            df = import_google_fit_csv(file_path)
            if not df.empty:
                return df
        except:
            pass

        # Fallback to generic CSV
        return import_generic_csv(file_path)

    else:
        raise Exception(f"Unsupported file format: {file_ext}")


def save_imported_data(df, output_path="data/raw/xiaomi_today.csv"):
    """
    Save imported data to standardized format.

    Args:
        df: DataFrame to save
        output_path: Where to save the file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Ensure required columns exist
    required_cols = ["timestamp"]
    for col in required_cols:
        if col not in df.columns:
            raise Exception(f"Missing required column: {col}")

    # Sort by timestamp
    df = df.sort_values("timestamp")

    # Save
    df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(df)} records to {output_path}")


def import_and_save(file_path):
    """
    Import a file and save to standard location.

    Args:
        file_path: Path to file to import

    Returns:
        bool: True if successful
    """
    try:
        print(f"Importing {os.path.basename(file_path)}...")

        # Auto-detect and import
        df = auto_import(file_path)

        if df.empty:
            print("⚠️ No data found in file")
            return False

        # Save to standard location
        save_imported_data(df)

        print(f"✅ Successfully imported {len(df)} records")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


# For testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        import_and_save(file_path)
    else:
        print("Usage: python import_manual.py <file_path>")
        print("\nSupported formats:")
        print("  - Zepp/Mi Fit CSV/JSON exports")
        print("  - Apple Health export.xml")
        print("  - Google Fit CSV exports")
        print("  - Generic CSV files")
