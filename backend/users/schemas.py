from pydantic import BaseModel
from pydantic import ConfigDict
from enum import Enum


class Organization(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)


class ClerkWebhookEvent(str, Enum):
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    USER_UPDATED = "user.updated"
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_DELETED = "organization.deleted"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_MEMBERSHIP_CREATED = "organizationMembership.created"
    ORGANIZATION_MEMBERSHIP_DELETED = "organizationMembership.deleted"
    ORGANIZATION_MEMBERSHIP_UPDATED = "organizationMembership.updated"


class ClerkWebhook(BaseModel):
    object: str = "event"
    type: ClerkWebhookEvent
    data: dict
