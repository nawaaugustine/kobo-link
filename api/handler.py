from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import requests
from base64 import b64encode

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Parse the username and password from the request body
            user_data = json.loads(post_data)
            username = user_data.get('username')
            password = user_data.get('password')

            # Create the authentication header
            auth_header = b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')

            # Parse parameters from URL
            params = parse_qs(urlparse(self.path).query)
            uid = params.get('uid')[0]
            id = params.get('id')[0]
            action = params.get('action')[0]

            # Construct the URL for the GET request
            base_url = "https://kobo.unhcr.org"
            url = f"{base_url}/api/v2/assets/{uid}/data/{id}/enketo/{action}/?return_url=false"

            # Make a GET request with the Basic Authentication header
            headers = {'Authorization': f'Basic {auth_header}'}
            response = requests.get(url, headers=headers)

            # Ensure the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                json_response = response.json()

                # Extract the URL
                returned_url = json_response.get('url')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'url': returned_url}).encode())
            else:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"Request to KoBo API failed with status code: {response.status_code}"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f"Error in Vercel serverless function: {str(e)}"}).encode())
