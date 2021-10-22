# Hackerrank Evaluations

- [Setup](#setup)
- [Running The App](#running-the-app)
- [Deploying to Google App Engine](#deploy-google-app-engine)

## Setup
* This app runs on Python 3
  * `hackerrankevals.yaml` is a config file for running the app on the Google App Engine Python 3 Standard Environment
* It is recommended to use `virtualenv` with the directory name of `env`
* A config file `config.ini` is necessary
  * There is a example config file `config.example.ini`
    * You will need to generate a random base 64 string `SECRET_KEY` for use with sessions
    * You will need to generate a oauth client secret file for Google Login and include the file in the top level directory as well as the filename in the config file
* In order to run this app locally, you will need to generate SSL certificates `cert.pem` and `key.pem`

## Running The App

To run the app locally
* Set up the [`datastore emulator`](https://cloud.google.com/datastore/docs/tools/datastore-emulator) locally
* Start virtual environment
  * `virtualenv -p python3 env`
  * `source env/bin/activate`
  * If this is your first time, install the dependencies
    * pip install -r requirements.txt
* To start the server
  `FLASK_APP=app.py FLASK_DEBUG=1 python -m flask run --cert=cert.pem --key=key.pem -p 5001 --extra-files=config.ini`

## Deploying to Google App Engine

You must have the Google Cloud SDK installed

You can deploy using 

`gcloud app deploy hackerrankevals.yaml`

