#!/bin/bash

# # Configuration file
# config_file="pyproject.toml"

# # Extract the current version
# current_version=$(grep -E '^version = "[0-9]+\.[0-9]+\.[0-9]+"' "$config_file" | sed 's/version = "\(.*\)"/\1/')

# # Increment the version
# IFS='.' read -ra version_parts <<< "$current_version"
# version_parts[2]=$((version_parts[2] + 1))
# new_version="${version_parts[0]}.${version_parts[1]}.${version_parts[2]}"
# echo "Current version: $current_version"
# echo "New version: $new_version"

# # Update the version in the configuration file
# sed -i "s/version = \"$current_version\"/version = \"$new_version\"/" "$config_file"

# Re-create distribution directories
# rm -rf dist
# rm -rf gaohn_common_utils.egg-info

cd pipeline-feature

# Install build package
python3 -m pip install --upgrade build

# Build package
python3 -m build

# Install twine package
python3 -m pip install --upgrade twine

# Upload package to Test PyPI
source ../.env
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$PYPI_API_TOKEN

twine upload dist/*
# python3 -m twine upload --repository testpypi dist/*
