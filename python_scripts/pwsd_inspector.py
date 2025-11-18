#!/usr/bin/env python3
"""
PWSD Portal Inspector
Debug tool to help you understand the myaccount.pwsd.org portal structure
and find where your water usage data is located.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import yaml
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration"""
    secrets_path = '/config/secrets.yaml'
    
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, 'r') as f:
                secrets = yaml.safe_load(f)
                return {
                    'username': secrets.get('pwsd_username') or secrets.get('sprypoint_username'),
                    'password': secrets.get('pwsd_password') or secrets.get('sprypoint_password')
                }
        except Exception as e:
            logger.error(f"Error loading secrets: {str(e)}")
    
    return {
        'username': os.getenv('PWSD_USERNAME'),
        'password': os.getenv('PWSD_PASSWORD')
    }


def inspect_pwsd_portal():
    """Inspect the PWSD portal and save debug information"""
    
    config = load_config()
    username = config.get('username')
    password = config.get('password')
    
    if not username or not password:
        logger.error("Missing credentials! Please configure secrets.yaml")
        return
    
    base_url = "https://myaccount.pwsd.org"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    logger.info("=" * 80)
    logger.info("PWSD PORTAL INSPECTOR")
    logger.info("=" * 80)
    logger.info(f"Portal: {base_url}")
    logger.info(f"Username: {username}")
    logger.info("")
    
    try:
        # Step 1: Get login page
        logger.info("STEP 1: Fetching login page...")
        login_url = f"{base_url}/login"
        
        response = session.get(login_url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save login page
        with open('/config/debug_pwsd_login.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("✓ Login page saved to: /config/debug_pwsd_login.html")
        
        # Analyze login form
        form = soup.find('form')
        if form:
            logger.info("\nLogin form details:")
            logger.info(f"  Action: {form.get('action', 'N/A')}")
            logger.info(f"  Method: {form.get('method', 'POST')}")
            logger.info("\n  Form fields:")
            for inp in form.find_all('input'):
                logger.info(f"    - {inp.get('name', 'unnamed')}: {inp.get('type', 'text')}")
        
        # Step 2: Login
        logger.info("\nSTEP 2: Attempting login...")
        
        login_data = {
            'username': username,
            'password': password
        }
        
        # Get hidden fields
        if form:
            for hidden in form.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    login_data[name] = value
        
        login_response = session.post(login_url, data=login_data, allow_redirects=True, timeout=30)
        
        logger.info(f"  Response status: {login_response.status_code}")
        logger.info(f"  Final URL: {login_response.url}")
        
        # Save post-login page
        with open('/config/debug_pwsd_after_login.html', 'w', encoding='utf-8') as f:
            f.write(login_response.text)
        logger.info("✓ Post-login page saved to: /config/debug_pwsd_after_login.html")
        
        # Check if login was successful
        if 'logout' in login_response.text.lower() or 'sign out' in login_response.text.lower():
            logger.info("✓ Login appears successful!")
        else:
            logger.warning("⚠ Login status unclear - check saved HTML files")
        
        # Step 3: Explore pages
        logger.info("\nSTEP 3: Exploring portal pages...")
        
        pages_to_check = [
            ('/customer/water-smart-meters', 'water_smart_meters'),  # Main usage page
            ('/', 'home'),
            ('/dashboard', 'dashboard'),
            ('/account', 'account'),
            ('/usage', 'usage'),
            ('/consumption', 'consumption'),
            ('/myaccount', 'myaccount'),
        ]
        
        found_pages = []
        
        for path, name in pages_to_check:
            try:
                url = f"{base_url}{path}"
                resp = session.get(url, timeout=20)
                
                if resp.status_code == 200:
                    logger.info(f"✓ Found: {url}")
                    found_pages.append((path, name, url))
                    
                    # Save the page
                    filename = f"/config/debug_pwsd_{name}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(resp.text)
                    logger.info(f"  Saved to: {filename}")
                    
                    # Look for usage-related content
                    if any(kw in resp.text.lower() for kw in ['usage', 'gallon', 'water', 'consumption']):
                        logger.info(f"  → Contains water usage keywords!")
                        
                        # Try to find specific values
                        import re
                        pattern = r'(\d+\.?\d*)\s*(gallon|gal|ccf)'
                        matches = re.findall(pattern, resp.text.lower())
                        if matches:
                            logger.info(f"  → Potential usage values found: {matches[:5]}")  # Show first 5
                
            except Exception as e:
                logger.debug(f"Could not access {path}: {str(e)}")
                continue
        
        # Step 4: Check for API endpoints
        logger.info("\nSTEP 4: Checking for API endpoints...")
        
        api_endpoints = [
            # V1 API endpoints (PRIORITY)
            '/api/v1/customer/water-smart-meters',
            '/api/v1/smart-meters/usage',
            '/api/v1/smart-meters/monthly',
            '/api/v1/meters/usage',
            '/api/v1/usage',
            '/api/v1/usage/monthly',
            '/api/v1/usage/current',
            '/api/v1/consumption',
            '/api/v1/consumption/monthly',
            '/api/v1/account/usage',
            '/api/v1/account',
            '/api/v1/dashboard',
            '/api/v1/billing/current',
            '/api/v1/billing',
            
            # Non-versioned API endpoints
            '/api/customer/water-smart-meters',
            '/api/smart-meters/usage',
            '/api/smart-meters/monthly',
            '/api/meters/usage',
            '/api/usage',
            '/api/usage/monthly',
            '/api/usage/current',
            '/api/account/usage',
            '/api/consumption',
            '/api/consumption/monthly',
            '/api/dashboard',
            '/api/billing/current',
        ]
        
        api_found = False
        
        for endpoint in api_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                resp = session.get(url, timeout=10)
                
                if resp.status_code == 200:
                    content_type = resp.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        logger.info(f"✓ API endpoint found: {url}")
                        api_found = True
                        
                        try:
                            data = resp.json()
                            filename = f"/config/debug_pwsd_api_{endpoint.replace('/', '_')}.json"
                            with open(filename, 'w') as f:
                                json.dump(data, f, indent=2)
                            logger.info(f"  Saved JSON to: {filename}")
                            logger.info(f"  JSON keys: {list(data.keys()) if isinstance(data, dict) else f'{len(data)} items'}")
                        except:
                            pass
                    else:
                        logger.debug(f"{url} returned {content_type}")
                
            except:
                pass
        
        if not api_found:
            logger.info("No JSON API endpoints found (this is normal, will use HTML scraping)")
        
        # Step 5: Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info("\nDebug files created in /config/:")
        logger.info("  - debug_pwsd_login.html")
        logger.info("  - debug_pwsd_after_login.html")
        
        for _, name, _ in found_pages:
            logger.info(f"  - debug_pwsd_{name}.html")
        
        logger.info("\nNext steps:")
        logger.info("  1. Review the HTML files to find your water usage")
        logger.info("  2. Look for the specific HTML element containing the value")
        logger.info("  3. Note the class name, ID, or structure")
        logger.info("  4. Update pwsd_water_scraper.py if needed")
        logger.info("\nSearch for your usage:")
        logger.info("  grep -i 'gallon' /config/debug_pwsd_*.html")
        logger.info("  grep -i 'usage' /config/debug_pwsd_*.html")
        
        logger.info("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"Error during inspection: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    inspect_pwsd_portal()
