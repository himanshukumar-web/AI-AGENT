import requests

def get_random_joke():
    try:
        headers = {
            'Accept': 'application/json'
        }
        res = requests.get("https://icanhazdadjoke.com/", headers=headers).json()
        return res["joke"]
    except Exception as e:
        print(f"Error fetching joke: {e}")
        return "Why did the chicken cross the road? To get to the other side."
