#!/bin/bash

cd application

mkdir package

## GREETINGS MODULE
mkdir "package/$1"

cp -R chalice "package/$1/chalice"
cp "$1/app.py" "package/$1/app.py"
cp -R "$1/chalicelib" "package/$1/chalicelib"
cp -R utils "package/$1/chalicelib/utils"
cp -R "model" "package/$1/chalicelib/model"
cp -R "config" "package/$1/chalicelib/config"

cd "package/$1"
zip -r "../$1.zip" .

cd ../../
mkdir packages


pip3 install -r requirements.txt --target packages
cd packages
zip -g -r "../package/$1.zip" .

cd ../package
rm -rf $1

aws s3 cp "$1.zip" "$2"

cd ..

rm -rf package
