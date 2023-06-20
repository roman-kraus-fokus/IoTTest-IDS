import requests
import time 

url = 'http://localhost:80/ids/start_testcase'
data = {
    'testcase_name': '001',
    'timestamp_unix_in_ns': time.time_ns()
}

response = requests.post(url, json=data)

print(response.status_code)
print(response.text)