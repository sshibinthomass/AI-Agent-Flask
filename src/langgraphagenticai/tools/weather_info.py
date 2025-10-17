import googlemaps
import dotenv
from typing import Dict, Optional, List
dotenv.load_dotenv()
import os
import json
from pathlib import Path
import requests

def get_weather_for_restaurant(restaurant_name: str) -> Optional[Dict]:
    """
    Fetch weather or climate for a given restaurant.
    Args:
        restaurant_name (str): The name of the restaurant.
    Returns:
        Optional[Dict]: The weather for the given restaurant.
    """
    try:
        with open("data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        position = None
        for item in data:
            if item.get('title') == restaurant_name:
                position = item.get('position', {})
                break
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": float(position.get('lat')),
            "longitude": float(position.get('lng')),
            "current_weather": True,
        }
        
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()["current_weather"]
        
    except Exception as e:
        print(f"Error fetching Weather: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    result = get_weather_for_restaurant(restaurant_name="Sasou")
    print(result)