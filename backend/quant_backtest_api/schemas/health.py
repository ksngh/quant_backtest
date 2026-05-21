from pydantic import BaseModel


class HealthDatabase(BaseModel):
    configured: bool
    reachable: bool


class HealthResponse(BaseModel):
    status: str
    service: str
    database: HealthDatabase
