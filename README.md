# Parker Water & Sanitation District (PWSD) - Home Assistant Integration

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Automatically track your **Parker Water & Sanitation District (PWSD)** water usage in Home Assistant using their official APIs!

## 🎯 Features

- ✅ **Official APIs** - Uses PWSD's actual smart meter and interval APIs
- ✅ **Real daily data** - Yesterday and today's actual consumption from meter
- ✅ **Monthly tracking** - Current month's total water usage
- ✅ **Energy Dashboard** - Full integration with Home Assistant Energy Dashboard
- ✅ **No calculations** - All data comes directly from PWSD APIs
- ✅ **Configurable polling** - Updates every 3 hours (adjustable)

## 📊 What You Get

### Sensors Created:
- `sensor.pwsd_monthly_water_usage` - Total gallons for current month (for Energy Dashboard)
- `sensor.pwsd_yesterday_water_usage` - Yesterday's actual consumption (from meter)
- `sensor.pwsd_today_water_usage` - Today's consumption so far (from meter)
- `sensor.average_daily_water_usage` - Calculated average (optional)

### Example Values:
```
Monthly Total: 2,145 gallons (November 2025)
Yesterday: 156 gallons (Nov 17, 2025)
Today So Far: 45 gallons (Nov 18, 2025)
Average Daily: 142 gal/day
```

## 🚀 Quick Start

### Prerequisites

- Home Assistant (2023.1 or newer)
- PWSD customer account at https://myaccount.pwsd.org
- Python 3.8+ (included in Home Assistant OS)
- Your account number and meter ID
- Python packages: `requests` and `pyyaml`

### Installation

#### Step 1: Install Required Python Packages

Home Assistant OS requires manual installation of Python dependencies:

```bash
# SSH into your Home Assistant instance, then:
pip3 install --break-system-packages requests pyyaml
```

**Note:** The `--break-system-packages` flag is required for Home Assistant OS. This is safe and necessary for installing packages outside of virtual environments.

**Verify installation:**
```bash
python3 -c "import requests, yaml; print('Packages installed successfully!')"
```

#### Step 2: Download the Script

```bash
wget https://raw.githubusercontent.com/gshepperd/PWSD_HomeAssistant_Integration/main/python_scripts/pwsd_water_scraper.py
mkdir -p /config/python_scripts
mv pwsd_water_scraper.py /config/python_scripts/
chmod +x /config/python_scripts/pwsd_water_scraper.py
```

#### Step 3: Add Credentials

Add to `/config/secrets.yaml`:

```yaml
pwsd_username: "your_email@example.com"
pwsd_password: "your_password"
pwsd_account_number: "1234567"  # From URL when logged in
pwsd_meter_id: "12345678"       # Your meter number
```

**Find your account number:**
- Log into https://myaccount.pwsd.org
- Look at URL: `https://myaccount.pwsd.org/dashboard?account=1234567`
- The number after `account=` is your account number

**Find your meter ID:**
- Go to Customer → Water Smart Meters
- Your meter number is displayed on the page

#### Step 4: Configure Home Assistant

Add to `/config/configuration.yaml`:

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

Add sensors to `/config/command_line.yaml`:
```yaml
command_line: !include command_line.yaml
```
(Copy contents from `config_examples/command_line.yaml`)

Add automations to `/config/automations.yaml`:
(Copy contents from `config_examples/automations.yaml`)

#### Step 5: Test and Restart

```bash
# Test the script
python3 /config/python_scripts/pwsd_water_scraper.py

# Check configuration
Developer Tools → YAML → Check Configuration

# Restart Home Assistant
Settings → System → Restart
```

## ⏱️ Polling Frequency

**Default: Every 3 hours**

The integration polls PWSD APIs every 3 hours by default. This balances data freshness with being respectful to PWSD's servers.

### To Change Polling Frequency:

Edit the automation in `/config/automations.yaml`:

```yaml
trigger:
  - platform: time_pattern
    hours: "/3"  # ← Change this number
```

**Options:**
- `hours: "/1"` = Every 1 hour (⚠️ Not recommended)
- `hours: "/2"` = Every 2 hours
- `hours: "/3"` = Every 3 hours (DEFAULT)
- `hours: "/4"` = Every 4 hours (Matches meter reading)
- `hours: "/6"` = Every 6 hours (Conservative)
- `hours: "/12"` = Every 12 hours (Very conservative)

### ⚠️ Rate Limiting Warning

**Important:** Polling too frequently may trigger rate limiting from PWSD.

**Recommendations:**
- ✅ **Recommended:** 3-4 hours between polls
- ⚠️ **Minimum:** 2 hours (use sparingly)
- ❌ **Avoid:** Every hour or more frequent

