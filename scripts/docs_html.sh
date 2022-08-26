#! /bin/bash

. env/bin/activate
PYTHONPATH=./ sphinx-build -b html docs/source docs/build/html
deactivate
