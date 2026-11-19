"""Health check endpoint.

Decision: Keep health checks free of heavy dependencies so orchestrators
(Kubernetes, Docker, load balancers) get a fast, reliable signal.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
