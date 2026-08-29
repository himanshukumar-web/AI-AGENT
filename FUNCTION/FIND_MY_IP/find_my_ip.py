import requests

def find_my_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json')
        if response.status_code == 200:
            ip_address = response.json()
            return ip_address["ip"]
        else:
            return "Unable to get IP"
    except Exception as e:
        print(f"Error finding IP: {e}")
        return "Error finding IP"
