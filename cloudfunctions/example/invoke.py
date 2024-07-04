import urllib

import google.auth.transport.requests
import google.oauth2.id_token

import os

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

