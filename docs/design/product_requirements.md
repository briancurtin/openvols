# OpenVols product requirements

## Problem

In talking to other trail organization leaders over the years, none really like their
volunteer management platform. As an organizer of a small nonprofit that partners with
larger land managers and joins their events as well, the platforms they use feel
heavier-weight than they need to be. Often times, email is the simplest
way to get actual registrations that result in people showing up, despite it
being harder to manage on the organization side.

Most of these platforms are single-tenant, so you need an account with all of them.
It's ultimately kind of a hassle to have one thing you're interested in doing
spread across many sites with all sorts of differences in how they're managed.

With volunteerism in decline[^0][^1], any roadblock to finding and retaining
willing participants is worth exploring.

## Goals

1. Provide a single place to find and register for volunteer opportunities.
2. Use email-based "magic links" for authentication, removing the friction
   of having extra accounts.
3. Provide analytics to find friction points in the process. This is only helpful
   once prospective volunteers have found this site, but knowing the conversion
   rates between discovery, registration, and attendance are something
   I don't believe is generally well known.

## Non-goals

This isn't necessarily trying to compete with any other service, I mostly think
it's fun to work on this project like I would if it was my job, and to experiment
with some things around planning, implementation, and delivery. This is mostly
born from my having free time and wanting to fix my own organization's website,
and figured I have the skills to solve this in a way that helps more than just
my own group.

While it's not a goal to "win" market share or anything like that, I do think
there's a real benefit to this platform existing, which is why I'm pursuing it.

## Audience

* Organizations seeking volunteers
* Volunteers seeking opportunities to serve

## Functional requirements

## Scope

### MVP

To launch, we should have the following capabilities:
* Users can authenticate via email
* Organizations can be created manually
* Users with admin role can create and manipulate opportunities
* Users can find opportunities
* Users can register for opportunities and are automatically approved
* Users are notified by email to remind of their upcoming participation

### v1

* Organization creation request workflow removes manual creation need
* Users can cancel their participation
* Participation being cancelled invokes promotion of next unapproved participant
* Users can be notified by text to remind of their upcoming participation

## Constraints

Time and money are the main constaints. It's an open source project to help
volunteers, so it's a double whammy. There are no deadlines to meet, it's mostly
a fun thing to do.


[^0]: https://www.evidencebasedmentoring.org/what-is-your-evidence-based-mentoring-iq-2/
[^1]: https://www.census.gov/library/working-papers/2025/adrm/CES-WP-25-41.html
