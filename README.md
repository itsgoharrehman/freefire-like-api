# Free Fire Like API

High-concurrency asynchronous API service for player profile inspection and interaction automation with in-memory token rotation pool and connection pooling.

---

## Overview

A standalone REST API service built with FastAPI and AsyncIO. Designed for large-scale player profile inspection and interaction automation, managing concurrent sender accounts through an in-memory token rotation pool, micro-batched Protobuf serializations, and staggered HTTP connection pooling.

The service incorporates automated token health auditing, token quarantine on authentication failure, and an optional broadcast notifier.

## Architecture

```mermaid
sequenceDiagram
    autonumber
    participant Client as API Client / Caller
    participant Gateway as FastAPI Router (app.py)
    participant Auth as Security Layer (API Key)
    participant Pool as Token Manager (core/tokens.py)
    participant Dispatcher as Async Dispatcher (core/dispatcher.py)
    participant GameAPI as Remote Game Endpoints (Protobuf)
    participant Notifier as Notifier (core/notifier.py)

    Client->>Gateway: GET /api/v1/like?uid=<TARGET_UID>&key=<API_KEY>
    Gateway->>Auth: Validate Constant-Time API Key
    Auth-->>Gateway: Authorized
    Gateway->>Pool: Acquire Active Tokens
    Pool-->>Gateway: Return Active Tokens
    Gateway->>Dispatcher: Spawn Asynchronous Parallel Tasks
    par Micro-Batched Requests
        Dispatcher->>GameAPI: Binary Protobuf Payload (Chunk 1)
        Dispatcher->>GameAPI: Binary Protobuf Payload (Chunk 2)
        Dispatcher->>GameAPI: Binary Protobuf Payload (Chunk N)
    end
    GameAPI-->>Dispatcher: Delivery Acks
    Dispatcher->>Notifier: Optional Broadcast Event
    Dispatcher-->>Gateway: Aggregate Delivery Summary
    Gateway-->>Client: JSON Response
```

## Setup & Running

### 1. Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your parameters:
```env
API_KEY=your_secure_api_key_here
HOST=0.0.0.0
PORT=8000
```

### 3. Run Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Endpoints Reference

| Endpoint | Method | Authentication | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/like` | `GET` | `X-API-Key` or `?key=` | Dispatches parallel likes to the specified target UID. |
| `/api/v1/profile` | `GET` | `X-API-Key` or `?key=` | Inspects player profile details and level. |
| `/api/v1/tokens/status` | `GET` | `X-API-Key` or `?key=` | Returns token pool metrics. |
| `/api/v1/cron/refresh` | `GET` | `X-API-Key` or `?key=` | Triggers account token refresh. |
| `/api/v1/cron/ping` | `GET` | `X-API-Key` or `?key=` | Health ping endpoint. |
| `/health` | `GET` | Public | System health probe. |

## License

This project is licensed under the [MIT License](LICENSE).
