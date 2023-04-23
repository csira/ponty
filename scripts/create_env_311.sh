#! /bin/bash

python3.11 -m venv env311
. env311/bin/activate
pip install -r reqs.txt
deactivate
