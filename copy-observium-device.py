import getpass
import json
import logging
import os
import paramiko
import requests
import sys
from enum import Enum
from typing import Dict, List


DEVICE_NAME: str = sys.argv[1].lower()
TOGGLE: str = sys.argv[2]

OBSERVIUM_USER: str = os.getenv('OBSERVIUM_USER', input("Provide the username to connect to Observium API: "))
OBSERVIUM_USER_PASSWORD: str = os.getenv('OBSERVIUM_PASSWORD', getpass.getpass(f"Password for {OBSERVIUM_USER}: "))
AUTH: tuple = (OBSERVIUM_USER, OBSERVIUM_USER_PASSWORD)

api_url: str = "https://{}.management.nl-ix.net/api/v0/devices/"
local_observium_host: str = 'rtm-ixmgmt-observium-01'
LOCAL_OBSERVIUM_API: str = api_url.format(local_observium_host)
remote_observium_host: str = local_observium_host + '-new'
REMOTE_OBSERVIUM_API: str = api_url.format(remote_observium_host)


logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler('copy-observium-device.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)


class ToggleState(str, Enum):
    ENABLED = '0'
    DISABLED = '1'


class SFTPClient:
    def __init__(self) -> None:
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(
                remote_observium_host, 
                username=os.getenv('USER'), 
                password=getpass.getpass(f"Password for {os.getenv('USER')} (SSH): ")
                )
            self.sftp_client = self.ssh_client.open_sftp()
        except paramiko.ssh_transport.SSHException as e:
            logger.error(f"Failed to connect to {remote_observium_host}: {e}")
            sys.exit(1)
    
    def put(self, local_path: str, remote_path: str) -> None:
        try:
            self.sftp_client.put(local_path, remote_path)
        except paramiko.ssh_exception.SSHException as e:
            logger.error(f"Failed to upload file to {remote_observium_host}: {e}")
    
    def close(self) -> None:
        self.sftp_client.close()
        self.ssh_client.close() 


def list_subdirectories(path: str) -> List[str]:
    return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]


def get_all_device_ids(device_name: str = None) -> Dict[str, str]:
    device_id_map = {}
    get_url = LOCAL_OBSERVIUM_API if not device_name else LOCAL_OBSERVIUM_API + f"{device_name}/"
    get_response = requests.get(get_url, auth=AUTH)
    if get_response.status_code != 200:
        logger.error(f"Failed to retrieve device information from Observium API: {get_response.status_code}")
        sys.exit(1)
    device_info = get_response.json()
    if not device_info:
        logger.error("Could not retrieve a list of devices from Observium API")
        sys.exit(1)
    
    if not device_name:
        for device in device_info['devices'].values():
            device_id_map[device['hostname']] = device['device_id']
    else:
        device_id_map[device_info['device']['hostname']] = device_info['device']['device_id']
    return device_id_map


def update_device(device_id: str, toggle: ToggleState) -> bool:
    if not device_id:
        logger.error(f'Device {device_id} is missing or invalid')
        return False
    
    local_put_url = LOCAL_OBSERVIUM_API + f"{device_id}/"
    remote_put_url = REMOTE_OBSERVIUM_API + f"{device_id}/"
    headers = {"Content-Type": "application/json"}
    payload = {"disabled": toggle.value}
    put_kwargs = {"headers": headers, "data": json.dumps(payload), "auth":AUTH}
    
    try:
        local_put_response = requests.put(local_put_url, **put_kwargs)
        remote_put_response = requests.put(remote_put_url, **put_kwargs)

        if not all([local_put_response.ok, remote_put_response.ok]):
            logger.error(f"Failed to update device polling for {device_id}")
            return False
        logger.info(f"Successfully updated device polling for {device_id}")
        return True
    except requests.exceptions.RequestException as request_exception:
        logger.error(f"Failed to update device_id {device_id} polling: {request_exception}")
        return False


def copy_rrd_data(sftp_client: SFTPClient, device_name: str, rrd_filepath: str) -> None:
    device_rrd_filepath = os.path.join(rrd_filepath, device_name)
    sftp_client.put(device_rrd_filepath, device_rrd_filepath)
    

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ['0', '1']:
        print("Usage: python copy-observium-device.py <DEVICE> <TOGGLE>")
        print("  - DEVICE: single device name or 'all' to update all devices")
        print("  - TOGGLE: 0 (enabled) or 1 (disabled)")
        sys.exit(1)
        
    toggle = ToggleState(TOGGLE)
    sftp_client = SFTPClient()
    rrd_filepath = "/opt/observium/rrd"
    
    try:
        if DEVICE_NAME.lower() == "all":
            device_id_map = get_all_device_ids()
            folders = list_subdirectories(rrd_filepath)
            for device_name in folders:
                device_id = device_id_map.get(device_name, {}).get('device_id', None)
                updated = update_device(device_id, toggle)
                if updated:
                    copy_rrd_data(sftp_client, device_name, rrd_filepath)
        else:
            device_id_map = get_all_device_ids(DEVICE_NAME)
            updated = update_device(device_id_map.get(DEVICE_NAME), toggle)
            if updated:
                copy_rrd_data(sftp_client, DEVICE_NAME, rrd_filepath)
    finally:
        sftp_client.close()
