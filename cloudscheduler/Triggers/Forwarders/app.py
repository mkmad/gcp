import os
import requests
import logging
import signal
import datetime
import traceback
from flask import Flask, request, jsonify
from requests.adapters import HTTPAdapter, Retry

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=30)  # Set session timeout
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set max content length to 16MB

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("proxy_server.log"),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console
    ]
)

# Flask server load balancer IP
FLASK_SERVER_URL = "http://10.90.2.4:80/"

# Setup request session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))


@app.route("/", methods=["POST"])
def proxy():
    """
    Proxy endpoint for handling requests from Cloud Scheduler
    and forwarding them to the internal Flask server.
    """
    try:
        payload = request.get_json()
        if not payload:
            logging.warning("Received invalid payload")
            return jsonify({"error": "Invalid payload"}), 400

        logging.info(f"Forwarding request to {FLASK_SERVER_URL} with payload: {payload}")

        # Forward the payload to the Flask server with retry mechanism
        response = session.post(FLASK_SERVER_URL, json=payload, timeout=600)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx

        logging.info(f"Received response from Flask server: {response.json()}")

        return jsonify({"status": "success", "flask_response": response.json()}), response.status_code

    except requests.exceptions.RequestException as e:
        error_details = {
            "error": f"Failed to reach LB: {str(e)}",
            "error_type": type(e).__name__,
            "request_url": FLASK_SERVER_URL,
            "timestamp": datetime.datetime.now().isoformat()
        }
        logging.error(f"RequestException: {error_details}")
        return jsonify(error_details), 500

    except Exception as e:
        error_details = {
            "error": f"An error occurred: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        logging.error(f"General Exception: {error_details}")
        return jsonify(error_details), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for the Flask server.
    """
    return jsonify({"status": "OK", "message": "Flask server is healthy"}), 200


def shutdown_handler(signum, frame):
    """Handles graceful shutdown on SIGINT or SIGTERM"""
    logging.info("Received shutdown signal. Stopping Flask server...")
    os._exit(0)


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# Get the port from the environment variable or default to 8080
port = int(os.getenv("PORT", 8080))

if __name__ == "__main__":
    logging.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, threaded=True)
