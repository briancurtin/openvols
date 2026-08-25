---
name: testing
description: Setting up and running the tools needed to test changes
---

# Testing
This is a small skill to setup and run tests.

## Instructions
1. Before testing any changes, ensure that the type checker passes by running `uv run --python 3.14 ty check`
2. If the types are good, format the code using `uv run --python 3.14 ruff format`
3. To start the Postgres database, run `docker compose up -d`
4. Apply database migrations by running `uv run yoyo apply -b`
5. Run the tests with `uv run --python 3.14 pytest`
