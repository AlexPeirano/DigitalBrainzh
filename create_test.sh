#!/bin/bash
# Simple wrapper to create test EEG files
# Usage: ./create_test.sh [subject] [session] [task]

SUBJECT=${1:-"01"}
SESSION=${2:-"001"}
TASK=${3:-"test"}

# Activate venv and run the script
.venv/bin/python code/create_test_eeg.py \
    --subject "$SUBJECT" \
    --session "$SESSION" \
    --task "$TASK"

echo ""
echo "To save and push to OSF:"
echo "  datalad save -m \"data: test EEG sub-$SUBJECT ses-$SESSION\""
echo "  datalad push --to origin              # Push to GitHub"
echo "  datalad push --to osf-storage data/raw/  # Push content to OSF"
