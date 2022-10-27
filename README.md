# Getting Started

## Install Requirements

Install djangorestframework, elsapy, nltk, pybliometrics and requests.

```sh
cd .../mestrado-knowledge-maps/
pip3 install -r requirements.txt
```

## Setup

1. Apply Django's models to the database.

```sh
cd .../mestrado-knowledge-maps/mkm
python3 manage.py makemigrations
python3 manage.py migrate
```

2. (Optional) Add API keys to the following files:
```
.../mestrado-knowledge-maps/mkm/knowledge/api_utils/config.json.old
.../mestrado-knowledge-maps/mkm/knowledge/api_utils/config.ini.old
```
3. Rename them to:
```
config.json
config.ini
```

4. Create a super user.
```sh
cd .../mestrado-knowledge-maps/mkm
python3 manage.py createsuperuser
```

## Usage
Run server.
```sh
cd .../mestrado-knowledge-maps/mkm/
python3 manage.py runserver
```
