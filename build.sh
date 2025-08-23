#!/bin/bash
set -e
echo "Installing Python 3.12.11"
/app/.heroku/python/bin/python --version
echo "Installing pip from local whl"
/app/.heroku/python/bin/python -m ensurepip
/app/.heroku/python/bin/pip install ./wheels/pip-24.2-py3-none-any.whl
echo "Installing requirements"
/app/.heroku/python/bin/pip install -r requirements.txt