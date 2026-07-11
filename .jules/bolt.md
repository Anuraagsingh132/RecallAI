## 2024-03-24 - Bulk deletes for document chunks
**Learning:** Avoid ORM-level sequential deletes (`session.delete(chunk)` in a loop) for large collections like document chunks. This causes an N+1 query problem and blocks the async event loop with excessive DB I/O.
**Action:** Use bulk deletes (`await session.execute(delete(Model).where(...))`) to reduce database roundtrips to O(1) and avoid loading models into memory.
