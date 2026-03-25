import requests
import json
import time

BASE_URL = "http://localhost:5000" 

def test_privacy_features():
    print("Testing Privacy Hardening...")
    
    # 1. Test Expanded Tracking Parameter Stripping
    # _ga, msclkid, _ke are new tracking params
    target_url = "https://example.com/path?utm_source=test&_ga=123&msclkid=456&_ke=789&keep=this"
    print(f"Shortening with tracking: {target_url}")
    
    resp = requests.post(f"{BASE_URL}/shorten", json={"url": target_url})
    if resp.status_code != 200:
        print(f"FAILED: Status {resp.status_code}")
        return False
        
    data = resp.json()
    short_code = data['short_code']
    
    # Check redirect location
    redirect_resp = requests.get(f"{BASE_URL}/{short_code}", allow_redirects=False)
    location = redirect_resp.headers.get("Location")
    print(f"Redirect Location: {location}")
    
    for param in ["utm_source", "_ga", "msclkid", "_ke"]:
        if param in location:
            print(f"FAILED: Tracking param '{param}' leaked!")
            return False
            
    if "keep=this" not in location:
        print("FAILED: Legitimate param 'keep' was lost!")
        return False

    # 2. Test Deep Privacy Mode (No resolution)
    print("\nTesting Deep Privacy Mode...")
    # example.com/resolved should NOT be hit if we use a fake URL that redirects
    # We'll just verify the metadata is set to the 'Private' placeholder
    private_target = "https://example.com/private-test"
    resp = requests.post(f"{BASE_URL}/shorten", json={"url": private_target, "private_mode": True})
    data = resp.json()
    short_code = data['short_code']
    
    # Check bot preview for this code
    bot_resp = requests.get(f"{BASE_URL}/{short_code}", headers={"User-Agent": "Slackbot 1.0"})
    if "Private Link" not in bot_resp.text:
        print("FAILED: Private mode metadata not found in bot response!")
        return False
    if "resolution was skipped" not in bot_resp.text:
        print("FAILED: Private mode description not found!")
        return False
        
    print("SUCCESS: Deep Privacy Mode verified!")

    # 3. Test Bot Referrer Policy
    print("\nTesting Bot Referrer Policy...")
    if '<meta name="referrer" content="no-referrer">' not in bot_resp.text:
        print("FAILED: Bot response missing no-referrer meta tag!")
        return False
    print("SUCCESS: Bot Referrer Policy verified!")

    return True

if __name__ == "__main__":
    time.sleep(1) # Wait for potential server settling
    try:
        if test_privacy_features():
            print("\nALL PRIVACY TESTS PASSED!")
        else:
            exit(1)
    except Exception as e:
        print(f"Error during verification: {e}")
        exit(1)
