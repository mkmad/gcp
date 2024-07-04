import urllib

import google.auth.transport.requests
import google.oauth2.id_token

import os

"""
You need to provide the service account key in the application_default_credentials.json file. Here's how:

1. Create a Service Account Key:

- Go to the Google Cloud Console and navigate to IAM & Admin -> Service Accounts.
- Select the service account you want to impersonate (mohan-sa@mohan-sandbox.iam.gserviceaccount.com).
- Click on the "Keys" tab and then "Add Key".
- Choose "Create new key" and select "JSON" as the key type.
- Click "Create". This will download a JSON file containing the service account key.

2. Update application_default_credentials.json:

- Open the downloaded JSON file containing the service account key.
- Copy the entire contents of the file.
- Open your application_default_credentials.json file.
- Replace the entire contents of the file with the copied service account key.

3. Run Your Script:

- Run your Python script (invoke.py) again.

"""
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/mohan/gcp-keys/mohan-sandbox-sa.json"
CLOUD_FUNCTION_URL = "https://us-central1-mohan-sandbox.cloudfunctions.net/auth-function"

def make_authorized_get_request(endpoint, audience):
    """
    make_authorized_get_request makes a GET request to the specified HTTP endpoint
    by authenticating with the ID token obtained from the google-auth client library
    using the specified audience value.
    """

    # Cloud Functions uses your function's URL as the `audience` value
    # audience = https://project-region-projectid.cloudfunctions.net/myFunction
    # For Cloud Functions, `endpoint` and `audience` should be equal

    req = urllib.request.Request(endpoint)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)

    req.add_header("Authorization", f"Bearer {id_token}")
    response = urllib.request.urlopen(req)

    return response.read()

def make_unauthorized_get_request(endpoint):
    """
    make_unauthorized_get_request makes a GET request to the specified HTTP endpoint
    """

    try:
        req = urllib.request.Request(endpoint)
        response = urllib.request.urlopen(req)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    # unauth req
    print("\nUnauthenticated Request:")
    make_unauthorized_get_request(CLOUD_FUNCTION_URL)

    # auth req
    print("\nAuthenticated Request:")
    res = make_authorized_get_request(CLOUD_FUNCTION_URL, CLOUD_FUNCTION_URL)
    print(res)

