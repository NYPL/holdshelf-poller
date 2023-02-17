# Holdshelf Poller

This is an app to poll Sierra for items placed on a holdshelf and notify those patrons.

## Purpose

This app connects to the Sierra database directly to identify items placed on a holdshhelf. The specific holdshelves and item holding locations are configurable. When it encounters an item on a holdshelf, it checks Redis to determine if the hold has already been processed. If it has not been processed, a call is made to the PatronServices Notify endpoint (TK).

## Installation

Via Docker:

```
docker image build -t holdshelf-poller:local .
docker container run -e ENVIRONMENT=development holdshelf-poller:local
```

Or for development in OSX:
```
pyenv local 3.10
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

## Usage

### Running locally

To build a set of local test data for the `development` environment:

```
psql -c 'CREATE DATABASE sierra_local_item_status_listener';
psql sierra_local_item_status_listener < sierra-schema.sql
```

To run the app against local test data:
```
AWS_PROFILE=nypl-digital-dev ENVIRONMENT=development python main.py
```

## Contributing

This repo uses the [Main-QA-Production Git Workflow](https://github.com/NYPL/engineering-general/blob/main/standards/git-workflow.md#main-qa-production)

## Testing

```
make test
```

To check linting:
```
make lint
```

## Troubleshooting
### Troubleshooting psycopg "ImportError: no pq wrapper available."

In OSX, if you have a `/usr/local/opt/libpq/lib` and xcode installed, but get above error when running the app locally, you [may need to](https://stackoverflow.com/questions/70585068/how-do-i-get-libpq-to-be-found-by-ctypes-find-library) install the `psycopg` this way:

```
pip uninstall psycopg
pip install "psycopg[c]"
```

### Troubleshooting psycopg "library not found for -lssl"

Try first:
```
xcode-select --install
```

Followed by:
```
env LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pip install psycopg2
```

