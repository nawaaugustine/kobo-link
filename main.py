from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Parse parameters from URL
        params = parse_qs(urlparse(self.path).query)
        uid = params.get('uid')[0]
        id = params.get('id')[0]

        # Your base URL, change if needed
        base_url = "https://kobo.unhcr.org"

        # Construct the URL
        url = f"{base_url}/api/v2/assets/{uid}/data/{id}/enketo/edit/?return_url=false"

        # Make a GET request
        response = requests.get(url)

        # Ensure the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            json_response = response.json()

            # Extract the URL
            returned_url = json_response.get('url')

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(returned_url.encode())
        else:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Request failed with status code: {response.status_code}".encode())
        return
