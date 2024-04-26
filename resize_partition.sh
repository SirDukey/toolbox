#!/bin/bash

growpart /dev/sda 3
pvresize /dev/sda3
lvm lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
resize2fs -p /dev/mapper/ubuntu-—vg-ubuntu--lv
