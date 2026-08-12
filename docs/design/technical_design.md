# OpenVols Technical Design

## Overview

The OpenVols system is a multi-tenant open source volunteer management platform
that focuses on providing limited friction to prospective volunteers that want
to participate in opportunities to serve their community.

## Scope

### MVP
* Organizations can join. A likely early approach is manual setup until approvals are built.
* Organizations can do CRUD operations on opportunities
* Opportunities are listed and able to auto-approve registrations and waitlist participants
  * Waitlisted participants are auto-approved FIFO as opportunity capacity opens
* Users can authenticate via email magic link and set their contact information and preferences
* Users with access to a role can assume elevated privileges, such as managing an Organization
* Users can register to participate in an opportunity, or cancel their participation
* Email notifications can be sent 48 hours in advance of the opportunity

### Likely followup scope

* Organization approval system
* Registration and waitlist approval configurations, manual vs. automatic
* SMS notifications

## System architecture

At a high level, the system includes:
* Browser-based UI
* REST API service that integrates with a database and backs the UI
* Notification service that sends email and SMS reminders

```mermaid
architecture-beta

    group saas(cloud)[Hosted SaaS Services]
        service postgres(database)[Postgres] in saas
        service observability(database)[Observability] in saas

    group openvols(cloud)[OpenVols Platform]
        service frontend(internet)[UI] in openvols
        service loadbalancer(server)[Load Balancer] in openvols
        service api_node0(server)[API] in openvols
        service api_node1(server)[API] in openvols
        service collector(server)[OTel Collector] in openvols
        service scheduler(server)[Scheduler] in openvols
        service notifications(server)[Notifications] in openvols

    frontend:B <--> T:loadbalancer
    align column frontend loadbalancer

    align row scheduler loadbalancer

    scheduler:B --> T:notifications
    align column scheduler notifications

    loadbalancer:B --> T:api_node0
    loadbalancer:B --> T:api_node1
    align row api_node0 api_node1
    align column api_node0 collector

    api_node0:B --> T:collector
    api_node1:B --> T:collector
    notifications:B --> T:collector
    collector:B --> T: observability
    align column collector observability

    postgres:T <--> B:notifications
    postgres:T <--> B:api_node0
    postgres:T <--> B:api_node1
```

### UI

**TODO**

The UI will almost certainly use React. This is an area I know very little
about outside of my work on https://frtrails.org/, so it's not something I'm
coming into with as much thought as the backend.

### REST API

The REST API service will run on [FastAPI](https://fastapi.tiangolo.com/).

A few high level ideas:
* All authentication will be passwordless via "magic link" emails,
  authorization via roles that authenticated users can assume.
* Strict separation between REST layer and business logic. No code in the REST
  layer that isn't about HTTP.
* Use [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/) models
* Use [OpenTelemetry](https://opentelemetry.io/docs/languages/python/)
  for metrics and tracing.
    * The hosted deployment will likely use [Grafana's OTel support](https://grafana.com/docs/opentelemetry/).
* Use [structlog](https://www.structlog.org/en/stable/index.html) with
  [the OTel SDK](https://www.structlog.org/en/stable/frameworks.html#opentelemetry)
  to correlate logs with traces.

Most APIs here are CRUD operations without much or any logic. Add a location,
update a title, etc. One operations requires more logic: the waitlist.

#### Waitlist engine

The main feature of this platform is transitioning users to participants; the rest
is mostly CRUD. The likelihood of multiple concurrent approvals, especially
conflicting approvals, is infinitesimally small for this site. The stakes of
getting things wrong, such as allowing an extra participant, are pretty low
in my experience. However, that's not how everyone views it, and limits are limits
for a reason. It's a good thing to get right, and a nice exercise in building
good software. We can do this safely, so we should explore it.

* When a user registers their participation and `capacity > 0`, they are `approved = true`
* When a user registers their participation and `capacity == 0`, they are `approved = false`,
  aka waitlisted.
  * When the capacity of the event rises above the count of `approved = true` participants,
    participants can be added if the count is less or equal to the new open capacity.
    * This may happen due to a user canceling their participation, or by updating
      the event's capacity. Both must trigger evaluation of the wait list.
* It must be impossible to have `capacity < 0`

### Notifications

## Data model

```mermaid
```

## REST API

## Observability

## Testing
