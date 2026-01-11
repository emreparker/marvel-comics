<p align="center">
  <img src="logo.webp" alt="Marvel Metadata API" width="120" />
</p>

<h1 align="center">Marvel Metadata API</h1>

<p align="center">
  Free, open-source API for Marvel Comics comic metadata.<br>
  Search 37,500+ issues, browse by series or creator, and build reading lists.
</p>

<p align="center">
  <a href="https://marvel.emreparker.com"><strong>Live API</strong></a> ·
  <a href="https://marvel.emreparker.com/swagger"><strong>Swagger UI</strong></a> ·
  <a href="#quickstart"><strong>Quickstart</strong></a> ·
  <a href="#reading-lists"><strong>Reading Lists</strong></a>
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square" />
  <img alt="Issues" src="https://img.shields.io/badge/issues-37.5k-green?style=flat-square" />
</p>

<p align="center">
  <sub>
    Unofficial fan project. Metadata + links only. No comic content is hosted or distributed.
  </sub>
</p>

---

## Why This Exists

I subscribed to **Marvel Comics** wanting to read **Jonathan Hickman's epic Avengers run** leading to **Secret Wars (2015)**. But there was a problem:

> **You can't create real reading lists.**
> You can add issues to your Library, or save links... but there's no good way to build a long, structured reading order.

The reading order I wanted wasn't small. If you want Secret Wars to *hit*, you should read Hickman's entire run leading up to it. That's not a weekend checklist — that's a whole saga.

