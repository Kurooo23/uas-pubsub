# UAS Pub-Sub Log Aggregator — Implementation (Docker Compose)

**Services**: `aggregator` (FastAPI + workers), `publisher` (traffic generator), `broker` (Redis), `storage` (Postgres), `tests` (pytest).  
**Idempotency**: Unique `(topic, event_id)` + `INSERT ... ON CONFLICT DO NOTHING`.  
**Transactions**: Raw insert + processed upsert + counter update in a single transaction.  
**Isolation**: READ COMMITTED (sufficient with unique constraints).  
**Persistence**: Named volumes keep data across container recreates.

## Run
```bash
docker compose up -d --build
# (optional) Generate traffic
docker compose run --rm publisher
# (optional) Run tests (12–20 tests)
docker compose run --rm tests
```
## Endpoints
- `POST /publish` — single or batch.  
- `GET /events?topic=&limit=&offset=`  
- `GET /stats`  
- `GET /healthz`, `GET /readyz`
