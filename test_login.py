import requests
from bs4 import BeautifulSoup

# Create a session to maintain cookies
session = requests.Session()

# First get the login page to extract any required tokens
login_url = 'https://secure.adidam.org/Account/LogOn'
response = session.get(login_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Print all form fields to see what's needed
form = soup.find('form')
if form:
    print("Form found. Form elements:")
    for input_field in form.find_all(['input', 'button']):
        print(f"Type: {input_field.get('type')}, Name: {input_field.get('name')}, Value: {input_field.get('value')}")

# Extract any tokens (common in login forms)
token = None
token_field = soup.select_one('input[name="__RequestVerificationToken"]')
if token_field:
    token = token_field.get('value')
    print(f"Found token: {token}")
else:
    print("No verification token found")

# Prepare login data
username = input("Username: ")
print("Password: ", end="")
password = input()

login_data = {
    'UserName': Genem-nyc,
    'Password': zoem88,
    'RememberMe': 'true'
}

if token:
    login_data['__RequestVerificationToken'] = token

# Attempt login
print("Submitting login...")
response = session.post(login_url, data=login_data)
print(f"Login response status: {response.status_code}")

# Check if login was successful
if 'Log Off' in response.text or 'Logout' in response.text:
    print("Login successful!")
else:
    print("Login failed. Please check credentials.")
    
# Try accessing a page that requires login
test_url = 'https://secure.adidam.org/academy/ear-of-heart/1'
print(f"Trying to access: {test_url}")
response = session.get(test_url)
print(f"Access response status: {response.status_code}")
print(f"Page title: {BeautifulSoup(response.text, 'html.parser').title.text if BeautifulSoup(response.text, 'html.parser').title else 'No title'}")