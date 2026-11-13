#!/bin/bash
cd "$(dirname "$0")"
pip3 install -r requirements.txt
python3 init_db.py
python3 app.py
