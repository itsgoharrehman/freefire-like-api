# GOHAR REHMAN | FREE FIRE LIKE API (OB55)

High-Speed, Non-Rate-Limited, Private Free Fire Like Engine with 780+ Sender Concurrency Control.

---

## ⚡ Features
- **Private API Authentication**: Protected with strict `X-API-Key` header or `?key=` query parameter.
- **Ultra-High Speed**: Shared persistent keep-alive connection pool (`aiohttp.TCPConnector`) eliminating TLS handshake latency.
- **Micro-Batch Pipelining**: Dispatches likes in bursts of 40 with 35ms micro-staggers to avoid Garena database row lock contention.
- **Zero Receiving Limit**: Bypasses any receiver bottlenecks by distributing requests across up to 780+ sender accounts.
- **External Cronjob Webhooks**: Built-in endpoints for external cron triggers (`cron-job.org` or Linux cron):
  - `GET /api/v1/cron/refresh`
  - `GET /api/v1/cron/ping`
- **Telegram Notifications**: Real-time channel delivery announcements with clean, one-line-per-point formatting and modern emojis.

---

## 🚀 Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
# Or on Windows: double-click start.bat
```

Default server runs on `http://localhost:8000`.
Interactive API docs available at `http://localhost:8000/docs`.

---

## 🔑 Configuration (`config/settings.py`)
Set environment variables or edit `config/settings.py`:
- `API_KEY`: Secret key required to access all `/api/v1/*` endpoints (default: `GOHAR-LIKE-SECRET-2026`).
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token.
- `TELEGRAM_CHAT_ID`: Your Telegram Channel or Group ID.
- `BATCH_CHUNK_SIZE`: Number of likes per micro-batch (default: `40`).
- `BATCH_STAGGER_DELAY`: Delay in seconds between batches (default: `0.035`s).

---

## 🌐 API Endpoints

### 1. Dispatch Likes
`GET /api/v1/like?uid=<UID>&region=<REGION>&count=<COUNT>&key=<API_KEY>`
- `uid`: Target Player UID (e.g. `6412705717`)
- `region`: `IND`, `BD`, `PK`, `US`, `BR`, `GLOBAL`
- `count`: Likes to send (e.g. `100`, `500`, `780`)
- `key`: Your private API key

### 2. Player Profile Lookup
`GET /api/v1/profile?uid=<UID>&region=<REGION>&key=<API_KEY>`
Returns live player nickname, level, region, and likes count.

### 3. Token Pool Status
`GET /api/v1/tokens/status?key=<API_KEY>`
Returns active vs banned token metrics across all regions.

### 4. External Cron Refresh
`GET /api/v1/cron/refresh?key=<API_KEY>`
Triggers cache reload from `data/tokens.json` and broadcasts Telegram report.

### 5. Health Ping
`GET /api/v1/cron/ping?key=<API_KEY>`
Endpoint for uptime monitors and external cron pings.