**Note:** PWSD meters are read approximately every 3-4 hours, so the default polling frequency is designed to capture updates without excessive API calls.

## 📁 Project Structure

```
PWSD_HomeAssistant_Integration/
├── python_scripts/
│   ├── pwsd_water_scraper.py        # Main scraper (gets all data)
│   └── pwsd_inspector.py            # Debugging tool
├── config_examples/
│   ├── command_line.yaml            # Sensor configuration
│   ├── template.yaml                # Average daily calculation (optional)
│   ├── automations.yaml             # Auto-update automations
│   └── secrets.yaml                 # Credentials template
├── docs/
│   ├── SETUP_GUIDE.md               # Detailed setup instructions
│   ├── API_DOCUMENTATION.md         # API details
│   └── TROUBLESHOOTING.md           # Common issues and solutions
├── README.md                        # This file
├── LICENSE                          # MIT License
└── CHANGELOG.md                     # Version history
```

## 🔧 How It Works

The script makes three API calls to PWSD:

1. **Monthly Total** (Smart Meter API)
   ```
   GET /api/shared/smart-meter-usage-past-2-years?meterNumber=12345678
   ```

2. **Yesterday's Usage** (Interval API)
   ```
   GET /api/shared/interval?account_number=1234567&start_date=2025-11-17T00:00-07:00&end_date=2025-11-17T23:59-07:00&service_category=WATER&period=Daily&meter_id=12345678
   ```

3. **Today's Usage** (Interval API)
   ```
   GET /api/shared/interval?account_number=1234567&start_date=2025-11-18T00:00-07:00&end_date=2025-11-18T23:59-07:00&service_category=WATER&period=Daily&meter_id=12345678
   ```

All data comes directly from PWSD's official APIs - no scraping, no calculations!

## 📊 Home Assistant Energy Dashboard

Add to Energy Dashboard:
1. **Settings** → **Dashboards** → **Energy**
2. Click **"Add Water Source"**
3. Select **`sensor.pwsd_monthly_water_usage`**
4. Save and view your water usage alongside energy!

## 🎨 Dashboard Examples

### Simple Card
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
title: PWSD Water Usage
```

### Gauge Card
```yaml
type: gauge
entity: sensor.pwsd_monthly_water_usage
name: "Monthly Water Usage"
min: 0
max: 20000
needle: true
segments:
  - from: 0
    color: '#0da035'
  - from: 15000
    color: '#e0b400'
  - from: 18000
    color: '#db4437'
```

### History Graph
```yaml
type: history-graph
entities:
  - entity: sensor.pwsd_yesterday_water_usage
    name: Daily Usage
hours_to_show: 168
title: "Last 7 Days Water Usage"
```

## 🧪 Testing

Run the script manually:
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

## 🛠️ Troubleshooting

### Python Package Issues

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip3 install --break-system-packages requests pyyaml
```

### Script fails with "Login failed"
- Verify credentials in `secrets.yaml`
- Test login at https://myaccount.pwsd.org manually

### Sensor shows "unavailable"
- Check if JSON files exist in `/config/`
- Run script manually to test
- Check logs: Settings → System → Logs

### Today's usage shows 0 or unavailable
- Meter readings are updated every 3-4 hours
- Wait for next meter reading cycle
- Yesterday's usage is always more reliable

For more solutions, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📚 Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Detailed installation instructions
- [API Documentation](docs/API_DOCUMENTATION.md) - Technical API details
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## ⚠️ Important Notes

### Meter Reading Timing
- PWSD water meters are read approximately **every 3-4 hours**
- **Today's usage** updates after each meter reading cycle
- **Yesterday's usage** is always complete and reliable
- **Monthly total** updates after each meter reading

### Rate Limiting
- **Respect PWSD's servers** - Don't poll excessively
- **Recommended:** 3-4 hours between polls
- **Minimum:** 2 hours
- Default polling frequency matches meter reading frequency

### Update Schedule
- Script runs **every 3 hours** by default (adjustable)
- Also runs on Home Assistant startup
- Manual update available via button

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## ⚠️ Disclaimer

This is an unofficial integration. Not affiliated with or endorsed by Parker Water & Sanitation District. Use at your own risk.

## 🙏 Acknowledgments

- Parker Water & Sanitation District for providing the customer portal and APIs
- Home Assistant community

## 📧 Support

For issues and questions:
- Open an [Issue](https://github.com/gshepperd/PWSD_HomeAssistant_Integration/issues)
- Check existing documentation in `/docs`

## 🌟 Star This Repo!

If this integration helps you track your water usage, please give it a star! ⭐

---

**Made with 💧 for the Parker, Colorado community**
