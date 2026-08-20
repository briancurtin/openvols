"""
Data layer models

These models use a mixin to provide an ID and the created/updated timestamps
that get set via triggers, and inherit from a class of the same name
in the base models.
"""

from datetime import datetime

import pydantic

import openvols.models


class _DBModel(pydantic.BaseModel):
    """An object that exists in the database"""

    id: str = ""
    created: datetime | None = None
    updated: datetime | None = None


class Organization(_DBModel, openvols.models.Organization):
    """An Organization in the data layer"""


class User(_DBModel, openvols.models.User):
    """A User in the data layer"""


class Role(_DBModel, openvols.models.Role):
    """A Role in the data layer"""


class Location(_DBModel, openvols.models.Location):
    """A Location in the data layer"""


class Agreement(_DBModel, openvols.models.Agreement):
    """An Agreement in the data layer"""


class Opportunity(_DBModel, openvols.models.Opportunity):
    """An Opportunity in the data layer"""


class Participant(_DBModel, openvols.models.Participant):
    """A Participant in the data layer"""
