#!/bin/bash

if [ -d "local-test" ]; then
  rm -rf local-test
fi

mkdir local-test
cd local-test

if [ -d "chalicelib" ]; then
  rm -rf chalicelib
fi
if [ -d "chalice" ]; then
  rm -rf chalice
fi

cp -R ../chalice chalice
cp "../$1/app.py" app.py
cp -R "../$1/chalicelib" chalicelib
cp -R "../model" chalicelib/model
cp -R "../utils" chalicelib/utils
cp -R "../config" chalicelib/config
cp -f "../local-config.py" chalicelib/config/__init__.py

chalice local
