from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.partners.constants import BusinessPartnerRoleType


class BusinessPartnerRolePayload(BaseModel):
    role_type: BusinessPartnerRoleType
    valid_from: date | None = None
    valid_to: date | None = None


class BusinessPartnerCreate(BaseModel):
    partner_code: str = Field(max_length=50)
    partner_name: str = Field(max_length=200)
    tax_number: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    sap_card_code: str | None = Field(default=None, max_length=50)
    is_active: bool = True
    roles: list[BusinessPartnerRolePayload] = Field(default_factory=list)


class BusinessPartnerRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role_type: str
    valid_from: date | None
    valid_to: date | None


class BusinessPartnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    partner_code: str
    partner_name: str
    tax_number: str | None
    email: str | None
    phone: str | None
    address: str | None
    sap_card_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: list[BusinessPartnerRoleRead]
