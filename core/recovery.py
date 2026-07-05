from sqlmodel import select
from models.base import ProcessingJob
from core.transactions import scoped_transaction

async def recover_zombie_jobs() -> int:
    """
    Finds jobs stuck in 'PROCESSING' state on server boot and reverts them to 'PENDING'.
    Returns the number of jobs recovered.
    """
    async with scoped_transaction() as session:
        statement = select(ProcessingJob).where(ProcessingJob.status == "PROCESSING")
        results = await session.execute(statement)
        jobs = results.scalars().all()
        for job in jobs:
            job.status = "PENDING"
        # Commit handled by scoped_transaction
        return len(jobs)
