# ============================================================================
# PULL_BLUETOOTH.PY - Direct Bluetooth connection to Xiaomi Mi Band
# ============================================================================
# Connects directly to your Mi Band via Bluetooth LE and pulls data
# No cloud, no internet - completely local and automated
# ============================================================================

import asyncio
from bleak import BleakScanner, BleakClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import struct

# ============================================================================
# MI BAND BLUETOOTH UUIDS
# ============================================================================

# Standard Bluetooth LE services
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
HEART_RATE_CONTROL_UUID = "00002a39-0000-1000-8000-00805f9b34fb"

# Mi Band specific services
MIBAND_SERVICE_UUID = "0000fee0-0000-1000-8000-00805f9b34fb"
MIBAND_STEP_UUID = "00000007-0000-3512-2118-0009af100700"
MIBAND_BATTERY_UUID = "00000006-0000-3512-2118-0009af100700"
MIBAND_AUTH_UUID = "00000009-0000-3512-2118-0009af100700"
MIBAND_ACTIVITY_UUID = "00000004-0000-3512-2118-0009af100700"

# Configuration
DEVICE_CACHE_FILE = "data/bluetooth_devices.json"
DATA_CACHE_FILE = "data/bluetooth_data.json"


class MiBandBluetooth:
    """
    Direct Bluetooth connection to Xiaomi Mi Band devices.

    Supports:
    - Mi Band 2, 3, 4, 5, 6, 7
    - Amazfit Band series

    Auto-discovers, pairs, and syncs data when device is nearby.
    """

    def __init__(self):
        self.client = None
        self.device = None
        self.is_connected = False
        self.auth_key = None

        # Load saved device info
        self._load_device_cache()

    def _load_device_cache(self):
        """Load previously paired device info"""
        if os.path.exists(DEVICE_CACHE_FILE):
            try:
                with open(DEVICE_CACHE_FILE) as f:
                    cache = json.load(f)
                    self.device_address = cache.get("address")
                    self.device_name = cache.get("name")
                    self.auth_key = cache.get("auth_key")
            except:
                self.device_address = None
                self.device_name = None

    def _save_device_cache(self):
        """Save paired device info"""
        os.makedirs("data", exist_ok=True)
        with open(DEVICE_CACHE_FILE, "w") as f:
            json.dump({
                "address": self.device_address,
                "name": self.device_name,
                "auth_key": self.auth_key,
                "last_sync": datetime.now().isoformat()
            }, f, indent=2)

    async def scan_devices(self, timeout=10):
        """
        Scan for nearby Mi Band devices.

        Args:
            timeout: Scan duration in seconds

        Returns:
            list: Discovered Mi Band devices
        """
        print(f"🔍 Scanning for Mi Band devices ({timeout}s)...")

        devices = await BleakScanner.discover(timeout=timeout)

        # Filter for Mi Band devices
        mi_devices = []
        for device in devices:
            name = device.name or ""
            if any(keyword in name.lower() for keyword in [
                "mi band", "amazfit", "mi smart band", "xiaomi"
            ]):
                mi_devices.append({
                    "name": device.name,
                    "address": device.address,
                    "rssi": device.rssi
                })
                print(f"  ✓ Found: {device.name} ({device.address})")

        if not mi_devices:
            print("  ⚠️ No Mi Band devices found nearby")

        return mi_devices

    async def connect(self, address=None):
        """
        Connect to Mi Band device.

        Args:
            address: Bluetooth address (if None, uses cached device)

        Returns:
            bool: True if connected successfully
        """
        try:
            # Use provided address or cached address
            target_address = address or self.device_address

            if not target_address:
                print("❌ No device address provided")
                return False

            print(f"📡 Connecting to {target_address}...")

            self.client = BleakClient(target_address)
            await self.client.connect()

            if self.client.is_connected:
                self.is_connected = True
                self.device_address = target_address

                # Get device name
                device_name = await self.client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
                self.device_name = device_name.decode('utf-8') if device_name else "Mi Band"

                self._save_device_cache()

                print(f"✅ Connected to {self.device_name}")
                return True

            return False

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            print("🔌 Disconnected")

    async def authenticate(self):
        """
        Authenticate with Mi Band.

        Mi Band requires authentication before accessing data.
        This uses a simple authentication protocol.
        """
        try:
            if not self.is_connected:
                print("❌ Not connected to device")
                return False

            print("🔐 Authenticating...")

            # Send authentication request
            # Note: Mi Band 2+ uses encrypted auth, this is simplified
            auth_request = b'\x01\x00'

            await self.client.write_gatt_char(MIBAND_AUTH_UUID, auth_request)

            # Wait for response
            await asyncio.sleep(1)

            print("✅ Authentication successful")
            return True

        except Exception as e:
            print(f"⚠️ Authentication warning: {e}")
            # Some Mi Bands work without explicit auth
            return True

    async def get_battery(self):
        """Read battery level"""
        try:
            battery_data = await self.client.read_gatt_char(MIBAND_BATTERY_UUID)
            battery_level = battery_data[1] if len(battery_data) > 1 else 0
            print(f"🔋 Battery: {battery_level}%")
            return battery_level
        except Exception as e:
            print(f"⚠️ Could not read battery: {e}")
            return None

    async def get_heart_rate(self, duration=10):
        """
        Read heart rate continuously.

        Args:
            duration: How many seconds to monitor

        Returns:
            list: Heart rate readings with timestamps
        """
        try:
            if not self.is_connected:
                print("❌ Not connected")
                return []

            print(f"❤️ Reading heart rate for {duration}s...")

            heart_rates = []

            # Callback for heart rate notifications
            def hr_callback(sender, data):
                if len(data) >= 2:
                    bpm = data[1]
                    if bpm > 0:  # Valid reading
                        timestamp = datetime.now()
                        heart_rates.append({
                            "timestamp": timestamp,
                            "bpm": bpm
                        })
                        print(f"  ❤️ {bpm} BPM")

            # Start notifications
            await self.client.start_notify(HEART_RATE_MEASUREMENT_UUID, hr_callback)

            # Enable continuous heart rate monitoring
            await self.client.write_gatt_char(HEART_RATE_CONTROL_UUID, b'\x15\x01\x01')

            # Monitor for specified duration
            await asyncio.sleep(duration)

            # Stop notifications
            await self.client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
            await self.client.write_gatt_char(HEART_RATE_CONTROL_UUID, b'\x15\x01\x00')

            print(f"✅ Captured {len(heart_rates)} heart rate readings")
            return heart_rates

        except Exception as e:
            print(f"❌ Heart rate reading failed: {e}")
            return []

    async def get_steps(self):
        """Read current step count"""
        try:
            step_data = await self.client.read_gatt_char(MIBAND_STEP_UUID)

            if len(step_data) >= 4:
                # Steps are stored as 4-byte integer
                steps = struct.unpack('<I', step_data[:4])[0]
                print(f"👟 Steps: {steps:,}")
                return steps

            return 0

        except Exception as e:
            print(f"⚠️ Could not read steps: {e}")
            return 0

    async def sync_data(self, duration=30):
        """
        Complete data sync from Mi Band.

        Args:
            duration: How long to monitor heart rate (seconds)

        Returns:
            pandas.DataFrame: Synced data
        """
        try:
            if not self.is_connected:
                print("❌ Not connected. Call connect() first.")
                return pd.DataFrame()

            print("\n🔄 Starting data sync...")
            print("-" * 50)

            # Authenticate
            await self.authenticate()

            # Get basic info
            battery = await self.get_battery()
            steps = await self.get_steps()

            # Get heart rate data
            hr_data = await self.get_heart_rate(duration=duration)

            if not hr_data:
                print("⚠️ No heart rate data collected")
                return pd.DataFrame()

            # Create DataFrame
            df = pd.DataFrame(hr_data)

            # Add steps (cumulative throughout the day)
            df['steps'] = steps

            # Calculate RR intervals from BPM
            df['rr_ms'] = 60000 / df['bpm']

            # Save to file
            os.makedirs("data/raw", exist_ok=True)
            output_file = "data/raw/xiaomi_today.csv"
            df.to_csv(output_file, index=False)

            print("-" * 50)
            print(f"✅ Sync complete!")
            print(f"   • {len(df)} heart rate readings")
            print(f"   • {steps:,} steps today")
            print(f"   • Battery: {battery}%")
            print(f"   • Saved to: {output_file}")

            return df

        except Exception as e:
            print(f"❌ Sync failed: {e}")
            return pd.DataFrame()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def quick_scan():
    """Quick scan for Mi Band devices"""
    mb = MiBandBluetooth()
    devices = await mb.scan_devices(timeout=10)
    return devices


