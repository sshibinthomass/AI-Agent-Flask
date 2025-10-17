import json
import sys
import requests
from pathlib import Path
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP


current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.langgraphagenticai.tools.google_map_review import search_nearby_places
from src.langgraphagenticai.tools.google_map_review import get_place_details_by_id
from src.langgraphagenticai.tools.google_map_review import get_reviews_for_restaurant

mcp=FastMCP("Sushi restaurant", port=8002)

@mcp.tool()
def get_googlereviews(restaurant_name: str) -> dict:
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
        
        return search_nearby_places(lat, lng, radius, "restaurant")
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
    with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
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
    with open(project_root /"data/sushi.json", "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def get_restaurant_names() -> List[str]:
    """
    Get all available sushi restaurant names from the database.
    Returns:
        List[str]: The list of available sushi restaurant names.
    """
    with open(project_root /"data/sushi.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['title'] for item in data if 'title' in item]

@mcp.tool()
def get_restaurant_menu(restaurant_name: str) -> Dict:
    """
    Get the menu items and prices for a specific restaurant.
    Args:
        restaurant_name (str): The name of the restaurant
    Returns:
        dict: Menu items with prices
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for restaurant in data:
            if restaurant.get("title") == restaurant_name:
                menu = restaurant.get("menu", {})
                return {
                    "restaurant": restaurant_name,
                    "menu_items": menu.get("items", []),
                    "total_items": len(menu.get("items", []))
                }
        return {"error": f"Restaurant '{restaurant_name}' not found"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_restaurants_by_price_range(min_price: float, max_price: float) -> List[Dict]:
    """
    Find restaurants with menu items within a specific price range.
    Args:
        min_price (float): Minimum price
        max_price (float): Maximum price
    Returns:
        List[Dict]: Restaurants with items in the price range
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        results = []
        for restaurant in data:
            menu_items = restaurant.get("menu", {}).get("items", [])
            affordable_items = [
                item for item in menu_items 
                if min_price <= item.get("price", 0) <= max_price
            ]
            
            if affordable_items:
                results.append({
                    "restaurant": restaurant.get("title"),
                    "address": restaurant.get("address"),
                    "affordable_items": affordable_items,
                    "item_count": len(affordable_items)
                })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_restaurant_contact_info(restaurant_name: str) -> Dict:
    """
    Get contact information for a specific restaurant.
    Args:
        restaurant_name (str): The name of the restaurant
    Returns:
        dict: Contact information including phone, email, website
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for restaurant in data:
            if restaurant.get("title") == restaurant_name:
                contact_info = restaurant.get("contactInfo", {})
                return {
                    "restaurant": restaurant_name,
                    "phone": contact_info.get("phoneNumber"),
                    "email": contact_info.get("email"),
                    "website": contact_info.get("website"),
                    "address": restaurant.get("address")
                }
        return {"error": f"Restaurant '{restaurant_name}' not found"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_restaurants_by_food_type(food_type: str) -> List[Dict]:
    """
    Find restaurants that serve a specific type of food.
    Args:
        food_type (str): Type of food (e.g., "Japanese", "Asian", "Sushi")
    Returns:
        List[Dict]: Restaurants serving the specified food type
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        results = []
        food_type_lower = food_type.lower()
        
        for restaurant in data:
            food_types = restaurant.get("foodTypes", [])
            if any(food_type_lower in ft.lower() for ft in food_types):
                results.append({
                    "restaurant": restaurant.get("title"),
                    "address": restaurant.get("address"),
                    "food_types": food_types,
                    "price_level": restaurant.get("priceSummary", {}).get("priceRangeLevel", "Unknown")
                })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]


if __name__=="__main__":
    mcp.run(transport="streamable-http")
