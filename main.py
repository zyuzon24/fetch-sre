import yaml
import requests
import time
import sys
import logging
from collections import defaultdict
from urllib.parse import urlparse
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

CHECK_INTERVAL = 15  # REQUIREMENT: Check every 15 seconds
TIMEOUT = 0.5  # REQUIREMENT: Endpoint responds in 500ms

# Set up file handler (detailed logs)
file_handler = logging.FileHandler("availability.log")
file_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)
file_handler.setFormatter(file_formatter)

# Set up console (stdout) handler (readable logs)
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter(
    "%(message)s"  # Only the message, no timestamp or log level
)
console_handler.setFormatter(console_formatter)

# Set up the root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

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
        logging.debug(f"Checked {url}: {response.status_code} in {duration_ms:.2f}ms")

        # Check if response is successful (2xx) and completed within 500ms
        if 200 <= response.status_code < 300 and duration_ms <= 500:
            return True
    except requests.RequestException as e:
        logging.warning(f"Request failed for {url}: {e}")
    
    return False

# Main function to monitor endpoints
def monitor_endpoints(file_path):
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    while True:
        for endpoint in config:
            url = endpoint['url']
            domain = extract_domain(url)
            result = check_health(endpoint)

            domain_stats[domain]["total"] += 1
            if result:
                domain_stats[domain]["up"] += 1

            status=''
            if result:
                status = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
            else:
                status = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"

            logging.info(f"{status}  {url}")
        
        
        # Log cumulative availability percentages
        logging.info("--- Availability Report ---")
        for domain, stats in domain_stats.items():
            up = stats["up"]
            total = stats["total"]
            if total > 0:
                availability = (up / total) * 100
            else:
                availability = 0
            logging.info(f"{domain} has {availability:.2f}% availability")

        logging.info("---------------------------\n")
        
        time.sleep(CHECK_INTERVAL)

# Entry point of the program
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")