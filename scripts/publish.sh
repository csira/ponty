#! /bin/bash

. env/bin/activate
twine upload dist/*
deactivate
