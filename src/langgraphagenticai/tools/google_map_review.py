import googlemaps
import dotenv
from typing import Dict, Optional, List
dotenv.load_dotenv()
import os
import json
from pathlib import Path

def process_reviews(place_data: dict) -> dict:
    """
    Process place data to extract simplified review information.
    """
    simplified_data = {
        'restaurant_name': place_data.get('name'),
        'address': place_data.get('formatted_address'),
        'rating': place_data.get('rating'),
        'total_reviews': place_data.get('user_ratings_total'),
        'price_level': place_data.get('price_level'),
        'opening_hours': place_data.get('opening_hours', {}).get('weekday_text', []),
        'phone': place_data.get('formatted_phone_number'),
        'website': place_data.get('website'),
        'reviews': []
    }
    
    for review in place_data.get('reviews', []):
        simplified_review = {
            'author': review.get('author_name'),
            'rating': review.get('rating'),
            'comment': review.get('text'),
            'time': review.get('time'),
            'relative_time': review.get('relative_time_description')
        }
        simplified_data['reviews'].append(simplified_review)
    
    return simplified_data

def get_place_details_by_id(place_id: str) -> Optional[Dict]:
    """
    Get detailed information about a place using its Place ID.
    """
    try:
        api_key = os.getenv("GOOGLE_MAP_API")
        if not api_key:
            raise ValueError("Google Maps API key not found in environment variables")
            
        gmaps = googlemaps.Client(key=api_key)
        
        place = gmaps.place(
            place_id=place_id,
            fields=["name", "formatted_address", "rating", "user_ratings_total", 
                   "price_level", "opening_hours", "formatted_phone_number", 
                   "website", "reviews", "geometry"]
        )
        
        return process_reviews(place["result"])
        
    except Exception as e:
        print(f"Error fetching place details: {str(e)}")
        return None

def search_nearby_places(lat: float, lng: float, radius: int, place_type: str = "restaurant") -> Dict:
    """
    Search for places near a specific location.
    """
    try:
        api_key = os.getenv("GOOGLE_MAP_API")
        if not api_key:
            raise ValueError("Google Maps API key not found in environment variables")
            
        gmaps = googlemaps.Client(key=api_key)
        
        places = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            type=place_type,
            keyword="sushi"
        )
        
        return {
            'results': places.get('results', []),
            'status': places.get('status')
        }
        
    except Exception as e:
        print(f"Error searching nearby places: {str(e)}")
        return {"error": str(e)}

def get_reviews_for_restaurant(restaurant_name: str) -> Optional[Dict]:
    """
    Fetch reviews for a given restaurant name from Google Maps API.
    """
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        sushi_file = project_root / 'data' / 'sushi.json'
        
        if not sushi_file.exists():
            raise FileNotFoundError(f"Could not find sushi.json at {sushi_file}")

        with open(sushi_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        place_id = None
        for item in data:
            if item.get('title') == restaurant_name:
                place_id = item.get('contactInfo', {}).get('place_id')
                break
        
        if not place_id:
            raise ValueError(f"Could not find place_id for restaurant: {restaurant_name}")

        return get_place_details_by_id(place_id)
        
    except Exception as e:
        print(f"Error fetching reviews: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    result = get_reviews_for_restaurant(restaurant_name="Sasou")
    print(json.dumps(result, indent=2, ensure_ascii=False))