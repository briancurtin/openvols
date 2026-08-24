# API route scaffolding

Summary of the work on the `add-tdd` branch to scaffold the REST layer for the
models in [models.py](../../src/openvols/models.py) and the tests that exercise it.

## Routes (`src/openvols/api/routers.py`)

* Added CRUD routes for all seven stored models: Organization, User, Role,
  Location, Agreement, Opportunity, Participant. Each resource gets:
  * `POST /api/<resource>` — create
  * `GET /api/<resource>` — list
  * `GET /api/<resource>/{id}` — get one
  * `PATCH /api/<resource>/{id}` — update
  * `DELETE /api/<resource>/{id}` — delete
* Create/update bodies use the base models (`Organization`, `User`, etc.)
  directly, wrapped with `fastapi.Body(embed=True)` to match the existing
  `/api/auth/login` convention.
* Every route except delete declares a `response_model` (the corresponding
  `Stored*` model, or a `list[...]`), so the OpenAPI schema is accurate and
  responses are actually validated rather than just documented.
* Create and update handlers build a real `Stored*` instance from the request
  body instead of returning a bare `200`:
  * Create sets `id=str(uuid.uuid4())`.
  * Update reuses the path `id`.
* Get handlers build a `Stored*` instance from module-level placeholder data
  (`_EXAMPLE_ORGANIZATION`, etc.) plus the requested `id`, since there's no
  data layer wired up yet.
* List routes return a small per-resource wrapper model (`ListStoredOrganizations`,
  etc.) holding an empty list, keyed by resource name, e.g. `{"organizations": []}`.
* Delete routes have no `response_model` and just `return 200`.

## Tests (`tests/test_routes.py`)

* Added a `fastapi.testclient.TestClient`-based pytest suite covering every
  route above, run against the real app so `response_model` validation is
  exercised, not bypassed.
* One payload fixture per model (`organization_body`, `user_body`, etc.);
  fixtures for nested models depend on the fixtures they need (e.g.
  `role_body` depends on `organization_body` and `user_body`).
* CRUD coverage is parametrized across the 7 resources (`RESOURCES`) instead
  of duplicating each test 7 times.
* Also covers the two auth routes (`/api/auth/login`, `/api/auth/validate`).
* `tests/__init__.py` existed as a stray empty directory rather than a file;
  replaced it with a real (empty) module file so `tests` is an importable
  package.

## Not yet done

* No data layer — create/get/update responses use placeholder or echoed
  request data, not anything persisted.
* Auth routes (`login`, `validate`) have no real magic-link logic yet.
* No pagination, filtering, or auth/authorization on any route.
