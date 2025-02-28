#!/bin/bash

# Exit script immediately if a command fails
set -e

# Define GCS path and local data path
GCS_PATH="gs://index_data_dishcovery/inverted_index_2.lmdb"
DATA_PATH="/backend/src/data/index_data_dishcovery/"
LMDB_DIR="/backend/src/data/index_data_dishcovery/inverted_index_2.lmdb"
# GOOGLE_APPLICATION_CREDENTIALS="/backend/gcs-container-key.json"

# gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# Check if the LMDB file already exists
if [ ! -d "$LMDB_DIR" ]; then
    echo "Downloading LMDB file from Google Cloud Storage..."
    gsutil -m cp -r $GCS_PATH $DATA_PATH
else
    echo "LMDB file already exists. Skipping download."
fi

# Start the Flask server
exec python -u -m flask run --host=0.0.0.0 --port=${PORT:-8080}