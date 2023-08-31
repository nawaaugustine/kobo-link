# Importing required modules
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import requests
from base64 import b64encode

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
            
            # Create the Basic Authorization header by Base64 encoding the username:password pair
            auth_header = b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')

            # Parse the query parameters from the request URL
            params = parse_qs(urlparse(self.path).query)
            uid = params.get('uid')[0]
            id = params.get('id')[0]
            action = params.get('action')[0]

            # Construct the final URL for the subsequent GET request
            base_url = "https://kobo.unhcr.org"
            url = f"{base_url}/api/v2/assets/{uid}/data/{id}/enketo/{action}/?return_url=false"

            # Make the GET request to the external KoBo API with the Basic Authorization header
            headers = {'Authorization': f'Basic {auth_header}'}
            response = requests.get(url, headers=headers)

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
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"Request to KoBo API failed with status code: {response.status_code}"}).encode())
        except Exception as e:
            # Handle any exceptions that may occur during the request processing
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f"Error in Vercel serverless function: {str(e)}"}).encode())
