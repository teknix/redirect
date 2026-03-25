import requests

BASE_URL = "http://localhost:5005"

def test_smart_stop():
    print("Verifying Smart Stop Logic...")
    
    # We can't easily simulate a 302 chain without a mock server, 
    # but we can test the Amazon URL the user provided if the container has internet access.
    amazon_url = "https://www.amazon.com/gp/buy/thankyou/handlers/display.html?purchaseId=106-9939829-9967466&ref_=chk_typ_browserRefresh&isRefresh=1"
    
    resp = requests.post(f"{BASE_URL}/shorten", json={"url": amazon_url})
    if resp.status_code != 200:
        print(f"FAILED: Shorten request failed with {resp.status_code}")
        return False
        
    data = resp.json()
    # The 'target' (cleaned) should NOT contain 'signin' or 'openid'
    if 'signin' in data['url'].lower() or 'openid' in data['url'].lower():
         print(f"FAILED: 'Smart Stop' failed! Target still contains auth keywords: {data['url']}")
         return False
    
    print(f"SUCCESS: Smart Stop verified for Amazon URL. Cleaned target: {data['url']}")
    return True

if __name__ == "__main__":
    if test_smart_stop():
        print("\nALL SMART STOP TESTS PASSED!")
    else:
        exit(1)
