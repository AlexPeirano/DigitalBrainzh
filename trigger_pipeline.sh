#!/bin/bash
# Trigger the DataLad preprocessing pipeline
# Usage: ./trigger_pipeline.sh "your commit message"

set -e

if [ -z "$1" ]; then
    echo "Usage: ./trigger_pipeline.sh \"commit message\""
    exit 1
fi

datalad save -m "$1"

# Integrate the result commits the CI pushed back to main
datalad update --how merge -s origin

# Push content to OSF first so the CI can download it once GitHub triggers
datalad push --to osf-storage data/raw/
datalad push --to origin
