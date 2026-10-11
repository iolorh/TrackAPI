# TrackAPI

**Track OpenAPI specification changes and detect potentially breaking API updates.**

**Live website:** https://trackapi.uk

## Features

- **Automatic monitoring** – Checks registered APIs every 6 hours.
- **Manual checks** – Trigger an immediate check whenever needed.
- **Breaking change detection** – Identifies removed endpoints, HTTP methods, schema properties and other potentially breaking changes.
- **Change classification** – Categorises detected differences by their potential impact.
- **Filtering** – Browse and filter previously detected changes.
- **Email notifications** – Sends notifications about API changes.
- **API spec and DeepDiff viewing** - View the most recent OpenAPI spec for every API, and the DeepDiff objects for every change, to help developers understand the changes

## Screenshots

### Dashboard
**View APIs, recent changes, and summarised information**
![TrackAPI Dashboard](static/screenshot1.png)

### APIs
**View all your APIs and their most recent OpenAPI specifications**
![TrackAPI APIs page](static/screenshot2.png)

### Changes
**View and filter through changes by the API and by breaking classification, and view every change's DeepDiff object**
![TrackAPI Changes page](static/screenshot3.png)

## How It Works

TrackAPI stores snapshots of API specifications and compares them to detect changes.

1. A user registers an API by providing a URL to its OpenAPI JSON specification.
2. TrackAPI retrieves the specification and stores a snapshot in its database.
3. A background worker periodically retrieves the latest specification.
4. DeepDiff compares the latest specification against the previous snapshot.
5. Changes are classified as breaking, potentially breaking or Non-Breaking.
6. The results are stored and displayed in a readable format.

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| HTTP requests | HTTPX |
| Specification comparison | DeepDiff |
| Database | SQLite |
| Frontend | HTML, CSS, Jinja2 |
| Application server | Gunicorn, Uvicorn |
| Reverse proxy | Traefik |
| Containerisation | Docker, Docker Compose |
| Hosting | DigitalOcean |

## Architecture

TrackAPI runs as multiple Docker containers, separating the web application from the automatic monitoring process.

The FastAPI backend handles user requests, API management and change history. A separate Python worker performs scheduled specification checks. Both components use a SQLite database to persist API registrations, specification snapshots and detected changes.

Traefik handles incoming HTTPS traffic and routes requests to the backend.

## Limitations

Change classification is based on predefined rules although it covers most of the possible OpenAPI spec changes, it's not guarantee that every breaking change will be detected.

Some changes may require manual review to determine their actual impact on API consumers.
