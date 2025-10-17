import json
import sys
import requests
from pathlib import Path
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
import time
from functools import wraps

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
sys.path.append(str(project_root))


mcp=FastMCP("Parking near restaurant", port=8003)

@mcp.tool()
def get_parking_data() -> dict:
    """
    Get available parking spaces in Munich.
    Returns:
        dict: The details about the available parking spaces in Munich.
    """
    with open(project_root / "data/parking.json", "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def get_open_parking_lots() -> List[Dict]:
    """
    Get all parking lots that are currently open.
    Returns:
        List[Dict]: Currently open parking lots with details
    """
    try:
        with open(project_root / "data/parking.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        open_lots = []
        for lot in data:
            business_hours = lot.get("businessHours", {})
            if business_hours.get("currentStatus") == "OPEN":
                open_lots.append({
                    "title": lot.get("title"),
                    "address": lot.get("address"),
                    "distance": lot.get("distance_from_current_location"),
                    "duration": lot.get("duration_from_current_location"),
                    "price_summary": lot.get("priceSummary", {}).get("priceSummaryText"),
                    "free_spots": lot.get("parking", {}).get("freeSpotsNumber"),
                    "total_spots": lot.get("parking", {}).get("spotsNumber"),
                    "next_status_change": business_hours.get("nextStatusChange")
                })
        
        return open_lots
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_parking_with_free_spots() -> List[Dict]:
    """
    Get parking lots that currently have free spots available.
    Returns:
        List[Dict]: Parking lots with available spots
    """
    try:
        with open(project_root / "data/parking.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        available_lots = []
        for lot in data:
            parking_info = lot.get("parking", {})
            free_spots = parking_info.get("freeSpotsNumber")
            
            if free_spots and free_spots > 0:
                available_lots.append({
                    "title": lot.get("title"),
                    "address": lot.get("address"),
                    "free_spots": free_spots,
                    "total_spots": parking_info.get("spotsNumber"),
                    "availability_percentage": round((free_spots / parking_info.get("spotsNumber", 1)) * 100, 1),
                    "distance": lot.get("distance_from_current_location"),
                    "price_summary": lot.get("priceSummary", {}).get("priceSummaryText")
                })
        
        return sorted(available_lots, key=lambda x: x["free_spots"], reverse=True)
    except Exception as e:
        return [{"error": str(e)}]
    

@mcp.tool()
def get_24_hour_parking() -> List[Dict]:
    """
    Get parking lots that are open 24 hours.
    Returns:
        List[Dict]: 24-hour parking lots
    """
    try:
        with open(project_root / "data/parking.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        all_day_lots = []
        for lot in data:
            business_hours = lot.get("businessHours", {})
            formatted_hours = business_hours.get("formattedHours", [])
            
            if any("24 hours" in hour for hour in formatted_hours):
                all_day_lots.append({
                    "title": lot.get("title"),
                    "address": lot.get("address"),
                    "distance": lot.get("distance_from_current_location"),
                    "price_summary": lot.get("priceSummary", {}).get("priceSummaryText"),
                    "free_spots": lot.get("parking", {}).get("freeSpotsNumber"),
                    "payment_methods": lot.get("paymentMethods", [])
                })
        
        return all_day_lots
    except Exception as e:
        return [{"error": str(e)}]
    
@mcp.tool()
def get_parking_with_disabled_access() -> List[Dict]:
    """
    Get parking lots with disabled parking spots.
    Returns:
        List[Dict]: Parking lots with disabled access
    """
    try:
        with open(project_root / "data/parking.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        disabled_lots = []
        for lot in data:
            parking_info = lot.get("parking", {})
            services = parking_info.get("services", [])
            
            if "DISABLED" in services:
                disabled_lots.append({
                    "title": lot.get("title"),
                    "address": lot.get("address"),
                    "disabled_spots": parking_info.get("disabledSpotsNumber"),
                    "total_spots": parking_info.get("spotsNumber"),
                    "distance": lot.get("distance_from_current_location"),
                    "price_summary": lot.get("priceSummary", {}).get("priceSummaryText")
                })
        
        return disabled_lots
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_parking_payment_methods() -> Dict:
    """
    Get all available payment methods across parking lots.
    Returns:
        Dict: Payment methods and which lots accept them
    """
    try:
        with open(project_root / "data/parking.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        payment_methods = {}
        for lot in data:
            methods = lot.get("paymentMethods", [])
            for method in methods:
                if method not in payment_methods:
                    payment_methods[method] = []
                payment_methods[method].append({
                    "title": lot.get("title"),
                    "address": lot.get("address"),
                    "distance": lot.get("distance_from_current_location")
                })
        
        return payment_methods
    except Exception as e:
        return {"error": str(e)}


if __name__=="__main__":
    mcp.run(transport="streamable-http")