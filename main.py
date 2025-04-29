import yaml
import requests
import time
from collections import defaultdict
from urllib.parse import urlparse

CHECK_INTERVAL = 15  # REQUIREMENT: Check every 15 seconds
TIMEOUT = 0.5  # REQUIREMENT: Endpoint responds in 500ms

# Function to load configuration from the YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Extract domain from URL (ignores port numbers)
def extract_domain(url):
    parsed = urlparse(url)
    return parsed.hostname

# Function to perform health checks
def check_health(endpoint):
    url = endpoint['url']
    method = endpoint.get('method', 'GET').upper()
    headers = endpoint.get('headers',{})
    body = endpoint.get('body')

    try:
        start = time.time()
        response = requests.request(
            method, 
            url, 
            headers=headers, 
            data=body,
            timeout=TIMEOUT
        )
        
        duration_ms = (time.time() - start) * 1000
        
        if 200 <= response.status_code < 300 and duration_ms <= 500:
            return True
    except requests.RequestException:
        pass
    
    return False

# Main function to monitor endpoints
def monitor_endpoints(file_path):
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    while True:
        for endpoint in config:
            domain = extract_domain(endpoint["url"])
            result = check_health(endpoint)

            domain_stats[domain]["total"] += 1
            if result:
                domain_stats[domain]["up"] += 1

        # Log cumulative availability percentages
        print("\n--- Availability Report ---")
        for domain, stats in domain_stats.items():
            up = stats["up"]
            total = stats["total"]
            if total > 0:
                availability = (up / total) * 100
            else:
                availability = 0
            print(f"{domain} has {availability:.2f}% availability percentage")

        print("---")
        time.sleep(CHECK_INTERVAL)

# Entry point of the program
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")