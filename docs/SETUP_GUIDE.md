# PWSD Home Assistant Integration - Setup Guide

Complete step-by-step installation instructions.

## Prerequisites

Before you begin, make sure you have:
- ✅ Home Assistant 2023.1 or newer
- ✅ PWSD customer account at https://myaccount.pwsd.org
- ✅ SSH or Terminal access to your Home Assistant instance
- ✅ Your PWSD account number and meter ID

## Step 0: Install Required Python Packages

**⚠️ IMPORTANT:** You must install Python dependencies before running the script!

### Install requests and pyyaml

SSH into your Home Assistant instance and run:

```bash
pip3 install --break-system-packages requests pyyaml
```

**Why `--break-system-packages`?**
- Home Assistant OS uses a read-only system partition
- This flag allows installing packages outside virtual environments
- This is safe and necessary for Home Assistant OS

### Verify Installation

```bash
python3 -c "import requests, yaml; print('✓ Packages installed successfully!')"
```

**Expected output:**
```
✓ Packages installed successfully!
```

### Troubleshooting Package Installation

**Error:** `pip3: command not found`

**Solution:** Use Home Assistant's Python directly:
```bash
/usr/local/bin/python3 -m pip install --break-system-packages requests pyyaml
```

**Error:** `Permission denied`

**Solution:** Make sure you're SSH'd in as root or use sudo:
```bash
sudo pip3 install --break-system-packages requests pyyaml
```

---

## Step 1: Find Your PWSD Account Information

### Account Number
1. Log into https://myaccount.pwsd.org
2. Look at the URL after logging in
3. Example: `https://myaccount.pwsd.org/dashboard?account=1234567`
4. Your account number is `1234567`

### Meter ID
1. In the PWSD portal, go to **Customer** → **Water Smart Meters**
2. Your meter number will be displayed (e.g., `12345678`)
3. Note this number

---

## Step 2: Install the Python Script

### Option A: Download Directly
```bash
cd /config/python_scripts
wget https://raw.githubusercontent.com/gshepperd/PWSD_HomeAssistant_Integration/main/python_scripts/pwsd_water_scraper.py
chmod +x pwsd_water_scraper.py
```

### Option B: Manual Upload
1. Download `pwsd_water_scraper.py` from this repository
2. Upload to `/config/python_scripts/` using:
   - File Editor add-on
   - Samba share
   - SSH/SCP

### Verify Installation
```bash
ls -la /config/python_scripts/pwsd_water_scraper.py
```

Should show the file with execute permissions.

---

## Step 3: Add Credentials

Edit `/config/secrets.yaml` and add:

```yaml
# Parker Water & Sanitation District
pwsd_username: "your_email@example.com"
pwsd_password: "your_password"
pwsd_account_number: "1234567"
pwsd_meter_id: "12345678"
```

**Replace with your actual values!**

**Security Note:** Never commit `secrets.yaml` to git or share publicly!

---

## Step 4: Test the Script

Before integrating with Home Assistant, test the script manually:

```bash
python3 /config/python_scripts/pwsd_water_scraper.py
```

**Expected output:**
```
================================================================================
Parker Water & Sanitation District - Complete Water Usage
Fetching: Monthly Total + Yesterday's Usage + Today's Usage
================================================================================
STEP 1: Fetching /login to get CSRF + AWS cookies...
STEP 2: Posting login form to /api/authenticate ...
✓ LOGIN SUCCESS (PLAY_SESSION_SESUG acquired)

--- MONTHLY USAGE ---
✓ Successfully extracted usage: 2145 gallons

--- YESTERDAY'S USAGE ---
✓ Yesterday's usage: 156 gallons

--- TODAY'S USAGE (SO FAR) ---
✓ Today's usage: 45 gallons

✓ SUCCESS! Data retrieved:
   Monthly Total: 2145 gal (November 2025)
   Yesterday: 156 gal (2025-11-17)
   Today (so far): 45 gal (2025-11-18)
================================================================================
```

**Verify JSON files were created:**
```bash
ls -la /config/pwsd_*.json
```

