from kiteconnect import KiteConnect
import webbrowser

# Step 1: Set your credentials
api_key = "8u2wqiw1fiqfeo00"
api_secret = "5bskty652vfivmzht2vztithrap5dh3u"

kite = KiteConnect(api_key=api_key)

# Step 2: Open login URL
print("Login here and get the request_token URL:")
login_url = kite.login_url()
print(login_url)
webbrowser.open(login_url)

# Step 3: Paste request_token from URL after login
request_token = input("Paste request_token here: ")

# Step 4: Generate access_token
data = kite.generate_session(request_token, api_secret=api_secret)
print("Access token:", data["access_token"])
