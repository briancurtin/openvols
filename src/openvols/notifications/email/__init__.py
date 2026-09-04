"""
Public interface for the OpenVols email notification layer.

Callers should only ever import from openvols.notifications.email, never
from a submodule such as openvols.notifications.email.sendgrid or
openvols.notifications.email._email. That is what keeps callers decoupled
from which backend is actually configured.
"""

from openvols.notifications.email._email import *
from openvols.notifications.email._factory import *
