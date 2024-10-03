from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

class handler(BaseHTTPRequestHandler):
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

            # Get the login page to retrieve CSRF token
            login_url = 'https://kobo.unhcr.org/accounts/login/'
            login_page_response = requests.get(login_url)

            if login_page_response.status_code != 200:
                raise Exception(f"Failed to load login page. Status code: {login_page_response.status_code}")

            # Extract CSRF token from the login page
            soup = BeautifulSoup(login_page_response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

            # Extract initial csrftoken cookie
            initial_cookies = login_page_response.cookies.get_dict()
            csrftoken_cookie = initial_cookies.get('csrftoken')

            # Prepare payload
            payload = {
                'csrfmiddlewaretoken': csrf_token,
                'login': username,
                'password': password,
                'Login': '',  # Corresponds to the submit button
            }

            headers = {
                'Referer': login_url,
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            # Perform login
            login_response = requests.post(
                login_url,
                data=payload,
                headers=headers,
                cookies={'csrftoken': csrftoken_cookie},
                allow_redirects=False
            )

            # Check if login was successful
            if login_response.status_code != 302:
                raise Exception("Login failed. Please check your username and password.")

            # Extract cookies from the response
            login_cookies = login_response.cookies.get_dict()
            kobonaut_cookie = login_cookies.get('kobonaut', '')
            csrftoken_cookie = login_cookies.get('csrftoken', csrftoken_cookie)  # Update csrftoken if it changed

            # Prepare cookies for subsequent requests
            session_cookies = {
                'csrftoken': csrftoken_cookie,
                'kobonaut': kobonaut_cookie
            }

            # Now, proceed to make the API request using the session cookies
            base_url = "https://kobo.unhcr.org"
            api_url = f"{base_url}/api/v2/assets/{uid}/data/{id}/enketo/{action}/?return_url=false"

            # Make the GET request to the KoBo API with the session cookies
            api_response = requests.get(api_url, cookies=session_cookies)

            if api_response.status_code != 200:
                raise Exception(f"KoBo API request failed with status code {api_response.status_code}")

            # Parse the JSON response to get the Enketo URL
            enketo_data = api_response.json()
            enketo_url = enketo_data.get('url')

            # Access the Enketo URL to retrieve the __csrf cookie
            enketo_response = requests.get(enketo_url, cookies=session_cookies, allow_redirects=False)

            # Extract __csrf cookie
            enketo_cookies = enketo_response.cookies.get_dict()
            enketocsrf_cookie = enketo_cookies.get('__csrf', '')

            # Send cookies to the client
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            # Set cookies
            self.send_header('Set-Cookie', f'kobonaut={kobonaut_cookie}; Path=/; Domain=.unhcr.org; Secure; HttpOnly')
            self.send_header('Set-Cookie', f'csrftoken={csrftoken_cookie}; Path=/; Domain=.unhcr.org; Secure; HttpOnly')
            if enketocsrf_cookie:
                self.send_header('Set-Cookie', f'__csrf={enketocsrf_cookie}; Path=/; Domain=.unhcr.org; Secure; HttpOnly')
            self.end_headers()
            # Send the Enketo URL
            self.wfile.write(json.dumps({'url': enketo_url}).encode())

        except Exception as e:
            # Handle any exceptions that may occur during the request processing
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f"Error in serverless function: {str(e)}"}).encode())
