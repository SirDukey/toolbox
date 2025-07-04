#!/bin/bash

YELLOW="\033[33m"
GREEN="\033[32m"
RED="\033[31m"
WHITE="\033[1;37m"
NC="\033[0m"

if [ $# -ne 1 ]; then
	echo -e "Usage: ${YELLOW}$0 ${GREEN}<DEVICE_NAME>${NC} or ${GREEN}\"all\"${NC}"
	exit 1
fi


function timestamp() {
    date '+%d-%m-%Y %H:%M:%S'
}

function check_dependencies() {
    dependencies=(
        jq
    )
    for cmd in "${dependencies[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo -e "${WHITE}$(timestamp)${NC} [${RED}ERROR${NC}] Required command '$cmd' is not installed."
            missing=true
        fi
    done

    if [ "$missing" = true ]; then
        echo -e "${WHITE}$(timestamp)${NC} [${RED}ERROR${NC}] One or more dependencies are missing. Exiting."
        exit 1
    fi
}

check_dependencies


DEVICE_NAME="$1"

echo -e "${WHITE}Username for Observium: ${NC}"
read OBSERVIUM_USER
echo -e "${WHITE}Password for ${YELLOW}$OBSERVIUM_USER${WHITE}: ${NC}"
read -s OBSERVIUM_USER_PASSWORD

local_observium_host="rtm-ixmgmt-observium-01"
remote_observium_host="rtm-ixmgmt-observium-01-new"
domain="management.nl-ix.net"
api="api/v0/devices"
rrd_filepath="/opt/observium/rrd"


function toggle_polling() {
    # $1 - device id
    # $2 - polling status ("1" to disable, "0" to enable)

    hosts=(
        "$local_observium_host"
        "$remote_observium_host"
    )

    for host in "${hosts[@]}"; do
        response=$(curl --no-buffer -s -u $OBSERVIUM_USER:$OBSERVIUM_USER_PASSWORD \
        -X PUT https://$host.$domain/$api/$1/ \
        -H "Content-Type: application/json" \
        -d "{\"disabled\": \"$2\"}")
        update_response=$(echo "$response" | jq -r '.status')
        if [ "$update_response" != "updated" ]; then
            echo -e "${WHITE}$(timestamp)${NC} - [${RED}ERROR${NC}] - Failed to toggle polling for device $1 on $host"
            exit 1
        else
            echo -n -e " $host[$2:${GREEN}\u2713${NC}] "
        fi
    done
    echo ""
}


function update_device() {
    # $1 - device name

    echo -n -e "${WHITE}$(timestamp)${NC} - [${YELLOW}INFO${NC}] - Updating device $1"

    # convert the device name into a device id
    response=$(curl --no-buffer -s -u $OBSERVIUM_USER:$OBSERVIUM_USER_PASSWORD http://$local_observium_host.$domain/$api/$1/)
    device_id=$(echo "$response" | jq -r '.device_id')
    original_state=$(echo "$response" | jq -r '.device.disabled')
    state_changed="no"

    # disable the polling on both observium hosts
    if [ "$original_state" == "0" ]; then
        toggle_polling $device_id 1
        state_changed="yes"
    fi

    # copy the rrd folder to the new observium
    scp -q -r -p $rrd_filepath/$1 $remote_observium_host.$domain:$rrd_filepath/
    if [ $? -ne 0 ]; then
        echo -e "${WHITE}$(timestamp)${NC} - [${RED}ERROR${NC}] - Failed to copy $1 to $remote_observium_host"
    else
        echo -n -e " copy[${GREEN}\u2713${NC}] "
    fi

    # enable the polling on both observium hosts
    if [ "$state_changed" == "yes" ]; then
        toggle_polling $device_id $original_state
    fi
    echo ""

}


if [ "$DEVICE_NAME" == "all" ]; then
    # get the rrd folder list
    folders=()
    while IFS= read -r -d '' dir; do
        folders+=("$(basename "$dir")")
    done < <(find "$rrd_filepath" -mindepth 1 -maxdepth 1 -type d -print0)

    counter=0
    limit=2

    for device_name in "${folders[@]}"; do
        update_device $device_name
        echo ""
        ((counter++))
        if [ $counter -ge $limit ]; then
            break
        fi
    done
else
    update_device $DEVICE_NAME
fi
