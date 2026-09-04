"""
Public interface for the OpenVols SMS notification layer.

Callers should only ever import from openvols.notifications.sms, never from
a submodule such as openvols.notifications.sms.twilio or
openvols.notifications.sms._sms. That is what keeps callers decoupled from
which backend is actually configured.
"""

from openvols.notifications.sms._factory import *
from openvols.notifications.sms._sms import *
