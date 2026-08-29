import requests

def get_random_advice():
    try:
        res = requests.get("https://api.adviceslip.com/advice").json()
        return res['slip']['advice']
    except Exception as e:
        print(f"Error fetching advice: {e}")
        return "Always do your best."
