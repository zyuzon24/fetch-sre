# Fetch SRE Project (Python)

## Overview

This project monitors the availability of HTTP endpoints defined in a YAML configuration file and outputs cumulative availability by domain.

The code is based on the Python starter file provided by Fetch.

---

##  Requirements 

- Must accept a YAML configuration as command line argument
- YAML format must match that in the sample provided
- Must accurately determine the availability of all endpoints during every check cycle
- Endpoints are only considered available if they meet the following conditions
    - Status code is between 200 and 299
    - Endpoint responds in 500ms or less
- Must return availability by domain
- Must ignore port numbers when determining domain
- Must determine availability cumulatively
- Check cycles must run and log availability results every 15 seconds regardless of the number of endpoints or their response times

---

## Installation

### Install Python dependencies

```
pip install requests pyyaml
```

## Usage

Run the script with the YAML file path as an argument:
```
python main.py sample.yaml
```
The script will continue running until manually stopped (e.g., `Ctrl+C`).

## Issues Identified and Changes Made

### 1. Missing Method Default

- **Problem:** `method` field is optional, but if omitted, `requests.request()` receives `NoneType` object and raises an error.
- **Fix:** Used `endpoint.get('method', 'GET').upper()` to default to `'GET'`.
- **Identified by:** Running the code and getting an error
```
  File "/usr/lib/python3/dist-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/requests/sessions.py", line 564, in request
    method=method.upper(),
           ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'upper'
```

### 2. Headers Could Be NoneType

- **Problem:** Missing `headers` field resulted in `NoneType`, which can cause issues in the event of iterating through multiple headers.
- **Fix:** Used `endpoint.get('headers', {})` to default to an empty dictionary.

### 3. No Timeout

- **Problem:** Response times were not measured as it was a missing parameter in `requests.request()`. 
- **Fix:** Measured latency using `time.time()` and enforced a 500ms timeout with the `requests` library.
https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts

### 4. Set Constants

- **Problem:** Hardcoding the check frequency and timeout is not ideal for maintainability if the numbers need to be changed in the future.
- **Fix:** Create constants at the beginning of the script for easier maintanability of the check frequency and timeout.


### 5. Use urlparse from urllib library to extract domain

- **Problem:** String splitting was used to extract the domain and could leave ports included
- **Fix:** Utilize the urlparse within the urllib library, which splits a URL string to its components
https://docs.python.org/3/library/urllib.parse.html
- **Identified by:** Testing URLs with ports included
```
>>> from urllib.parse import urlparse

>>> ("scheme://netloc/path;parameters?query#fragment")
ParseResult(scheme='scheme', netloc='netloc', path='/path;parameters', params='',
            query='query', fragment='fragment')

>>> o = urlparse("http://docs.python.org:80/3/library/urllib.parse.html?"
    "highlight=params#url-parsing")

>>> o
ParseResult(scheme='http', netloc='docs.python.org:80',
            path='/3/library/urllib.parse.html', params='',
            query='highlight=params', fragment='url-parsing')

>>> o.scheme
'http'

>>> o.netloc
'docs.python.org:80'

>>> o.hostname
'docs.python.org'

>>> o.port
80

>>> o._replace(fragment="").geturl()
'http://docs.python.org:80/3/library/urllib.parse.html?highlight=params'
```

### 6. Return Type Changed from "UP"/"DOWN" to True/False
- **Problem:** The `check_health()` function returned "UP" or "DOWN" strings. While this is readable, this required awkward string comparisons like if result == "UP" in the `monitor_endpoints()` function.
- **Fix:** Replaced "UP"/"DOWN" with True/False. This made it possible to use the result directly in conditionals (`if result:`)

### 7. Division-by-Zero Protection When Calculating Availability
- **Problem:** The availability calculation originally assumed `total > 0` when computing `(up / total) * 100`. While the main loop does increment `total` on every endpoint check, there’s still a theoretical risk, like in future refactors, that the code could attempt to divide by zero.
- **Fix:** Added a conditional expression to handle the zero case, ensuring that the function returns `0` instead of raising a `ZeroDivisionError` if `total == 0`.

### 8. Incorrect Body Handling
- **Problem:** The original code used `json=body` when sending requests with payloads. The `body` provided in the YAML file is already a stringified JSON object (e.g., `'{"foo":"bar"}'`). The valid request was being incorrectly marked as a failure due to the API expecting a valid JSON object.
- **Fix:** Replaced json=body with `data=body`, which sends the body  as provided in the YAML without further encoding.
- **Identified by:** While testing the YAML sample provided, I noticed that availability was being reported as 25% instead of the expected 50%. After looking through each endpoint and printing the server responses, I confirmed that `sample body up`, which should have succeeded, was failing. Switching to `data=body` resolved the issue and produced the correct 50% availability.

### 9. Availability Output Accuracy

- **Problem**: The original starter code rounded availability percentages to the nearest integer, using round(). This causes a loss of precision. This is significant because for example if you have 1 million requests, a 99.99% success rate (100 failed requests) and a 99.95% success rate (500 failed requests) have a significant difference, and rounding these numbers loses that precision.

- **Fix:** Updated the code to preserve decimal precision by formatting availability with two decimal places using `availability = (up / total) * 100` and displaying it with `f"{availability:.2f}%"`. This ensures accurate visibility of changes in success rates over time.