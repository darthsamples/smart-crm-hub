# Import required modules
import requests # Used for making HTTP requests to APIs
from typing import Any, Dict  # Used for type hinting

# Import configuration settings (the base URL for your API, Claude key, Etc.)
from agent.config import AgentSettings

# Define a function to make an API request using a given method, endpoint, and optional data
def api_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    # Construct the full URL for the API call
    url = f"{AgentSettings.FASTAPI_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    try:
        # Choose the request method dynamically
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        else:
            # Raise an error if the method is not supported
            raise ValueError(f"Unsupported method: {method}")
        
        # Raise an error if the method is not supported
        response.raise_for_status()

         # Return the JSON response as a Python dictionary
        return response.json()
    except requests.RequestException as e:
        # Print an error message if the request fails and return an empty dictionary
        print(f"API request failed: {e}")
        return {}

# Define a function to extract RFM (Recency, Frequency, Monetary) values from a text response
def parse_rfm_response(claude_response: str) -> Dict[str, float]:
    # Simplified parsing of Claude's response, initialize the RFM dictionary with default float values
    rfm = {"recency": 0.0, "frequency": 0.0, "monetary": 0.0}

    # Loop through each RFM key and extract its value from the response
    for key in rfm.keys():
        if key in claude_response.lower():
            # Extract the number that follows the RFM keyword in the text
            rfm[key] = float(claude_response.split(key)[1].split()[0])
    return rfm # Return the populated RFM dictionary