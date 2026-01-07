#!/bin/bash

PROJECTS=(kitbot_2025 diff_drive skeleton)

mkdir -p generated # Create generated directory if it doesn't exist
for project in "${PROJECTS[@]}"; do
    rm -f $project.zip # Remove existing zip file if it exists
    rm -rf "generated/$project" # Clean up previous generated folder
    mkdir -p "generated/$project"
    git ls-files -z "$project" | xargs -0 -I {} cp --parents "{}" "generated"
    cd "generated/$project"
    zip -r ../$project.zip .
    cd ../..
    echo "Generated $project.zip"
done
