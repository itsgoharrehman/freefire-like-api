# Free Fire Multi-Region Fleet Like API

A high-concurrency, asynchronous Free Fire like delivery and account management API engine supporting multi-region fleets (Bangladesh, Middle East, Pakistan, India, Europe, Americas).

---

## Features

- **High-Throughput Parallel Delivery:** Controlled 35-worker concurrency pool dispatching likes in parallel with sub-5s response time.
- **Dynamic Multi-Region Gateway Routing:** Automatic gateway resolution across Garena servers (`clientbp`, `ind`, `us`).
- **Synchronous Fast Token Renewal:** High-speed 30-worker parallel authentication engine with smart TTL evaluation, completing renewals in seconds without timeout risk.
- **Real-Time Telegram Alerts:** Event-driven visual cards for like delivery receipts, failure alerts, and token renewal reports.
- **Strict Security:** 100% environment-driven architecture with zero hardcoded credentials, API keys, or accounts in source code.

---

## Core Architecture

```
api/
  └── index.py            # FastAPI router exposing like dispatch, player info, health, and refresh
core/
  ├── config.py           # Multi-region settings, timeouts, and gateway routing
  ├── engine.py           # Parallel multi-region like dispatch and profile lookup engine
  ├── token_cache.py      # Hot in-memory token cache and Garena OAuth/MajorLogin renewal engine
  ├── crypto.py           # Free Fire AES-CBC encryption and Protobuf serializer
  └── telegram.py         # Async Telegram event notification client
ff_proto/                 # Free Fire OB55 Protobuf definitions
```

---

## API Endpoints

### 1. Delivery & Execution
- **`GET /like?uid={target_uid}`** or **`POST /like`**
  - Sends fleet likes in parallel to the target player UID.
  - Authentication: `X-API-Key` header, `Authorization: Bearer <key>`, or `api_key` query param.

### 2. Player Information
- **`GET /info?uid={target_uid}`**
  - Retrieves structured profile details: nickname, region, level, current likes, credit score, and ranking stats.

### 3. Fleet Health & Token Renewal
- **`GET /health`**
  - Returns service status, fleet name, configured accounts count, active cached tokens count, and server uptime.
- **`POST /refresh`** (or **`GET /refresh`**)
  - Runs synchronous high-concurrency token renewal across all configured accounts with smart TTL evaluation.

---

## Environment Configuration

Configure all settings via `.env` (gitignored):

```env
# Fleet Configuration
FLEET_NAME=GLOBAL
API_KEY=your_secure_api_key

# Garena Client Credentials
CLIENT_ID=100067
CLIENT_SECRET=your_garena_client_secret

# Concurrency & Timeouts
MAX_CONCURRENT_LIKES=35
MAX_CONCURRENT_REFRESH=30
REQUEST_TIMEOUT=4.5
MAJOR_TIMEOUT=4.0
REFRESH_STAGGER_DELAY=0.01
TOKEN_TTL_HOURS=20

# Telegram Event Alerts (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
```

---

## License

Private & Proprietary. All rights reserved.