I went looking for the **Marvel API** — only to realize it had been shut down. But I found [marvel.geoffrich.net](https://marvel.geoffrich.net), a site with cached Marvel API data and direct links to Marvel Comics.

So I built this: a tool to collect that cached metadata and turn it into a **searchable API** and **reading list builder**. Now I can finally read Hickman's Avengers/New Avengers saga in the right order.

**This project is for anyone who wants to build Marvel reading lists or explore comic metadata.**

---

## Data

| Metric | Count |
|--------|-------|
| Issues | 37,526 |
| Series | 6,990 |
| Creators | 4,341 |
| Years | 1939-2025 |

---

## Features

- **Full-Text Search** — Search across all issues by title
- **Browse by Series** — Get all issues in a series, sorted by publication order
- **Creator Lookup** — Find all issues by your favorite writers or artists
- **Direct MU Links** — Every issue includes a link that opens directly in Marvel Comics
- **Reading List Builder** — Generate Markdown checklists from JSON reading orders

---

## Rate Limits

| Limit | Value |
|-------|-------|
| Requests per minute | 60 |
| Burst allowance | 30 |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
```

---

## Quickstart

### Use the Hosted API

```bash
# Health check
curl https://marvel.emreparker.com/v1/health

# Search for issues
curl "https://marvel.emreparker.com/v1/search/issues?q=secret+wars&limit=5"

# Get a specific issue
curl https://marvel.emreparker.com/v1/issues/52447

# Browse issues from 2015
curl "https://marvel.emreparker.com/v1/issues?year=2015&limit=10"

# Get all issues in a series
curl https://marvel.emreparker.com/v1/series/16452/issues

# Find comics by Jonathan Hickman
curl "https://marvel.emreparker.com/v1/creators?role=writer&limit=50"
curl https://marvel.emreparker.com/v1/creators/11743/issues
```

### Interactive Docs

- **Custom Docs**: [marvel.emreparker.com](https://marvel.emreparker.com)
- **Swagger UI**: [marvel.emreparker.com/swagger](https://marvel.emreparker.com/swagger)
- **ReDoc**: [marvel.emreparker.com/redoc](https://marvel.emreparker.com/redoc)
- **OpenAPI JSON**: [marvel.emreparker.com/openapi.json](https://marvel.emreparker.com/openapi.json)

---

## API Endpoints

### Issues

| Endpoint | Description |
|----------|-------------|
| `GET /v1/issues` | List issues with optional filters (year, series_id) |
| `GET /v1/issues/{id}` | Get detailed issue metadata |
| `GET /v1/search/issues?q=` | Full-text search by title |

### Series

| Endpoint | Description |
|----------|-------------|
| `GET /v1/series` | List all series with issue counts |
| `GET /v1/series/{id}` | Get series summary |
| `GET /v1/series/{id}/issues` | Get all issues in a series |

### Creators

| Endpoint | Description |
|----------|-------------|
| `GET /v1/creators` | List creators with optional role filter |
| `GET /v1/creators/{id}` | Get creator details with role breakdown |
| `GET /v1/creators/{id}/issues` | Get all issues by a creator |

### System

| Endpoint | Description |
|----------|-------------|
| `GET /v1/health` | Health check with database status |

See the [Swagger UI](https://marvel.emreparker.com/swagger) for full request/response schemas.

---

## Reading Lists

This repo includes a reading list builder and example lists for Jonathan Hickman's Secret Wars saga.

### Pre-built Reading Lists

| List | Issues | Description |
|------|--------|-------------|
| [hickman_minimal.md](data/hickman_minimal.md) | 89 | Fast path: Avengers + New Avengers + Secret Wars |
| [hickman_full.md](data/hickman_full.md) | 219 | Full runway: Secret Warriors, FF, Ultimates, + main saga |

Each list is a Markdown checklist with direct Marvel.com links. Copy into Notes, Notion, or any Markdown app and start reading.

### Build Your Own Reading List

1. Create a JSON file with your reading order:

```json
{
  "name": "my_reading_list",
  "description": "My custom reading order",
  "issues": [
    "Avengers (2012) #1",
    "Avengers (2012) #2",
    "New Avengers (2013) #1"
  ]
}
```

2. Run the reading list builder:

```bash
python build_reading_list.py \
  --list lists/my_list.json \
  --db data/marvel.db \
  --out data/my_list.md
```

3. Output looks like:

```markdown
# my_reading_list

My custom reading order

## Checklist

- [ ] [Avengers (2012) #1](https://www.marvel.com/comics/issue/43528/avengers_2012_1)
- [ ] [Avengers (2012) #2](https://www.marvel.com/comics/issue/43532/avengers_2012_2)
- [ ] [New Avengers (2013) #1](https://www.marvel.com/comics/issue/43512/new_avengers_2013_1)

---
Total: 3
```

---

## Run Locally

### Prerequisites

- Python 3.10+
- SQLite database (download from releases or build yourself)

### Installation

```bash
git clone https://github.com/emreparker/marvel-comics.git
cd marvel-comics

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### Run the API

```bash
# Set database path
export MARVEL_DB_PATH=data/marvel.db

# Start server
uvicorn marvel_metadata.api.app:app --host 0.0.0.0 --port 8787
```

Your local server will be at `http://localhost:8787`. Or use the hosted API at [marvel.emreparker.com](https://marvel.emreparker.com).

### CLI Commands

```bash
# Parse a raw JSON payload into JSONL
marvel-metadata parse --input response-2022.json --out data/issues.jsonl

# Build SQLite database from JSONL
marvel-metadata normalize build --input data/all_issues.jsonl --out data/marvel.db

# Serve the API
marvel-metadata serve --db data/marvel.db --port 8787

# Build a reading list
marvel-metadata list-build --list lists/hickman.json --db data/marvel.db --out out/hickman.md
```

---

## Example Response

### GET /v1/issues/52447

```json
{
  "id": 52447,
  "digital_id": 38866,
  "title": "Secret Wars (2015) #1",
  "issue_number": "1",
  "description": "The Marvel Universe is no more! The interdimensional Incursions have eliminated each and every alternate universe one by one...",
  "page_count": 54,
  "detail_url": "https://www.marvel.com/comics/issue/52447/secret_wars_2015_1",
  "series": {
    "id": 18468,
    "name": "Secret Wars (2015 - 2016)"
  },
  "cover": {
    "path": "http://i.annihil.us/u/prod/marvel/i/mg/1/20/556f39d24db05",
    "extension": "jpg"
  },
  "dates": {
    "on_sale": "2015-05-06",
    "unlimited": "2015-11-09"
  },
  "creators": [
    {"id": 11743, "name": "Jonathan Hickman", "role": "writer"},
    {"id": 474, "name": "Esad Ribic", "role": "penciller (cover)"}
  ]
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| Database | SQLite with FTS5 |
| CLI | Typer |
| Hosting | Fly.io |

---

## Disclaimer

This is an **unofficial** fan-made project.

- Provides **metadata and links only**
- Does **not** host or distribute comic content
- Marvel and all related trademarks are property of their respective owners

---

## License

MIT
