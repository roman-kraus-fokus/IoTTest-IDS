## Sysdig
- if not done yet: install sysdig on the host, see: https://github.com/draios/sysdig/wiki/How-to-Install-Sysdig-for-Linux

## Agent
- install python dependencies:
    ```
    pip install -r requirements.txt
    ```
- run the agent script:
    ```sh
    sudo python3 agent.py target_container_name endpoint
    ```