# Mindcase Python SDK

[![PyPI version](https://img.shields.io/pypi/v/mindcase.svg)](https://pypi.org/project/mindcase/)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Collect structured data from 30+ web sources with a single API call. The official Python SDK for [Mindcase](https://mindcase.co).

```bash
pip install mindcase
```

## Quick Start

```python
from mindcase import Mindcase

client = Mindcase(api_key="mk_live_...")

results = client.run("instagram/profiles", params={
    "usernames": ["nike", "adidas"]
})

for row in results:
    print(f"{row['Username']}: {row['Followers']} followers")
```

## Supported Data Sources

| Platform | Agents | Use Cases |
|----------|--------|-----------|
| **LinkedIn** | Profiles, Companies, Employees, Jobs, Posts, People Search, Company Search, Domain Lookup | Lead generation, recruiting, market research |
| **Instagram** | Profiles, Posts, Comments | Influencer analysis, brand monitoring, engagement tracking |
| **YouTube** | Videos, Channels, Comments, Shorts | Content research, competitor analysis, audience insights |
| **Amazon** | Products, Reviews, Bestsellers | Price monitoring, product research, review analysis |
| **Google Maps** | Businesses, Reviews, Reverse Geocoding | Local business data, location intelligence, competitive analysis |
| **Twitter / X** | Posts | Social listening, trend tracking, sentiment analysis |
| **TikTok** | Profiles | Creator analytics, engagement benchmarking |
| **Reddit** | Posts, Comments | Community insights, brand sentiment, market research |
| **Shopify** | Products | Competitor pricing, product catalog extraction |
| **Indeed** | Jobs | Job market analysis, salary benchmarking |
| **App Store** | Reviews | App sentiment analysis, feature request mining |
| **Flipkart** | Products | Indian e-commerce pricing, product data |
| **Myntra** | Products | Fashion e-commerce data, trend analysis |

See all agents and parameters: [docs.mindcase.co/agents-overview](https://docs.mindcase.co/agents-overview)

## Features

- **30+ pre-built agents** across 15 platforms — no scraping infrastructure to manage
- **Sync and async** — block until results or fire-and-forget
- **Automatic polling** — `client.run()` handles job lifecycle for you
- **Typed responses** — iterate results, extract columns, convert to dicts
- **Retry with backoff** — built-in resilience for transient failures
- **Credit tracking** — check your balance programmatically

## Usage

### Discover Agents

```python
# List all available agents
agents = client.agents.list()

# Filter by platform
linkedin_agents = client.agents.list("linkedin")

# Get agent details and required parameters
agent = client.agents.get("linkedin/profiles")
print(agent.required_params)
```

### Run Agents

```python
# Synchronous — blocks until results are ready
results = client.run("linkedin/company-search", params={
    "queries": ["AI startups San Francisco"],
    "maxResults": 50
})

print(f"{results.row_count} companies found")
print(f"{results.credits_used} credits used")

for company in results:
    print(company["name"], company["industry"])

# Asynchronous — returns a Job immediately
job = client.run_async("amazon/reviews", params={
    "startUrls": [{"url": "https://www.amazon.com/dp/B0XXXXXXXXX"}]
})
print(f"Job {job.id} started, status: {job.status}")
```

### Manage Jobs

```python
# List recent jobs
jobs = client.jobs.list()

# Check status
job = client.jobs.get("job_abc123")
print(job.status)  # "completed", "running", "failed"

# Get results
results = client.jobs.results("job_abc123")

# Cancel a running job
client.jobs.cancel("job_abc123")
```

### Check Credits

```python
balance = client.credits()
print(f"{balance} credits remaining")
```

### Error Handling

```python
from mindcase import (
    Mindcase,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ValidationError,
    NotFoundError,
)

try:
    results = client.run("instagram/profiles", params={
        "usernames": ["nike"]
    })
except AuthenticationError:
    print("Invalid API key")
except InsufficientCreditsError as e:
    print(f"Need {e.required} credits, have {e.remaining}")
except RateLimitError:
    print("Too many requests — slow down")
except ValidationError as e:
    print(f"Bad parameters: {e}")
```

## Configuration

```python
client = Mindcase(
    api_key="mk_live_...",                         # or set MINDCASE_API_KEY env var
    base_url="https://api.mindcase.co/api/v1",    # default
    timeout=30,                                     # HTTP request timeout in seconds
    poll_interval=3.0,                              # job polling interval in seconds
    run_timeout=300,                                 # max wait for run() in seconds
)
```

## Get Your API Key

Sign up at [app.mindcase.co](https://app.mindcase.co) and create an API key in the API Console.

## MCP Server (Claude Integration)

This package includes a built-in MCP server that exposes all 30+ agents as Claude tools.

**Add to Claude Code:**

```bash
claude mcp add mindcase -- mindcase mcp
```

**Add to Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mindcase": {
      "command": "uvx",
      "args": ["mindcase", "mcp"],
      "env": {
        "MINDCASE_API_KEY": "mk_live_..."
      }
    }
  }
}
```

Then ask Claude: *"Find the top 10 AI startups on LinkedIn"* or *"Get reviews for this Amazon product"*.

## Also Available

- **[Node.js SDK](https://www.npmjs.com/package/mindcase)** — `npm install mindcase` for JavaScript/TypeScript

## Documentation

- [API Documentation](https://docs.mindcase.co)
- [Agent Reference](https://docs.mindcase.co/agents-overview)
- [Authentication](https://docs.mindcase.co/authentication)
- [Python SDK Guide](https://docs.mindcase.co/sdk/python)
- [MCP Server Guide](https://docs.mindcase.co/sdk/mcp)
- [Node.js SDK Guide](https://docs.mindcase.co/sdk/node)

## License

MIT
