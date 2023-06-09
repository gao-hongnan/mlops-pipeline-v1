#!/bin/bash

# curl -o publish_package.sh \
#    https://raw.githubusercontent.com/gao-hongnan/common-utils/main/scripts/devops/ci/ci_publish_package.sh

set -e

# Fetch the utils.sh script from a URL and source it
UTILS_SCRIPT=$(curl -s https://raw.githubusercontent.com/gao-hongnan/common-utils/main/scripts/utils.sh)
source /dev/stdin <<<"$UTILS_SCRIPT"
logger "INFO" "Fetched the utils.sh script from a URL and sourced it"

usage() {
    echo "Usage: $0 [-u <username>] [-p <password>]"
    echo "  -u, --username    Twine username (default: __token__)"
    echo "  -p, --password    Twine password"
    exit 1
}

install_dependencies() {
    # Install dependencies
    python3 -m pip install --upgrade pip
    python3 -m pip install --upgrade build twine
}

build_package() {
    # Build package
    python3 -m build
}

upload_package() {
    # Upload package to Test PyPI
    twine upload dist/*
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--username)
            if [[ -z "$2" ]]; then
                echo "Value for TWINE_USERNAME is missing"
                exit 1
            fi
            TWINE_USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            if [[ -z "$2" ]]; then
                echo "Value for TWINE_PASSWORD is missing"
                exit 1
            fi
            TWINE_PASSWORD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set default values if not provided
TWINE_USERNAME=${TWINE_USERNAME:-__token__}

# Call functions
install_dependencies
build_package

# Upload package, passing username and password as environment variables
TWINE_USERNAME="$TWINE_USERNAME" TWINE_PASSWORD="$TWINE_PASSWORD" upload_package
