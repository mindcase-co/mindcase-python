# Mindcase Python SDK

Official Python SDK for the [Mindcase Developer API](https://docs.mindcase.co) — programmatic access to 30+ data collection agents across Instagram, LinkedIn, YouTube, Amazon, Google Maps, and more.

## Installation

```bash
pip install mindcase
```

## Quick Start

```python
from mindcase import Mindcase

client = Mindcase(api_key="mk_live_...")
# Or set MINDCASE_API_KEY env var and omit api_key

# Run an agent and get results
results = client.run("instagram/profiles", params={
    "usernames": ["nike", "adidas"]
})

for row in results:
    print(f"{row['Username']}: {row['Followers']} followers")
```

## API Reference

### Discovery

```python
# List all agents
agents = client.agents.list()

# Filter by platform
agents = client.agents.list("instagram")

# Get agent details + required params
agent = client.agents.get("instagram/profiles")
print(agent.required_params)
```

### Run Agents

```python
# Sync — blocks until results
results = client.run("instagram/profiles", params={
    "usernames": ["nike"]
})

# Async — returns immediately
job = client.run_async("instagram/profiles", params={
    "usernames": ["nike"]
})
print(job.id, job.status)
```

### Manage Jobs

```python
jobs = client.jobs.list()
job = client.jobs.get("job_abc123")
results = client.jobs.results("job_abc123")
client.jobs.cancel("job_abc123")
```

### Credits

```python
balance = client.credits()
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
except InsufficientCreditsError:
    print("Not enough credits")
except RateLimitError:
    print("Too many requests")
```

## Configuration

```python
client = Mindcase(
    api_key="mk_live_...",                          # or MINDCASE_API_KEY env var
    base_url="https://api.mindcase.co/api/v1",     # default
    timeout=30,                                      # HTTP timeout (seconds)
    poll_interval=3.0,                               # polling interval (seconds)
    run_timeout=300,                                  # max wait for run() (seconds)
)
```

## Documentation

Full docs: [docs.mindcase.co](https://docs.mindcase.co)
