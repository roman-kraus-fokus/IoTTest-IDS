import requests
import time 
import sys

if __name__ == "__main__":
    if len(sys.argv) == 3:
        mode = sys.argv[1] 
        testcase_name = sys.argv[2]

        url = f"http://localhost:80/ids/{mode}_testcase"
        data = {
            'testcase_name': testcase_name
        }

        response = requests.post(url, json=data)

        print(response.status_code)
        print(response.text)
    else:
        print("needed arguments: [start|stop] testcase_name")