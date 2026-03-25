# Silent URL Cleaner & Shortener

A containerized URL shortener and cleaner designed for privacy and minimal overhead. It resolves redirects, strips tracking parameters, and removes referrer data in a single step with no logging.

## Features

- **Privacy**: 
    - Implementation of `Referrer-Policy: no-referrer` on all redirects.
    - Zero server or application logs.
- **Smart Cleaning**: 
    - Automated stripping of `utm_*`, `fbclid`, and other common tracking parameters.
    - Normalization of hosts and paths.
- **Smart Stop**: 
    - Redirect resolution terminates before reaching authentication gates (e.g., login pages).
- **Link Previews**: 
    - Bot detection serves Open Graph tags for rich previews in chat applications while maintaining human privacy.
- **Dark Theme**: 
    - Minimalist dark-mode interface for manual URL shortening.
- **Direct Access**: 
    - Support for cleaning URLs directly via the path (e.g., `localhost:5006/google.com`).

## Setup

### Prerequisites
- Docker and Docker Compose

### Getting Started
1. **Prepare Environment**:
   ```bash
   cp .env.docker.local.example .env.docker.local
   ```
2. **Start Service**:
   ```bash
   make up
   ```
   *By default, the service is available at `http://localhost:5006`.*

### Management Commands
- `make up`: Start the service stack.
- `make build`: Rebuild and start the containers.
- `make logs`: View application logs.
- `make clean`: Shut down and remove associated volumes.

## Configuration

Settings are managed via a tiered environment file system:
- `.env.docker`: Tracked default settings (Ports, Database).
- `.env.docker.local`: Local overrides and secrets (Untracked).
- `.env.production`: Production secrets (Exclusive priority).

## Testing

Smoke tests for cleaning and redirect logic are located in the scripts directory:
```bash
python3 scripts/verify_lean.py
python3 scripts/verify_smart_stop.py
```

## Architecture
The service is built as a single-file Python application running on an Alpine-based container for a minimal footprint. It uses deterministic hashing for short codes to ensure consistent mapping without redundant database lookups.
