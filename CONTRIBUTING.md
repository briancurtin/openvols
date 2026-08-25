# Contributor Guide

TODO: lay out env setup details as I build them out

## AI Policy

AI is a tool. Good software is built through good design and good engineering practices. If you can produce that with AI, go for it.

Low-value submissions that have the appearance of slop, or change for the sake of change, will not be accepted. If you can't hold a conversation about any submitted issues or PRs, those will be closed without further engagement.

## Code Guidelines
- Comments should describe _what_ and _why_, not _how_. Ideally code is written in such a way
that the _how_ is identifiable, but if not, that's a sign it may be too complex.
- Use whitespace! Code is read more often than it's written, so readability counts.
  - `return` lines should be preceded by a blank line
  - The end of an indented scope should have a following blank line.
  - Introducing a new scope should _usually_ be preceded by a blank line. This is a bit situational,
    as sometimes you have preconditions defined right before a `for` block, which can be fine.
    If there are a stack of lines at one scope, break it up with whitespace before introducing
    an indented scope.
- Use concurrency effectively.
  - If you a coroutine can be scheduled earlier in a function's scope than when the result is needed,
    create the task early and `await` it where the answer is needed.
  - If you can schedule multiple coroutines, consider doing so.
  - You should still take care to understand what the effects of the concurrent call are, but a lot
    of the time we are better off scheduling a coroutine as early as possible if all of its data
    is available. Sometimes you want to wait to check a condition later on in a function to prevent
    even scheduling a coroutine at all, which can be fine, but you should evaluate the likelihood
    of the skip condition to see if it may make sense to always schedule the coroutine even
    if we don't end up needing its result.
- Import entire modules as much as possible. Prefer `from openvols import api`
  instead of `from openvols.api import <a dozen names>`. This does not apply to re-exporting names
  from an underscore prefixed module—that is expected and okay. The same guideline applies to
  standard library and third-party dependencies.
  - Sometimes it's acceptable to import specific names when they're either exact or very closely
  a duplicate. Use this sparingly only how its intended. A few cases that are ok to do:
    - `from datetime import datetime`
    - `from dataclasses import dataclass`
