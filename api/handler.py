# Importing required modules
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

# Define the handler class that inherits from BaseHTTPRequestHandler
class handler(BaseHTTPRequestHandler):
  
    # Handle POST requests
    def do_POST(self):
        try:
            # Retrieve the content length from the HTTP header
            content_length = int(self.headers['Content-Length'])
            # Read the body content of the POST request
            post_data = self.rfile.read(content_length)

            # Parse the JSON payload to get username and password
            user_data = json.loads(post_data)
            username = user_data.get('username')
            password = user_data.get('password')
            
            # Parse the query parameters from the request URL
            params = parse_qs(urlparse(self.path).query)
            uid = params.get('uid')[0]
            id = params.get('id')[0]
            action = params.get('action')[0]

            # Start a session
            session = requests.Session()

            # Get the login page to retrieve CSRF token
            login_url = 'https://kobo.unhcr.org/accounts/login/'
            response = session.get(login_url)

            # Check if the page was retrieved successfully
            if response.status_code != 200:
                raise Exception(f"Failed to load login page. Status code: {response.status_code}")

            # Extract CSRF token
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

            # Prepare payload
            payload = {
                'csrfmiddlewaretoken': csrf_token,
                'login': username,
                'password': password,
                'remember': 'on',
                'next': ''
            }

            # Headers including Referer
            headers = {
                'Referer': login_url,
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            # Perform login
            response = session.post(login_url, data=payload, headers=headers)

            # Check if login was successful by looking for a login error message
            if 'Please enter a correct username and password' in response.text:
                raise Exception("Login failed. Please check your username and password.")

            # Now, proceed to make the API request using the session
            base_url = "https://kobo.unhcr.org"
            api_url = f"{base_url}/api/v2/assets/{uid}/data/{id}/enketo/{action}/?return_url=false"

            # Make the GET request to the KoBo API with the session
            response = session.get(api_url)

            # Check for a successful response (HTTP 200)
            if response.status_code == 200:
                # Parse the JSON response to get the required URL
                json_response = response.json()
                returned_url = json_response.get('url')
                
                # Send the HTTP 200 status and the URL back to the client
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'url': returned_url}).encode())
            else:
                # Handle non-200 status codes by sending an error message
                self.send_response(response.status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"Request to KoBo API failed with status code: {response.status_code}"}).encode())

        except Exception as e:
            # Handle any exceptions that may occur during the request processing
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f"Error in serverless function: {str(e)}"}).encode())
