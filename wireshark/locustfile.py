from locust import HttpUser, task, events
import gevent

# A dictionary to store the status codes and their counts per endpoint
status_codes = {}

@events.request.add_listener
def track_status_code(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    if response and (response.status_code < 200 or response.status_code >= 300):
        endpoint = name
        status_code = response.status_code
        if endpoint not in status_codes:
            status_codes[endpoint] = {}
        if status_code not in status_codes[endpoint]:
            status_codes[endpoint][status_code] = 0
        status_codes[endpoint][status_code] += 1

class WebsiteUser(HttpUser):

    host = "https://mifflin-dev-1047314544751.us-central1.run.app"
    wait_time = lambda _: 0  # No wait between requests

    # Define the list of hosts to be hit simultaneously
    hosts = [
        "https://mifflin-dev-1047314544751.us-central1.run.app/v2/heartbeat/"
    ]
    @task
    def send_requests(self):
        # List to hold greenlets for parallel execution
        jobs = []

        # Create a greenlet for each host and add it to the jobs list
        for host in self.hosts:
            job = gevent.spawn(self.send_request, host)
            jobs.append(job)

        # Wait for all greenlets to complete their tasks
        gevent.joinall(jobs)

    def send_request(self, host):
        """
        Send a request to the specified host and use a specific name to track it.
        """
        with self.client.get(host, name=f"Parallel Request to {host}", catch_response=True) as response:
            if response.status_code >= 400:
                response.failure(f"Received {response.status_code}")

# At the end of the test, you can print out the status codes counts
@events.test_stop.add_listener
def print_status_codes(environment, **kwargs):
    print("Final Report on Status Codes:")
    for endpoint, codes in status_codes.items():
        print(f"Endpoint: {endpoint}")
        for code, count in codes.items():
            print(f"  Status Code: {code} - Count: {count}")
    print("Completed printing status codes. Exiting now.")
    # Adding a flush to ensure all prints are outputted before exit
    import sys
    sys.stdout.flush()