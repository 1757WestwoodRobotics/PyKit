#!/bin/bash

PROJECTS=(kitbot_2025 diff_drive skeleton)

for project in "${PROJECTS[@]}"; do
    rm -f $project.zip # Remove existing zip file if it exists

    cd $project
    zip -r ../$project.zip $(git ls-files .) > /dev/null
    cd ..
    echo "Generated $project.zip"
done
