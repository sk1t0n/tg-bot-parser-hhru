#!/bin/sh

gunicorn main:app --worker-class aiohttp.GunicornWebWorker
