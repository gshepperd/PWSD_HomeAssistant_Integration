#!/usr/bin/env python3
"""
Parker Water & Sanitation District - Combined Water Usage Scraper
Fetches monthly total, yesterday's usage, and today's usage (so far)

Based on the working monthly scraper authentication flow
"""

import requests
import json
import sys
import yaml
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

BASE = "https://myaccount.pwsd.org"
CONFIG_DIR = Path(__file__).parent.parent
SECRETS_FILE = CONFIG_DIR / "secrets.yaml"
MONTHLY_OUTPUT_FILE = CONFIG_DIR / "pwsd_monthly_water_usage.json"
YESTERDAY_OUTPUT_FILE = CONFIG_DIR / "pwsd_yesterday_water_usage.json"
TODAY_OUTPUT_FILE = CONFIG_DIR / "pwsd_today_water_usage.json"


class PWSDClient:
    def __init__(self, username, password, account_number, meter):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.meter = meter

        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Origin": BASE,
            "Referer": f"{BASE}/login",
            "X-Requested-With": "XMLHttpRequest"
        })

    def login(self):
        """Login to PWSD using their authentication flow"""
        log.info("STEP 1: Fetching /login to get CSRF + AWS cookies...")
        r = self.s.get(f"{BASE}/login", timeout=10)
        r.raise_for_status()

        # Browser uses Basic Auth header
        basic = requests.auth._basic_auth_str(self.username, self.password)

        payload = {
            "j_username": self.username,
            "j_password": self.password
        }

        self.s.headers.update({
            "Authorization": basic,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        })

        log.info("STEP 2: Posting login form to /api/authenticate ...")
        r = self.s.post(f"{BASE}/api/authenticate", data=payload, timeout=15)

        if r.status_code != 200:
            log.error("Login failed: %s", r.text)
            return False

        # Confirm the session cookie exists
        if "PLAY_SESSION_SESUG" not in self.s.cookies:
            log.error("Login failed — session cookie not set")
            return False

        log.info("✓ LOGIN SUCCESS (PLAY_SESSION_SESUG acquired)")
        return True

    def get_monthly_usage(self):
        """Get monthly usage data from the past 2 years API endpoint"""
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_month_name = now.strftime("%B")
        
        # Use timestamp as cache buster (like the browser does)
        timestamp = int(time.time() * 1000)
        
        # Build the API URL
        url = f"{BASE}/api/shared/smart-meter-usage-past-2-years?meterNumber={self.meter}&_={timestamp}"
        
        log.info(f"STEP 3: Requesting monthly usage from smart-meter-usage-past-2-years API")
        log.info(f"   Looking for: {current_month_name} {current_year}")
        
        r = self.s.get(url, timeout=15)

        if r.status_code == 401:
            log.error("Unauthorized — session not accepted by PWSD server.")
            return None
        
        if r.status_code != 200:
            log.error(f"API request failed with status {r.status_code}")
            return None

        try:
            data = r.json()
        except:
            log.error("Invalid JSON returned: %s", r.text[:200])
            return None

        # Data structure: {meter_id: {data: [{consumption, date, ...}]}}
        if self.meter not in data:
            log.error(f"Meter {self.meter} not found in API response")
            log.error(f"Available keys: {list(data.keys())}")
            return None
        
        meter_data = data[self.meter]
        readings = meter_data.get("data", [])
        
        if not readings:
            log.error("No readings found in API response")
            return None
        
        log.info(f"✓ Received {len(readings)} months of data")
        
        # Find the current month's data
        current_month_data = None
        
        for reading in readings:
            date_str = reading.get("date", "")
            try:
                # Parse the date string
                reading_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                
                # Check if this is the current month
                if reading_date.year == current_year and reading_date.month == current_month:
                    current_month_data = reading
                    log.info(f"✓ Found current month data: {date_str}")
                    break
            except Exception as e:
                log.debug(f"Could not parse date {date_str}: {e}")
                continue
        
        if not current_month_data:
            log.warning(f"Could not find data for {current_month_name} {current_year}")
            
            # Fall back to the most recent reading
            if readings:
                log.info("Using most recent reading as fallback...")
                current_month_data = readings[-1]
        
        consumption = current_month_data.get("consumption")
        reading_total = current_month_data.get("reading")
        date_str = current_month_data.get("date", "")
        
        if consumption is None:
            log.error("'consumption' not found in reading")
            return None
        
        log.info(f"✓ Successfully extracted usage: {consumption} gallons")
        
        return {
            "value": consumption,
            "unit": "gallons",
            "month": current_month_name,
            "year": current_year,
            "period": "monthly",
            "meter_reading": reading_total,
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "source_type": "smart_meter_api",
            "source_url": "/api/shared/smart-meter-usage-past-2-years"
        }

    def get_daily_usage(self, date, label="day"):
        """
        Fetch daily water usage from the interval API for a specific date
        
        Args:
            date: datetime object for the date to fetch
            label: description for logging (e.g., "yesterday", "today")
        """
        date_str = date.strftime('%Y-%m-%d')
        
        # Date range: full 24-hour period
        start_date = f"{date_str}T00:00-07:00"
        end_date = f"{date_str}T23:59-07:00"
        
        # Use timestamp as cache buster
        timestamp = int(time.time() * 1000)
        
        # Build API URL
        url = (
            f"{BASE}/api/shared/interval"
            f"?account_number={self.account_number}"
            f"&start_date={start_date}"
            f"&end_date={end_date}"
            f"&service_category=WATER"
            f"&graphs=%5B%5D"
            f"&format=json"
            f"&meter_id={self.meter}"
            f"&period=Daily"
            f"&_={timestamp}"
        )
        
        log.info(f"Requesting {label}'s usage from interval API")
        log.info(f"   Date: {date_str}")
        
        r = self.s.get(url, timeout=15)
        
        if r.status_code == 401:
            log.error("Unauthorized — session not accepted by PWSD server.")
            return None
        
        if r.status_code != 200:
            log.error(f"API request failed with status {r.status_code}")
            return None
        
        try:
            data = r.json()
        except:
            log.error("Invalid JSON returned: %s", r.text[:200])
            return None
        
        # Find the water consumption series
        water_series = None
        for series in data:
            if (series.get('seriesGroup') == 'Water' and 
                series.get('measurementType') == 'Consumption'):
                water_series = series
                break
        
        if not water_series:
            log.error("Could not find water consumption data in response")
            return None
        
        # Get data points
        data_points = water_series.get('dataPoints', [])
        
        if not data_points:
            log.warning(f"No data points found for {date_str}")
            log.warning(f"Meter reading may not be available yet for {label}")
            return None
        
        # Find the specific data point for this date
        day_data = None
        for point in data_points:
            point_date = point['date'].split('T')[0]  # Extract date part
            if point_date == date_str:
                day_data = point
                break
        
        if not day_data:
            log.warning(f"Could not find data for {date_str}")
            available_dates = [p['date'].split('T')[0] for p in data_points]
            log.warning(f"Available dates: {available_dates}")
            return None
        
        usage = day_data['value']
        log.info(f"✓ {label.capitalize()}'s usage: {usage} gallons")
        
        return {
            'value': usage,
            'unit': 'gallons',
            'date': date_str,
            'full_date': day_data['date'],
            'meter_number': day_data['meterNumber'],
            'measurement_type': 'Daily Consumption',
            'source_type': 'interval_api',
            'source_url': '/api/shared/interval',
            'timestamp': datetime.now().isoformat()
        }


