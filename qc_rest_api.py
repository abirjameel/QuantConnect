import os
from base64 import b64encode
from hashlib import sha256
from time import time
import requests
from dotenv import load_dotenv

# Replace with your actual User ID and API Token
load_dotenv()
USER_ID = os.getenv("QUANTCONNECT_USER_ID")
API_TOKEN = os.getenv("QUANTCONNECT_API_TOKEN")
BASE_URL = "https://www.quantconnect.com/api/v2/"


def get_headers():
    # Get timestamp
    timestamp = f'{int(time())}'
    time_stamped_token = f'{API_TOKEN}:{timestamp}'.encode('utf-8')

    # Get hased API token
    hashed_token = sha256(time_stamped_token).hexdigest()
    authentication = f'{USER_ID}:{hashed_token}'.encode('utf-8')
    authentication = b64encode(authentication).decode('ascii')

    # Create headers dictionary.
    return {
        'Authorization': f'Basic {authentication}',
        'Timestamp': timestamp
    }

# Authenticated state check
try:
    response = requests.post(f"{BASE_URL}authenticate", headers=get_headers())
    response.raise_for_status() # Raise an exception for HTTP errors
    print("Authentication successful:", response.json())
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")


# Read all projects
try:
    response = requests.post(f"{BASE_URL}projects/read", headers=get_headers())
    response.raise_for_status() # Raise an exception for HTTP errors
    print("Authentication successful:", response.json())
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")


# Get a Project's Detail
try:
    payload = {
        "id": 25743424  # ID of the project to read
    }
    response = requests.post(f"{BASE_URL}projects/read", headers=get_headers(), json=payload)
    response.raise_for_status() # Raise an exception for HTTP errors
    print("Authentication successful:", response.json())
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")


# Create a New Test Project

try:
    payload = {
    "name": f"TestProject_{int(time())}",  # Unique project name using current timestamp
    "language": "Py"  # Programming language for the project (Python)
}
    response = requests.post(f"{BASE_URL}/projects/create", headers=get_headers(), json=payload)
    response.raise_for_status() # Raise an exception for HTTP errors
    print("Authentication successful:", response.json())
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")