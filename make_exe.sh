#!/bin/bash

#PYTHONPATH=. pyinstaller --onefile pyportify/views.py
#PYTHONPATH=. pyinstaller --onefile pyportify/copy_all.py
PYTHONPATH=. pyinstaller pyportify.spec
#mv dist/copy_all dist/pyportify-copyall
#cp -R pyportify/static dist/

