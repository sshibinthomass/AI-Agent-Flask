from mcp.server.fastmcp import FastMCP
from src.langgraphagenticai.tools.google_map_review import get_reviews_for_restaurant
from src.langgraphagenticai.tools.weather_info import get_weather_for_restaurant
from src.langgraphagenticai.tools.google_map_review import get_place_details_by_id
import json
import requests
from typing import List, Dict, Optional


mcp=FastMCP("Get restaurant, parking, weather, reviews", port=8000)

@mcp.tool()
def get_reviews(restaurant_name: str) -> dict:
    """
    Get the latest Google reviews for the given restaurant name.
    Args:
        restaurant_name (str): The name of the restaurant
    Returns:
        dict: The reviews for the given restaurant name.
    """
    try:
        result = get_reviews_for_restaurant(restaurant_name)
        if result is None:
            return {"error": f"Could not find reviews for {restaurant_name}"}
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_place_details(place_id: str) -> dict:
    """
    Get detailed information about a place using Google Places API.
    Args:
        place_id (str): The Google Place ID
    Returns:
        dict: Detailed place information including reviews
    """
    try:
        return get_place_details_by_id(place_id)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_nearby_restaurants(lat: float, lng: float, radius: int = 1000) -> dict:
    """
    Search for restaurants near a specific location.
    Args:
        lat (float): Latitude
        lng (float): Longitude
        radius (int): Search radius in meters (default: 1000)
    Returns:
        dict: List of nearby restaurants
    """
    try:
        from src.langgraphagenticai.tools.google_map_review import search_nearby_places
        return search_nearby_places(lat, lng, radius, "restaurant")
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_weather(restaurant_name: str) -> dict:
    """
    Fetch weather or climate for a given restaurant.
    Args:
        restaurant_name (str): The name of the restaurant.
    Returns:
        Optional[Dict]: The weather for the given restaurant.
    """
    try:
        return get_weather_for_restaurant(restaurant_name)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_restaurant_data(restaurant_name: str) -> Optional[Dict]:
    """
    Get detailed information about a specific restaurant.
    Args:
        restaurant_name (str): The name of the restaurant.
    Returns:
        dict: The details about the given restaurant.
    """
    with open("data/sushi.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    matches = [r for r in data if r.get("title") == restaurant_name]
    return matches[0] if matches else None

@mcp.tool()
def get_all_restaurants() -> List[Dict]:
    """
    Get all restaurant data from the database.
    Returns:
        List[Dict]: All restaurant information.
    """
    with open("data/sushi.json", "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def get_restaurant_names() -> List[str]:
    """
    Get all available sushi restaurant names from the database.
    Returns:
        List[str]: The list of available sushi restaurant names.
    """
    with open('data/sushi.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['title'] for item in data if 'title' in item]

@mcp.tool()
def get_parking_data() -> dict:
    """
    Get available parking spaces in Munich.
    Returns:
        dict: The details about the available parking spaces in Munich.
    """
    with open("data/parking.json", "r", encoding="utf-8") as f:
        return json.load(f)

if __name__=="__main__":
    mcp.run(transport="streamable-http")