Should show:
- `pwsd_monthly_water_usage.json`
- `pwsd_yesterday_water_usage.json`
- `pwsd_today_water_usage.json`

---

## Step 5: Configure Home Assistant

### 5.1: Add Shell Command

Edit `/config/configuration.yaml` and add:

```yaml
# Shell command to run PWSD water usage script
shell_command:
  update_pwsd_water: "python3 /config/python_scripts/pwsd_water_scraper.py"

# Optional: Manual update button
input_button:
  update_pwsd_water_now:
    name: Update Water Usage Now
    icon: mdi:water-sync
```

### 5.2: Add Command Line Sensors

Create or edit `/config/command_line.yaml`:

```yaml
# Monthly water usage (for Energy Dashboard)
- sensor:
    command: "cat /config/pwsd_monthly_water_usage.json"
    name: "PWSD Monthly Water Usage"
    scan_interval: 3600
    unique_id: pwsd_monthly_water_usage
    value_template: "{{ value_json.value }}"
    unit_of_measurement: "gal"
    device_class: water
    state_class: total
    icon: mdi:water
    json_attributes:
      - unit
      - month
      - year
      - period
      - meter_reading
      - date
      - timestamp
      - source_type
      - source_url

# Yesterday's actual water usage
- sensor:
    command: "cat /config/pwsd_yesterday_water_usage.json"
    name: "PWSD Yesterday Water Usage"
    scan_interval: 3600
    unique_id: pwsd_yesterday_water_usage
    value_template: "{{ value_json.value }}"
    unit_of_measurement: "gal"
    device_class: water
    state_class: total_increasing
    icon: mdi:water-minus
    json_attributes:
      - unit
      - date
      - full_date
      - meter_number
      - measurement_type
      - source_type
      - source_url
      - timestamp

# Today's water usage so far
- sensor:
    command: "cat /config/pwsd_today_water_usage.json"
    name: "PWSD Today Water Usage"
    scan_interval: 1800
    unique_id: pwsd_today_water_usage
    value_template: "{{ value_json.value }}"
    unit_of_measurement: "gal"
    device_class: water
    state_class: total_increasing
    icon: mdi:water
    json_attributes:
      - unit
      - date
      - full_date
      - meter_number
      - measurement_type
      - source_type
      - source_url
      - timestamp
```

Make sure `/config/configuration.yaml` includes:
```yaml
command_line: !include command_line.yaml
```

### 5.3: Add Automations

Edit `/config/automations.yaml` and add:

```yaml
# =============================================================================
# POLLING FREQUENCY: Every 3 hours (adjustable)
# =============================================================================
# PWSD meters are read approximately every 3-4 hours
# Default polling matches this frequency
#
# To change polling frequency, modify "hours:" below:
#   hours: "/3"  = Every 3 hours (DEFAULT - recommended)
#   hours: "/4"  = Every 4 hours (matches meter reading)
#   hours: "/6"  = Every 6 hours (conservative)
#
# ⚠️ WARNING: Polling too frequently may trigger rate limiting from PWSD
# =============================================================================

- id: update_pwsd_water_every_3_hours
  alias: "Update PWSD Water Usage - Every 3 Hours"
  trigger:
    - platform: time_pattern
      hours: "/3"  # ← Change this to adjust frequency
  action:
    - service: shell_command.update_pwsd_water
    - delay: "00:00:20"
    - service: homeassistant.update_entity
      target:
        entity_id: 
          - sensor.pwsd_monthly_water_usage
          - sensor.pwsd_yesterday_water_usage
          - sensor.pwsd_today_water_usage

# Run on startup
- id: update_pwsd_water_startup
  alias: "Update PWSD Water Usage - Startup"
  trigger:
    - platform: homeassistant
      event: start
  action:
    - delay: "00:01:00"
    - service: shell_command.update_pwsd_water

# Manual update button (optional)
- id: manual_pwsd_water_update
  alias: "Manual PWSD Water Update Button"
  trigger:
    - platform: state
      entity_id: input_button.update_pwsd_water_now
  action:
    - service: shell_command.update_pwsd_water
    - delay: "00:00:20"
    - service: homeassistant.update_entity
      target:
        entity_id:
          - sensor.pwsd_monthly_water_usage
          - sensor.pwsd_yesterday_water_usage
          - sensor.pwsd_today_water_usage
```

