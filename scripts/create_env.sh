#! /bin/bash

[ -d env ] && rm -r env
python3 -m venv env
. env/bin/activate
pip install --upgrade pip
pip install -r reqs.txt
pip install -r docs/requirements.txt
deactivate
