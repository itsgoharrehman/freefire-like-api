# Contributing to freefire-like-api

Thank you for your interest in contributing. We welcome contributions that optimize async task scheduling, improve token rotation efficiency, or refine Protobuf serialization.

## Core Architectural Invariants
1. **AsyncIO Non-Blocking Standard**: All networking routines in `core/` must remain strictly asynchronous (`async`/`await`). Synchronous blocking I/O (such as `requests.get()`) is prohibited.
2. **Zero Secret Leakage**: Never commit `tokens.json`, live API keys, or Telegram credentials.
3. **Protobuf Backward Compatibility**: Any modification to Protobuf schema files (`*_pb2.py`) must maintain binary protocol compatibility.
4. **Micro-Batch Stability**: Concurrency changes must respect `BATCH_STAGGER_DELAY` safeguards.

## Contribution Workflow
1. Fork and clone:
   ```bash
   git clone https://github.com/<your-username>/freefire-like-api.git
   cd freefire-like-api
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Create a focused branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Test changes locally with mock token responses.
5. Submit a Pull Request completing the mandatory security checklist in `.github/PULL_REQUEST_TEMPLATE.md`.