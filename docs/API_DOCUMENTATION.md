# PWSD API Documentation

Technical documentation for the Parker Water & Sanitation District APIs used by this integration.

## Authentication

### Login Flow

1. **GET /login**
   - Retrieves CSRF tokens and AWS cookies
   - Sets up session for authentication

2. **POST /api/authenticate**
   - Authenticates user credentials
   - Returns `PLAY_SESSION_SESUG` cookie
   - Uses Basic Auth header

**Example:**
```python
# Step 1: Get login page
response = session.get("https://myaccount.pwsd.org/login")

# Step 2: Authenticate
basic_auth = requests.auth._basic_auth_str(username, password)
headers = {
    "Authorization": basic_auth,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}
payload = {
    "j_username": username,
    "j_password": password
}
response = session.post("https://myaccount.pwsd.org/api/authenticate", 
                       data=payload, headers=headers)
```

## API Endpoints

### 1. Smart Meter Usage (Past 2 Years)

**Endpoint:** `/api/shared/smart-meter-usage-past-2-years`

**Method:** GET

**Purpose:** Retrieves monthly water consumption data for the past 24 months

**Parameters:**
- `meterNumber` (required): Your water meter ID
- `_` (optional): Timestamp for cache busting

**Full URL:**
```
https://myaccount.pwsd.org/api/shared/smart-meter-usage-past-2-years?meterNumber=12345678&_=1731952800000
```

**Response Structure:**
```json
{
  "12345678": {
    "data": [
      {
        "consumption": 1982,
        "reading": 1398021,
        "date": "2025-11-01T00:00:00-06:00"
      },
      {
        "consumption": 1856,
        "reading": 1396039,
        "date": "2025-10-01T00:00:00-06:00"
      }
    ]
  }
}
```

---

### 2. Interval Data (Daily Usage)

**Endpoint:** `/api/shared/interval`

**Method:** GET

**Purpose:** Retrieves actual daily water consumption for specific date ranges

**Parameters:**
- `account_number` (required): Your PWSD account number
- `start_date` (required): Start date/time (ISO 8601 with timezone)
- `end_date` (required): End date/time (ISO 8601 with timezone)
- `service_category` (required): "WATER"
- `graphs` (required): URL-encoded empty array `%5B%5D`
- `format` (required): "json"
- `meter_id` (required): Your water meter ID
- `period` (required): "Daily"
- `_` (optional): Timestamp for cache busting

**Full URL (Yesterday's Usage):**
```
https://myaccount.pwsd.org/api/shared/interval?account_number=1234567&start_date=2025-11-17T00:00-07:00&end_date=2025-11-17T23:59-07:00&service_category=WATER&graphs=%5B%5D&format=json&meter_id=12345678&period=Daily&_=1731952800000
```

**Response Structure:**
```json
[
  {
    "graphType": "column",
    "seriesGroup": "Water",
    "measurementType": "Consumption",
    "measurementUnit": "gal",
    "dataPoints": [
      {
        "date": "2025-11-17T00:00:00-07:00",
        "value": 156,
        "measurementUnit": "gal",
        "meterNumber": "12345678"
      }
    ]
  }
]
```

---

## Rate Limiting

**Recommended Practice:**
- Run script **every 3-4 hours** (default: 3 hours)
- Use cache-busting timestamps
- Don't make rapid repeated requests
- Respect PWSD's infrastructure

**Current Implementation:**
- Runs every 3 hours by default
- Also runs on Home Assistant startup
- Manual refresh available

**⚠️ Warning:**
- Polling every hour or more frequently may trigger rate limiting
- PWSD meters are read approximately every 3-4 hours
- Polling frequency should match meter reading frequency
- PWSD may block excessive requests from your IP

---

## Data Freshness

### Monthly Data
- Updates after each meter reading (every 3-4 hours)
- Reflects cumulative usage for current month

### Daily Data (Interval API)
- **Yesterday:** Always complete and accurate
- **Today:** Updates every 3-4 hours as meter is read
- Meter readings occur approximately every 3-4 hours

---

## Authentication Headers

### Required Headers
```python
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Origin": "https://myaccount.pwsd.org",
    "Referer": "https://myaccount.pwsd.org/login",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Authorization": "Basic <base64_credentials>"
}
```

### Session Cookie
```
PLAY_SESSION_SESUG=<session_token>
```

Must be included in all authenticated requests.

---

## Security Considerations

- ✅ Use HTTPS for all requests
- ✅ Store credentials in secrets.yaml (never in code)
- ✅ Don't share session cookies
- ✅ Implement proper error handling
- ✅ Use authenticated sessions

---

## API Changes

PWSD may update their APIs without notice. If this integration stops working:

1. Check PWSD portal for changes
2. Use browser dev tools to inspect new API calls
3. Update integration accordingly
4. Submit PR to this repository

Last verified: November 2025
