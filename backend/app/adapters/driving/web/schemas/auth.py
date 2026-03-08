from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DevLoginRequest(BaseModel):
    email: str
    name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    role: str
