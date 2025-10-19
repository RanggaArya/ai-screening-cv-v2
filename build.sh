#!/bin/bash

# Keluar jika ada error
set -o errexit

# Instal dependensi
pip install -r requirements.txt

# Jalankan skrip ingesti data
python scripts/ingest_data.py