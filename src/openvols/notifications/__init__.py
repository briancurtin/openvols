"""
Notification library for the OpenVols system.

Split into two independent verticals, each mirroring the repository pattern
used by openvols.data: a Protocol-based contract plus settings that select a
backend, in openvols.notifications.email and openvols.notifications.sms.
Callers should import those subpackages directly, e.g.
`from openvols.notifications import email`, rather than reaching into a
specific backend such as openvols.notifications.email.sendgrid.
"""
