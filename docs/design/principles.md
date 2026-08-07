# Principles

The following principles guide how the OpenVols system is developed.

## Implementation characteristics

John Ousterhout's "A Philosophy of Software Design" is among my favorite books, and I think it's
a good overall guide for how I want to start this project. Below are some of the key things to
consider.

* Modules should be deep. Module is used in an abstract sense inclusive of executable systems;
  Python packages, modules, functions, and methods; REST APIs, etc.
* Eliminate special cases. Proper boundaries and translation between them can help ensure this.
  Models should consider invariants we can rely on instead of `null`/`None`, unless we specifically
  need their meaning.
* Pull complexity downward. The UI should not be handling business logic. REST APIs should
  not be doing anything except translating the HTTP layer. Keep higher levels simpler by having
  deeper modules that incorporate more of the logic with less configuration needed by what's above.
* Comments should describe _what_ and _why_, not _how_. Document reasoning for approaches,
  alternatives tried, and especially details about why you fixed something so we don't return
  to a prior mistake.
* Length is not by itself a useful criteria for measuring code. Breaking up a long function into
  a few smaller single-use functions is often a step backward. Depth and readability are more
  important factors. Having to jump around a lot when reading is not ideal, so cohesion within
  the function/module/package is something to be mindful of.

## Strong boundaries

* Keep the UI, application, and domain layers separate
* Use dependency inversion to decouple logic fully from the data layer.
    * This project's public deployment of the site will use Postgres, and it will be more easily
      testable and changeable if we consider abstractions between the application and data layer
      from the start.
    * [SQLModel](https://sqlmodel.tiangolo.com/) looks nice and integrates with FastAPI, but it
      doesn't appear to support migrations. It might reuse alembic but it's not clear.
    * [Yoyo](https://ollycope.com/software/yoyo/latest/) has worked nicely on another project in the past
      to handle migrations, when used alongside [asyncpg](https://magicstack.github.io/asyncpg/current/)

## Email-based IAM

* Everyone has email and very few people want another password to manage. Use the "magic link" concept.
* Make it very easy for users to register for opportunities. Enable a high conversion rate.
* Built-in email validation, reducing delivery problems.
* Email addresses can have different roles per-organization, e.g., an email address can map to a user
in one organization and an admin in another.
* Principal of Least Privilege—users have no role until they're granted one. Without a role you can
  do the simple actions an external person should need, such as viewing opportunities and registering
  to participate.

## Multi-tenancy

* The platform supports opportunities hosted by many organizations
* Organizations default to public opportunities and can be enabled to support private ones
    * Private here means they're not publicly listed. They're not hidden behind auth because not all
    users have a role linking them specifically with the organization. If you have the link you can
    participate. It's not intended to be a fully featured exclusive platform.

## Observability

* Use OpenTelemetry so we can decouple metrics and traces from their collection. This way
  the open source project is decoupled from deployment, which can use something like ClickHouse
  without the need for vendor lock-in upstream.
* Track metrics in the opportunity flow so we can analyze conversion and completion rate
* Use `structlog` for structured logging. No noise. If it doesn't help resolve a problem, don't log it.
