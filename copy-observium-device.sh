#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: $0 <DEVICE_NAME> or \"all\""
	exit 1
fi


function timestamp() {
    date '+%d-%m-%Y %H:%M:%S'
}

check_dependencies() {
    dependencies=(
        jq
    )
    for cmd in "${dependencies[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "$(timestamp) [ERROR] Required command '$cmd' is not installed."
            missing=true
        fi
    done

    if [ "$missing" = true ]; then
        echo "$(timestamp) [ERROR] One or more dependencies are missing. Exiting."
        exit 1
    fi
}

check_dependencies


DEVICE_NAME="$1"

echo "Username for Observium: "
read OBSERVIUM_USER
echo "Password for $OBSERVIUM_USER: "
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
        #"$local_observium_host"
        "$remote_observium_host"
    )

    for host in "${hosts[@]}"; do
        curl --no-buffer -s -u $OBSERVIUM_USER:$OBSERVIUM_USER_PASSWORD \
        -X PUT https://$host.$domain/$api/$1/ \
        -H "Content-Type: application/json" \
        -d "{\"disabled\": \"$2\"}"
        if [ $? -ne 0 ]; then
            echo "$(timestamp) - [ERROR] - Failed to toggle polling for device $1 on $host"
            exit 1
        fi
    done
}


function update_device() {
    # $1 - device name

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
    scp -q -r $rrd_filepath/$1 $remote_observium_host.$domain:$rrd_filepath/
    if [ $? -ne 0 ]; then
        echo "$(timestamp) - [ERROR] - Failed to copy $1 to $remote_observium_host"
    fi

    # enable the polling on both observium hosts
    if [ "$state_changed" == "yes" ]; then
        toggle_polling $device_id $original_state
    fi
}


if [ "$DEVICE_NAME" == "all" ]; then
    # get the rrd folder list
    folders=()
    while IFS= read -r -d '' dir; do
        folders+=("$(basename "$dir")")
    done < <(find "$rrd_filepath" -mindepth 1 -maxdepth 1 -type d -print0)

    for device_name in "${folders[@]}"; do
        update_device $device_name
    done
else
    echo "Copying data for a single device: $DEVICE_NAME"
    update_device $DEVICE_NAME
fi
