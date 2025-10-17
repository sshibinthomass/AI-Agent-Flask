#!/usr/bin/env python3
"""
Start MCP servers for the Flask application
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path


def start_mcp_servers():
    """Start MCP servers in background"""
    print("Starting MCP servers...")

    # Get the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    tools_dir = project_root / "src" / "langgraphagenticai" / "tools"

    # Start restaurant MCP server
    restaurant_script = tools_dir / "mcp_restaurant.py"
    parking_script = tools_dir / "mcp_parking.py"

    processes = []

    try:
        # Start restaurant server
        print(f"Starting restaurant MCP server: {restaurant_script}")
        restaurant_process = subprocess.Popen(
            [sys.executable, str(restaurant_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append(restaurant_process)

        # Start parking server
        print(f"Starting parking MCP server: {parking_script}")
        parking_process = subprocess.Popen(
            [sys.executable, str(parking_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append(parking_process)

        # Wait a bit for servers to start
        print("Waiting for servers to start...")
        time.sleep(5)

        # Check if servers are running
        import requests

        try:
            restaurant_response = requests.get("http://127.0.0.1:8002/mcp", timeout=5)
            print("✅ Restaurant MCP server is running")
        except:
            print("❌ Restaurant MCP server failed to start")

        try:
            parking_response = requests.get("http://127.0.0.1:8003/mcp", timeout=5)
            print("✅ Parking MCP server is running")
        except:
            print("❌ Parking MCP server failed to start")

        print("MCP servers started successfully!")
        print("Press Ctrl+C to stop all servers")

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping MCP servers...")
            for process in processes:
                process.terminate()
            print("MCP servers stopped")

    except Exception as e:
        print(f"Error starting MCP servers: {e}")
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    start_mcp_servers()
