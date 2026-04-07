from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DevRegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str


class DevLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    role: str
