# GreenTrack – Tree Plantation Management System

A software-only web application for community afforestation, built with Python Flask, SQLite, HTML and CSS.

## Features
- Dashboard showing registered trees, healthy trees, trees needing care and a status ratio
- Add, view, edit and delete tree records
- Record species, location, planting date, responsible person, status and notes
- Optional photo upload
- Record follow-up growth logs, height and condition
- Search and filter records
- Export records as CSV

## Run on Windows
1. Install Python 3.9 or newer.
2. Extract this ZIP and open Command Prompt in this folder.
3. Run `py -m pip install -r requirements.txt`
4. Run `py app.py`
5. Open `http://127.0.0.1:5000` in your browser.

The SQLite database is created automatically as `trees.db`. Uploaded photos are stored in `static/uploads`.

This is a local prototype: it does not include cloud hosting, user accounts, live GPS, or hardware sensors. Change the Flask secret key and add authentication before any public deployment.
