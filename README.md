# UAS Pub-Sub Log Aggregator — Implementation (Docker Compose)

**Services**: `aggregator` (FastAPI + workers), `publisher` (traffic generator), `broker` (Redis), `storage` (Postgres), `tests` (pytest).  
**Idempotency**: Unique `(topic, event_id)` + `INSERT ... ON CONFLICT DO NOTHING`.  
**Transactions**: Raw insert + processed upsert + counter update in a single transaction.  
**Isolation**: READ COMMITTED (sufficient with unique constraints).  
**Persistence**: Named volumes keep data across container recreates.

## Isolation Level, Trade-offs, Mitigations

### Choice: READ COMMITTED (default)
READ COMMITTED dipilih untuk throughput dan konflik transaksi yang lebih rendah dibanding SERIALIZABLE. Pada desain ini, konsistensi utama (dedup/idempotency) tidak bergantung pada snapshot isolation, tetapi **dikunci oleh constraint unik + upsert atomik di DB**.

### Trade-offs (READ COMMITTED)
- **Phantom reads / non-repeatable reads**: hasil query `GET /events` bisa berubah antar request jika ada event baru masuk saat pagination.
- **Write skew / lost update**: bisa terjadi jika aplikasi memakai pola *read → compute → write* pada statistik atau state yang dipakai bersama banyak worker.

### Mitigations (yang dipakai di implementasi)
- **Unique constraints**: `(topic, event_id)` memastikan event duplikat tidak dapat “lolos” walau ada worker paralel.
- **Upsert / conflict handling**: `INSERT ... ON CONFLICT DO NOTHING` menjadikan dedup/idempotency **atomik** (race condition berubah jadi “satu menang, sisanya konflik”).
- **Atomic counters**: statistik diupdate dengan operasi atomik (`count = count + 1`), bukan baca-lalu-tulis, sehingga mencegah lost update pada beban paralel.
- **Single transaction boundary**: langkah “insert raw + mark processed/upsert + update stats” dilakukan dalam **satu transaksi** agar state tidak setengah jadi.

### Optional: SERIALIZABLE + retry (jika ingin konsistensi snapshot lebih kuat)
Jika sistem butuh konsistensi yang lebih ketat (mis. invariant kompleks lintas tabel), bisa memakai SERIALIZABLE. Trade-off utama: lebih sering terjadi **serialization failure**, sehingga aplikasi wajib melakukan **retry** (mis. exponential backoff) ketika DB melempar error serialisasi.

## Run
```bash
docker compose up -d --build
# (optional) Generate traffic
docker compose run --rm publisher
# (optional) Run tests inside compose
docker compose run --rm tests
