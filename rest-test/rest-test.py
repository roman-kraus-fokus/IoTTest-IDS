import requests
import sys

if __name__ == "__main__":
    if len(sys.argv) == 4:        
        # either generation or testcase
        mode = sys.argv[1]
        # either start or stop
        stst = sys.argv[2] 
        # testcase or generation name
        name = sys.argv[3]



        url = f"http://localhost:80/ids/{stst}_{mode}"
        data = {
            f"{mode}_name": name
        }

        response = requests.post(url, json=data)

        print(response.status_code)
        print(response.text)
    else:
        print("needed arguments: [generation|testcase] [start|stop] name")