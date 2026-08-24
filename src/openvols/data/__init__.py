"""
Public interface for the OpenVols data layer.

Callers -- openvols.api above all -- should only ever import from
openvols.data, never from a submodule such as openvols.data.postgres or
openvols.data._store. That is what keeps callers decoupled from which
backend is actually configured.
"""

from openvols.data._store import (
    AgreementRepository,
    ConflictError,
    DataError,
    DataSettings,
    LocationRepository,
    NotFoundError,
    OpportunityRepository,
    OrganizationRepository,
    ParticipantRepository,
    Repository,
    RoleRepository,
    Store,
    UserRepository,
)

__all__ = [
    "AgreementRepository",
    "ConflictError",
    "DataError",
    "DataSettings",
    "LocationRepository",
    "NotFoundError",
    "OpportunityRepository",
    "OrganizationRepository",
    "ParticipantRepository",
    "Repository",
    "RoleRepository",
    "Store",
    "UserRepository",
]