### 5.4: (Optional) Add Template Sensor

Create or edit `/config/template.yaml`:

```yaml
- sensor:
    - name: "Average Daily Water Usage"
      unique_id: pwsd_avg_daily_usage
      state: >
        {% set total = states('sensor.pwsd_monthly_water_usage') | float(0) %}
        {% set days = now().day %}
        {{ (total / days) | round(0) if days > 0 else 0 }}
      unit_of_measurement: "gal"
      device_class: water
      icon: mdi:water-percent
```

Make sure `/config/configuration.yaml` includes:
```yaml
template: !include template.yaml
```

---

## Step 6: Validate and Restart

1. **Check Configuration**
   - Go to **Developer Tools** → **YAML**
   - Click **"Check Configuration"**
   - Should show "Configuration valid!"

2. **Restart Home Assistant**
   - Go to **Settings** → **System** → **Restart**
   - Wait for restart to complete

---

## Step 7: Verify Sensors

After restart:

1. Go to **Developer Tools** → **States**
2. Search for `pwsd`
3. You should see:
   - `sensor.pwsd_monthly_water_usage`
   - `sensor.pwsd_yesterday_water_usage`
   - `sensor.pwsd_today_water_usage`
   - `sensor.average_daily_water_usage` (if you added the template)

Click on each sensor to verify it has a value.

---

## Step 8: Add to Energy Dashboard

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **"Add Water Source"**
3. Select **`sensor.pwsd_monthly_water_usage`**
4. Click **Save**
5. Wait 24 hours for data to appear in graphs

---

## Step 9: Create Dashboard Card

Go to your dashboard and add a card:

```yaml
type: entities
entities:
  - entity: sensor.pwsd_monthly_water_usage
    name: "Month Total"
  - entity: sensor.pwsd_today_water_usage
    name: "Today So Far"
  - entity: sensor.pwsd_yesterday_water_usage
    name: "Yesterday"
  - entity: sensor.average_daily_water_usage
    name: "Daily Average"
  - entity: input_button.update_pwsd_water_now
    name: "Update Now"
title: PWSD Water Usage
```

---

## Adjusting Polling Frequency

### Current Default: Every 3 Hours

To change the polling frequency, edit the automation in `/config/automations.yaml`:

```yaml
trigger:
  - platform: time_pattern
    hours: "/3"  # ← Change this number
```

### Recommended Settings:

| Frequency | Setting | Notes |
|-----------|---------|-------|
| Every 3 hours | `hours: "/3"` | ✅ **Recommended** - Matches meter reading |
| Every 4 hours | `hours: "/4"` | ✅ Matches meter reading frequency |
| Every 6 hours | `hours: "/6"` | ✅ Conservative |
| Every 2 hours | `hours: "/2"` | ⚠️ Use sparingly |
| Every hour | `hours: "/1"` | ❌ Not recommended - may trigger rate limiting |

### ⚠️ Rate Limiting Considerations:

- **PWSD meters** are read approximately every 3-4 hours
- Polling at 3-4 hour intervals captures all updates
- PWSD may rate limit excessive API requests
- Be respectful of PWSD's infrastructure

---

## Troubleshooting

### Python Package Issues

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip3 install --break-system-packages requests pyyaml
```

### Script fails with "Login failed"
- Double-check username and password in secrets.yaml
- Try logging into https://myaccount.pwsd.org manually

### Sensors show "unavailable"
- Verify JSON files exist: `ls /config/pwsd_*.json`
- Run script manually and check for errors

### Today's usage shows 0
- Meters are read every 3-4 hours
- Wait for next meter reading cycle
- Yesterday's usage is always reliable

For more help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Next Steps

- Set up alerts for high usage
- Create historical graphs
- Track monthly trends
- Compare usage patterns

## Support

If you need help:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue on GitHub
- Check Home Assistant community forums
