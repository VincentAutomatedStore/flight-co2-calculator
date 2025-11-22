# test_icao_api.py
import requests
import json

def test_icao_api():
    url = "https://icec.icao.int/Home/PassengerCompute"
    
    payload = {
        "AirportCodeDeparture": "AES",
        "AirportCodeDestination": ["GDN"],
        "CabinClass": "",
        "Departure": "AES Airport",
        "Destination": ["GDN Airport"],
        "IsRoundTrip": True,
        "NumberOfPassenger": 1
    }
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://icec.icao.int",
        "Referer": "https://icec.icao.int/calculator",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }
    
    try:
        print("Sending request to ICAO API...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! ICAO API Response:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response Text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return None

if __name__ == "__main__":
    test_icao_api()