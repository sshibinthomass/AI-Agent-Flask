import json
import sys
from pathlib import Path
import requests
from mcp.server.fastmcp import FastMCP

# Fix import paths for MCP server
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))

mcp = FastMCP("Weather information for restaurants", port=8004)


@mcp.tool()
def get_weather_for_restaurant(restaurant_name: str) -> dict:
    """
    Fetch weather or climate for a given restaurant.
    Args:
        restaurant_name (str): The name of the restaurant.
    Returns:
        dict: The weather for the given restaurant including temperature, weather code, and description.
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        position = None
        for item in data:
            if item.get("title") == restaurant_name:
                position = item.get("position", {})
                break

        if not position:
            return {"error": f"Restaurant '{restaurant_name}' not found in database"}

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": float(position.get("lat")),
            "longitude": float(position.get("lng")),
            "current_weather": True,
        }

        resp = requests.get(url, params=params)
        resp.raise_for_status()
        weather_data = resp.json()["current_weather"]

        return {
            "restaurant": restaurant_name,
            "location": {
                "latitude": position.get("lat"),
                "longitude": position.get("lng"),
            },
            "weather": weather_data,
            "temperature": weather_data.get("temperature"),
            "weather_code": weather_data.get("weathercode"),
            "windspeed": weather_data.get("windspeed"),
            "winddirection": weather_data.get("winddirection"),
        }

    except Exception as e:
        return {"error": f"Error fetching weather: {str(e)}"}


@mcp.tool()
def get_weather_by_coordinates(latitude: float, longitude: float) -> dict:
    """
    Get weather information for specific coordinates.
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
    Returns:
        dict: Current weather information for the coordinates
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
        }

        resp = requests.get(url, params=params)
        resp.raise_for_status()
        weather_data = resp.json()["current_weather"]

        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "weather": weather_data,
            "temperature": weather_data.get("temperature"),
            "weather_code": weather_data.get("weathercode"),
            "windspeed": weather_data.get("windspeed"),
            "winddirection": weather_data.get("winddirection"),
        }

    except Exception as e:
        return {"error": f"Error fetching weather: {str(e)}"}


@mcp.tool()
def get_weather_for_all_restaurants() -> dict:
    """
    Get weather information for all restaurants in the database.
    Returns:
        dict: Weather information for all restaurants
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        weather_results = []

        for restaurant in data:
            restaurant_name = restaurant.get("title")
            position = restaurant.get("position", {})

            if not position:
                continue

            try:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": float(position.get("lat")),
                    "longitude": float(position.get("lng")),
                    "current_weather": True,
                }

                resp = requests.get(url, params=params)
                resp.raise_for_status()
                weather_data = resp.json()["current_weather"]

                weather_results.append(
                    {
                        "restaurant": restaurant_name,
                        "location": {
                            "latitude": position.get("lat"),
                            "longitude": position.get("lng"),
                        },
                        "temperature": weather_data.get("temperature"),
                        "weather_code": weather_data.get("weathercode"),
                        "windspeed": weather_data.get("windspeed"),
                    }
                )

            except Exception as e:
                weather_results.append(
                    {
                        "restaurant": restaurant_name,
                        "error": f"Failed to fetch weather: {str(e)}",
                    }
                )

        return {"total_restaurants": len(data), "weather_data": weather_results}

    except Exception as e:
        return {"error": f"Error processing restaurants: {str(e)}"}


@mcp.tool()
def get_weather_summary() -> dict:
    """
    Get a summary of weather conditions across all restaurant locations.
    Returns:
        dict: Weather summary including average temperature and conditions
    """
    try:
        with open(project_root / "data/sushi.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        temperatures = []
        weather_codes = []
        successful_fetches = 0

        for restaurant in data:
            position = restaurant.get("position", {})
            if not position:
                continue

            try:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": float(position.get("lat")),
                    "longitude": float(position.get("lng")),
                    "current_weather": True,
                }

                resp = requests.get(url, params=params)
                resp.raise_for_status()
                weather_data = resp.json()["current_weather"]

                temperatures.append(weather_data.get("temperature"))
                weather_codes.append(weather_data.get("weathercode"))
                successful_fetches += 1

            except Exception:
                continue

        if successful_fetches == 0:
            return {"error": "No weather data could be fetched"}

        avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0
        most_common_weather = (
            max(set(weather_codes), key=weather_codes.count) if weather_codes else None
        )

        return {
            "summary": {
                "total_locations": len(data),
                "successful_fetches": successful_fetches,
                "average_temperature": round(avg_temp, 1),
                "most_common_weather_code": most_common_weather,
                "temperature_range": {
                    "min": min(temperatures) if temperatures else None,
                    "max": max(temperatures) if temperatures else None,
                },
            }
        }

    except Exception as e:
        return {"error": f"Error generating weather summary: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
