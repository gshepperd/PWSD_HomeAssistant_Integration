# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-11-18

### Added
- **Interval API integration** - Uses official PWSD interval API for actual daily consumption data
- **Today's usage tracking** - Real-time today's water usage from meter (updates every 3-4 hours)
- **Yesterday's usage tracking** - Actual yesterday's consumption from meter
- Three separate sensors: monthly total, yesterday, and today
- **Python package requirements documentation** - Clear instructions for installing requests and pyyaml
- **Configurable polling frequency** - Default every 3 hours, user-adjustable
- **Rate limiting documentation** - Warnings and recommendations
- Comprehensive API documentation
- Troubleshooting guide with Python package issues

### Changed
- **Breaking:** Now requires `pwsd_account_number` in secrets.yaml
- **Breaking:** Python packages `requests` and `pyyaml` must be manually installed
- **Polling frequency:** Changed to every 3 hours (optimized for meter reading schedule)
- Renamed main script to `pwsd_water_scraper.py` for clarity
- Changed from calculated daily usage to actual API-sourced daily data
- Improved authentication flow
- Updated all documentation with accurate meter reading information (every 3-4 hours)
- Removed all personal identifying information from examples

### Removed
- Template-based daily usage calculations (replaced with API data)
- Personal account numbers and meter IDs from documentation

### Fixed
- No more timing issues with template sensors
- Eliminated dependency on template sensors for daily data
- Accurate meter reading frequency documentation

---

## [1.0.0] - 2025-11-14

### Added
- Initial release
- PWSD Smart Meter API integration for monthly usage
- Monthly water usage tracking
- Template-based daily usage calculation
- Home Assistant Energy Dashboard support
- Automatic updates
- Manual update button
- Complete setup documentation
- Inspector tool for debugging

---

## Migration Guide: v1.0.0 → v2.0.0

### Required Changes

1. **Install Python packages:**
   ```bash
   pip3 install --break-system-packages requests pyyaml
   ```

2. **Add account number to secrets.yaml:**
   ```yaml
   pwsd_account_number: "1234567"  # NEW - required!
   ```

3. **Update automation schedule:**
   - New: Every 3 hours (matches meter reading frequency)

4. **Add new sensors:**
   - `sensor.pwsd_yesterday_water_usage`
   - `sensor.pwsd_today_water_usage`

### Benefits of Upgrading

- ✅ Actual daily usage data (not calculated!)
- ✅ More accurate and reliable
- ✅ Configurable polling frequency
- ✅ Better rate limiting protection
- ✅ Matches PWSD meter reading schedule (every 3-4 hours)
- ✅ Comprehensive documentation
