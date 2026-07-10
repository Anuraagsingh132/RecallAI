## 2024-07-09 - N+1 database roundtrips during document chunk insertion
**Learning:** The document ingestion service was generating chunk `id` values dynamically in the database via an `async with scoped_transaction()` block, resulting in an unbatched N+1 insert sequence for parent chunks.
**Action:** By generating UUIDs client-side using `uuid.uuid4()`, the parent chunks can be batched together with `session.add_all()`, dramatically reducing database overhead during processing.
