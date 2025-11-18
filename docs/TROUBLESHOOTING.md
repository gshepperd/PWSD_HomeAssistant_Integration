# Troubleshooting Guide

Common issues and solutions for the PWSD Home Assistant Integration.

## Python Package Issues

### ModuleNotFoundError: No module named 'requests'

**Solution:**
```bash
pip3 install --break-system-packages requests pyyaml
```

**Verify installation:**
```bash
python3 -c "import requests, yaml; print('Packages installed!')"
```

### ModuleNotFoundError: No module named 'yaml'

**Solution:**
```bash
pip3 install --break-system-packages pyyaml
```

### pip3: command not found

**Solution:** Use Home Assistant's Python directly:
```bash
/usr/local/bin/python3 -m pip install --break-system-packages requests pyyaml
```

### Permission denied when installing packages

**Solution:**
```bash
sudo pip3 install --break-system-packages requests pyyaml
```

---

## Installation Issues

### Script not found
**Error:** `can't open file '/config/python_scripts/pwsd_water_scraper.py'`

**Solution:**
1. Verify file exists: `ls -la /config/python_scripts/pwsd_water_scraper.py`
2. Check filename is correct
3. Re-download if missing

### Permission denied
**Error:** `Permission denied`

**Solution:**
```bash
chmod +x /config/python_scripts/pwsd_water_scraper.py
```

---

## Authentication Issues

### Login failed
**Error:** `❌ LOGIN FAILED: Status 401`

**Solutions:**
1. Verify credentials in secrets.yaml
2. Test login at https://myaccount.pwsd.org manually
3. Check for special characters (use quotes):
   ```yaml
   pwsd_password: "P@ssw0rd!"  # Use quotes!
   ```
4. Check for extra spaces

---

## Configuration Issues

### Missing configuration values
**Error:** `Missing configuration values in secrets.yaml`

**Solution:** Make sure secrets.yaml has all 4 values:
```yaml
pwsd_username: "your_email@example.com"
pwsd_password: "your_password"
pwsd_account_number: "1234567"
pwsd_meter_id: "12345678"
```

---

## Sensor Issues

### Sensors show "unavailable"

**Solutions:**

1. Run script manually:
   ```bash
   python3 /config/python_scripts/pwsd_water_scraper.py
   ```

2. Check JSON files exist:
   ```bash
   ls -la /config/pwsd_*.json
   ```

3. Restart Home Assistant

### Today's usage shows 0

**This is normal!**
- Meters are read every 3-4 hours
- Today's usage updates after each reading cycle
- Wait 3-4 hours for next meter reading
- Yesterday's usage is always reliable

---

## Rate Limiting Issues

### Getting rate limited by PWSD

**Symptoms:**
- 429 errors
- Repeated failed API calls
- Blocked requests

**Solutions:**
1. Increase polling interval to 4+ hours
2. Wait 24 hours before trying again
3. Don't use manual update button excessively

**Edit automation:**
```yaml
trigger:
  - platform: time_pattern
    hours: "/4"  # Change from /3 to /4 or higher
```

---

## Automation Issues

### Automation not running

**Check:**
1. Settings → Automations & Scenes
2. Find "Update PWSD Water Usage"
3. Make sure it's enabled

**Test manually:**
- Developer Tools → Actions
- Select `shell_command.update_pwsd_water`
- Click "Perform Action"

---

## Debugging

### Enable debug logging
Add to configuration.yaml:
```yaml
logger:
  default: info
  logs:
    homeassistant.components.command_line: debug
```

### Check script output
```bash
python3 /config/python_scripts/pwsd_water_scraper.py 2>&1 | tee /tmp/pwsd_debug.log
```

### Check Home Assistant logs
Settings → System → Logs

Filter for: "pwsd", "command_line", "shell_command"

---

## Getting Help

Still having issues?

1. Check existing issues on GitHub
2. Open new issue with:
   - Home Assistant version
   - Error messages
   - What you've tried
3. DO NOT share passwords or credentials!