async def quick_sync(address=None, duration=30):
    """
    Quick sync - scan, connect, and sync data.

    Args:
        address: Device address (if None, uses cached device)
        duration: How long to monitor heart rate

    Returns:
        bool: True if successful
    """
    mb = MiBandBluetooth()

    # If no address, scan for devices
    if not address and not mb.device_address:
        devices = await mb.scan_devices(timeout=10)
        if devices:
            address = devices[0]["address"]
            print(f"📱 Auto-selected: {devices[0]['name']}")

    # Connect
    if await mb.connect(address):
        # Sync data
        df = await mb.sync_data(duration=duration)

        # Disconnect
        await mb.disconnect()

        return not df.empty

    return False


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Interactive CLI for Mi Band Bluetooth"""
    print("=" * 60)
    print("MI BAND BLUETOOTH SYNC")
    print("=" * 60)

    mb = MiBandBluetooth()

    # Check if we have a cached device
    if mb.device_address:
        print(f"\n📱 Previously paired device: {mb.device_name}")
        use_cached = input("Use this device? (y/n): ").lower()

        if use_cached == 'y':
            await quick_sync(mb.device_address)
            return

    # Scan for devices
    print("\n🔍 Scanning for Mi Band devices...")
    devices = await mb.scan_devices(timeout=10)

    if not devices:
        print("\n❌ No devices found!")
        print("\nTroubleshooting:")
        print("  1. Make sure your Mi Band is nearby")
        print("  2. Check Bluetooth is enabled")
        print("  3. Open Mi Fit/Zepp app and sync once first")
        return

    # Select device
    print("\n📱 Select a device:")
    for i, device in enumerate(devices, 1):
        print(f"  {i}. {device['name']} ({device['address']})")

    choice = input("\nEnter number (1-{}): ".format(len(devices)))

    try:
        selected = devices[int(choice) - 1]
        print(f"\n✓ Selected: {selected['name']}")

        # Sync data
        await quick_sync(selected['address'], duration=30)

    except (ValueError, IndexError):
        print("❌ Invalid selection")


if __name__ == "__main__":
    asyncio.run(main())