def load_config():
    """Load configuration from secrets.yaml or environment variables"""
    config = {}
    
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, 'r') as f:
                secrets = yaml.safe_load(f)
                config['username'] = secrets.get('pwsd_username')
                config['password'] = secrets.get('pwsd_password')
                config['account_number'] = secrets.get('pwsd_account_number')
                config['meter'] = secrets.get('pwsd_meter_id')
        except Exception as e:
            log.error(f"Error loading secrets.yaml: {e}")
    
    # Fallback to environment variables
    if not config.get('username'):
        config['username'] = os.getenv('PWSD_USERNAME')
    if not config.get('password'):
        config['password'] = os.getenv('PWSD_PASSWORD')
    if not config.get('account_number'):
        config['account_number'] = os.getenv('PWSD_ACCOUNT_NUMBER')
    if not config.get('meter'):
        config['meter'] = os.getenv('PWSD_METER_ID')
    
    return config


def save_json(data, output_file):
    """Save data to JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        log.error(f"Error saving to {output_file}: {e}")
        return False


def main():
    log.info("=" * 80)
    log.info("Parker Water & Sanitation District - Complete Water Usage")
    log.info("Fetching: Monthly Total + Yesterday's Usage + Today's Usage")
    log.info("=" * 80)
    
    cfg = load_config()

    # Validate configuration
    missing = []
    if not cfg.get('username'):
        missing.append('pwsd_username')
    if not cfg.get('password'):
        missing.append('pwsd_password')
    if not cfg.get('account_number'):
        missing.append('pwsd_account_number')
    if not cfg.get('meter'):
        missing.append('pwsd_meter_id')
    
    if missing:
        log.error("Missing configuration values in secrets.yaml:")
        for key in missing:
            log.error(f"  - {key}")
        log.error("\nAdd these to /config/secrets.yaml:")
        log.error("  pwsd_username: your_email@example.com")
        log.error("  pwsd_password: your_password")
        log.error("  pwsd_account_number: 1005495")
        log.error("  pwsd_meter_id: 82597769")
        sys.exit(1)

    client = PWSDClient(
        cfg['username'],
        cfg['password'],
        cfg['account_number'],
        cfg['meter']
    )

    if not client.login():
        log.error("=" * 80)
        log.error("FINAL: Login failed")
        log.error("=" * 80)
        sys.exit(1)

    # Get monthly usage
    log.info("")
    log.info("--- MONTHLY USAGE ---")
    monthly_usage = client.get_monthly_usage()
    monthly_success = False
    if monthly_usage:
        if save_json(monthly_usage, MONTHLY_OUTPUT_FILE):
            log.info(f"✓ Monthly data saved to: {MONTHLY_OUTPUT_FILE}")
            monthly_success = True

    # Get yesterday's usage
    log.info("")
    log.info("--- YESTERDAY'S USAGE ---")
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_usage = client.get_daily_usage(yesterday, "yesterday")
    yesterday_success = False
    if yesterday_usage:
        if save_json(yesterday_usage, YESTERDAY_OUTPUT_FILE):
            log.info(f"✓ Yesterday's data saved to: {YESTERDAY_OUTPUT_FILE}")
            yesterday_success = True

    # Get today's usage (so far)
    log.info("")
    log.info("--- TODAY'S USAGE (SO FAR) ---")
    today = datetime.now()
    today_usage = client.get_daily_usage(today, "today")
    today_success = False
    if today_usage:
        if save_json(today_usage, TODAY_OUTPUT_FILE):
            log.info(f"✓ Today's data saved to: {TODAY_OUTPUT_FILE}")
            today_success = True
    else:
        log.info("⚠️  Today's data not available yet (meter may not be read until tomorrow)")

    # Summary
    log.info("=" * 80)
    if monthly_success and yesterday_success:
        log.info("✓ SUCCESS! Data retrieved:")
        log.info(f"   Monthly Total: {monthly_usage['value']} gal ({monthly_usage['month']} {monthly_usage['year']})")
        log.info(f"   Yesterday: {yesterday_usage['value']} gal ({yesterday_usage['date']})")
        if today_success:
            log.info(f"   Today (so far): {today_usage['value']} gal ({today_usage['date']})")
        else:
            log.info(f"   Today (so far): Not available yet")
    elif monthly_success:
        log.info("⚠️  PARTIAL SUCCESS: Monthly data only")
        log.info(f"   Monthly Total: {monthly_usage['value']} gal")
    else:
        log.error("❌ FAILED: Could not retrieve data")
        sys.exit(1)
    log.info("=" * 80)


if __name__ == "__main__":
    main()
