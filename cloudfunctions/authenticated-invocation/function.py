# TO BE DEPLOYED AS A CLOUD FUNCTION IN GCP

from flask import Flask, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)

CLOUD_FUNCTION_URL = "" # Cloud function URL

@app.route('/', methods=['GET','POST'])
def hello_http(request):
    from google.auth.transport import requests as google_requests
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return 'Unauthorized', 401

    try:     
        token = auth_header.split(' ')[1]
        id_info = id_token.verify_token(token, google_requests.Request(), CLOUD_FUNCTION_URL)
        user_email = id_info['email']
    except Exception as e:
        return 'Unauthorized: {}'.format(e), 401

    return jsonify(message="Hello {}!".format(user_email))

if __name__ == '__main__':
    app.run(debug=True)