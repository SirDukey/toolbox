#!/bin/bash

if [ $# -ne 2 ]
then
  echo "Usage: $0 {yellow|green|red} text"
  exit 1
fi

################################
# Outputs the text as color
# Args:
#   color
#   text
# Example:
#   color.sh green "Hello World!"
#################################
function print_msg() {
  YELLOW="\033[33m"
  GREEN="\033[32m"
  RED="\033[31m"
  NC="\033[0m"

  case "$1" in
    "green")
      echo -e "${GREEN}$2${NC}"
      ;;
    "red")
      echo -e "${RED}$2${NC}"
      ;;
    "yellow")
      echo -e "${YELLOW}$2${NC}"
      ;;
    *)
      echo "$2"
      ;;
  esac
}

print_msg "$1" "$2"
