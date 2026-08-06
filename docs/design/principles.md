# Principles

The following principles guide how the OpenVols system is developed.

## Email-based IAM

* Everyone has email and very few people want another password to manage. Use the "magic link" idea.
* Make it very easy for users to sign up for opportunities. Enable a high conversion rate.
* Built-in email validation, reducing delivery problems.
* Email addresses can have different roles per-organization, e.g., an email address can map to a user
in one organization and an admin in another.

## Multi-tenancy

* The platform supports opportunities hosted by many organizations
* Organizations default to public opportunities and can be enabled to support private ones
    * Private here means they're not publicly listed. They're not hidden behind auth because not all
    users have a role linking them specifically with the organization. If you have the link you can
    participate. It's not intended to be so exclusive.

## Measure what matters

* Every opportunity should measure at least the following
    1. View counts of an opportunity.
    2. Participants of an opportunity that are started, approved, and after the opportunity occurs,
       ones that are marked completed by an owner.
* Use OpenTelemetry so we can decouple metrics creation from collection
* Use `structlog` for structured logging. No noise. If it doesn't help resolve a problem, don't log it.

## Strong boundaries

* Keep the UI, application, and domain layers separate
* Use dependency inversion to decouple logic fully from the data layer.
    * Deployment of the site will use Postgres but it will be more easily testable and changeable
      if we consider this from the start.
    * [SQLModel](https://sqlmodel.tiangolo.com/) looks nice and integrates with FastAPI, but it
      doesn't appear to support migrations. It might reuse alembic but it's not clear.
    * [Yoyo](https://ollycope.com/software/yoyo/latest/) has worked nicely on another project in the past
      to handle migrations, when used alongside [asyncpg](https://magicstack.github.io/asyncpg/current/)
