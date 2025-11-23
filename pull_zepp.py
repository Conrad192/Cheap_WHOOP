# ============================================================================
# PULL_ZEPP.PY - Real Xiaomi Mi Band / Amazfit data via Zepp API
# ============================================================================
# Connects to Zepp (Amazfit) API to pull real data from your watch
# Supports: Mi Band series, Amazfit watches
# ============================================================================

import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import hashlib
import hmac
import time

class ZeppAPI:
    """
    Interface to Zepp API for Xiaomi Mi Band and Amazfit devices.

    Note: This uses the Zepp Life (formerly Amazfit/Mi Fit) cloud API.
    Users need their Zepp/Mi Fit account credentials.
    """

    def __init__(self):
        self.base_url = "https://api-mifit.huami.com"
        self.app_token = None
        self.user_id = None
        self.session = requests.Session()

        # Load saved credentials if available
        self.credentials_file = "data/zepp_credentials.json"
        self._load_credentials()

    def _load_credentials(self):
        """Load saved authentication credentials"""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file) as f:
                    creds = json.load(f)
                    self.app_token = creds.get("app_token")
                    self.user_id = creds.get("user_id")
            except:
                pass

    def _save_credentials(self):
        """Save authentication credentials"""
        os.makedirs("data", exist_ok=True)
        with open(self.credentials_file, "w") as f:
            json.dump({
                "app_token": self.app_token,
                "user_id": self.user_id,
                "last_login": datetime.now().isoformat()
            }, f, indent=2)

    def login(self, email, password):
        """
        Login to Zepp API with email and password.

        Args:
            email: Your Zepp/Mi Fit account email
            password: Your account password

        Returns:
            bool: True if login successful
        """
        try:
            # Zepp API login endpoint
            login_url = f"{self.base_url}/v1/user/login"

            # Generate app token signature (required by API)
            timestamp = str(int(time.time() * 1000))

            # Login request
            response = self.session.post(login_url, data={
                "email": email,
                "password": hashlib.md5(password.encode()).hexdigest(),
                "app_name": "com.xiaomi.hm.health",
                "third_name": "huami_phone",
                "device_id": "02:00:00:00:00:00",
                "device_model": "android_phone",
                "app_version": "6.0.0",
                "country_code": "US",
                "lang": "en_US"
            })

            if response.status_code == 200:
                data = response.json()
                self.app_token = data.get("token_info", {}).get("app_token")
                self.user_id = data.get("token_info", {}).get("user_id")

                if self.app_token and self.user_id:
                    self._save_credentials()
                    return True

            return False

        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.app_token is not None and self.user_id is not None

    def get_heart_rate_data(self, date=None):
        """
        Get heart rate data for a specific date.

        Args:
            date: datetime object (default: today)

        Returns:
            pandas.DataFrame with columns: timestamp, bpm
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")

        if date is None:
            date = datetime.now()

        # Format date for API (YYYY-MM-DD)
        date_str = date.strftime("%Y-%m-%d")

        # Zepp heart rate endpoint
        url = f"{self.base_url}/v1/data/band_data.json"

        params = {
            "query_type": "heart_rate",
            "device_type": "0",
            "userid": self.user_id,
            "from_date": date_str,
            "to_date": date_str,
            "apptoken": self.app_token
        }

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            hr_data = data.get("data", [])

            # Parse heart rate data
            records = []
            for item in hr_data:
                timestamp = datetime.fromtimestamp(item.get("time", 0))
                bpm = item.get("value", 0)
                records.append({"timestamp": timestamp, "bpm": bpm})

            return pd.DataFrame(records)

        return pd.DataFrame()

    def get_sleep_data(self, date=None):
        """
        Get sleep data for a specific date.

        Args:
            date: datetime object (default: last night)

        Returns:
            pandas.DataFrame with columns: timestamp, sleep_stage
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")

        if date is None:
            date = datetime.now() - timedelta(days=1)

        date_str = date.strftime("%Y-%m-%d")

        url = f"{self.base_url}/v1/data/band_data.json"

        params = {
            "query_type": "sleep",
            "device_type": "0",
            "userid": self.user_id,
            "from_date": date_str,
            "to_date": date_str,
            "apptoken": self.app_token
        }

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            sleep_data = data.get("data", [])

            records = []
            for item in sleep_data:
                timestamp = datetime.fromtimestamp(item.get("start", 0))
                # Sleep stages: 1=light, 2=deep, 3=REM, 0=awake
                stage = item.get("stage", 0)
                records.append({"timestamp": timestamp, "sleep_stage": stage})

            return pd.DataFrame(records)

        return pd.DataFrame()

    def get_steps_data(self, date=None):
        """
        Get step count data for a specific date.

        Args:
            date: datetime object (default: today)

        Returns:
            pandas.DataFrame with columns: timestamp, steps
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")

        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        url = f"{self.base_url}/v1/data/band_data.json"

        params = {
            "query_type": "steps",
            "device_type": "0",
            "userid": self.user_id,
            "from_date": date_str,
            "to_date": date_str,
            "apptoken": self.app_token
        }

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            steps_data = data.get("data", [])

            records = []
            for item in steps_data:
                timestamp = datetime.fromtimestamp(item.get("time", 0))
                steps = item.get("value", 0)
                records.append({"timestamp": timestamp, "steps": steps})

            return pd.DataFrame(records)

        return pd.DataFrame()

    def get_spo2_data(self, date=None):
        """
        Get SpO2 (blood oxygen) data for a specific date.

        Args:
            date: datetime object (default: today)

        Returns:
            pandas.DataFrame with columns: timestamp, spo2
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")

        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        url = f"{self.base_url}/v1/data/band_data.json"

        params = {
            "query_type": "spo2",
            "device_type": "0",
            "userid": self.user_id,
            "from_date": date_str,
            "to_date": date_str,
            "apptoken": self.app_token
        }

        response = self.session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            spo2_data = data.get("data", [])

            records = []
            for item in spo2_data:
                timestamp = datetime.fromtimestamp(item.get("time", 0))
                spo2 = item.get("value", 0)
                records.append({"timestamp": timestamp, "spo2": spo2})

            return pd.DataFrame(records)

        return pd.DataFrame()

    def get_all_data(self, date=None):
        """
        Get all available data for a specific date.

        Returns merged dataframe with all metrics.
        """
        if date is None:
            date = datetime.now()

        # Fetch all data types
        hr_df = self.get_heart_rate_data(date)
        sleep_df = self.get_sleep_data(date)
        steps_df = self.get_steps_data(date)
        spo2_df = self.get_spo2_data(date)

        # Merge all data on timestamp
        if not hr_df.empty:
            df = hr_df
            if not sleep_df.empty:
                df = df.merge(sleep_df, on="timestamp", how="outer")
            if not steps_df.empty:
                df = df.merge(steps_df, on="timestamp", how="outer")
            if not spo2_df.empty:
                df = df.merge(spo2_df, on="timestamp", how="outer")

            # Sort by timestamp and fill missing values
            df = df.sort_values("timestamp").fillna(method="ffill")

            # Save to file
            os.makedirs("data/raw", exist_ok=True)
            df.to_csv("data/raw/xiaomi_today.csv", index=False)

            return df

        return pd.DataFrame()


def pull_zepp_data(email=None, password=None):
    """
    Convenience function to pull data from Zepp API.

    Args:
        email: Zepp account email (optional if already logged in)
        password: Zepp account password (optional if already logged in)

    Returns:
        bool: True if data was successfully pulled
    """
    api = ZeppAPI()

    # Login if credentials provided and not authenticated
    if email and password and not api.is_authenticated():
        if not api.login(email, password):
            print("❌ Login failed. Check your credentials.")
            return False

    if not api.is_authenticated():
        print("❌ Not authenticated. Please login first.")
        return False

    # Pull today's data
    df = api.get_all_data()

    if not df.empty:
        print(f"✅ Successfully pulled {len(df)} data points from Zepp")
        return True
    else:
        print("⚠️ No data available for today")
        return False


# For testing
if __name__ == "__main__":
    print("Zepp API Integration Test")
    print("-" * 50)

    # Test with manual credentials
    email = input("Enter your Zepp/Mi Fit email: ")
    password = input("Enter your password: ")

    pull_zepp_data(email, password)
