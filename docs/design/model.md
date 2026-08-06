# Data model

The following sketches out a data model

## Opportunities

An opportunity is something to participate in

opportunity_id
created
updated
start
end
deadline
location_id
contact_user_id
title
description
capacity
public
open
cancelled
completed
notes
auto_approve
agreement_ids

## Participants

A participant is a user interested in an opportunity

participant_id
opportunity_id
user_id
created
updated
approved
cancelled
attended

## Locations

A location is where an opportunity takes place

location_id
created
updated
organization_id
name
address
coordinates
contact

## Agreements

An agreement is content that a participant must agree to on a given cadence

agreement_id
created
organization_id
title
content
cadence { single, annual, perpetual }

## Acceptances

An acceptance is the record a user accepting an agreement

agreement_id
opportunity_id
user_id
timestamp
valid_until

## Organizations

An organization hosts opportunities for users to participate in

organization_id
name
details
website
contact_name
contact_email
contact_phone
private_allowed
approved

## Roles

Users can have an advanced role per organization
- Managers can create and edit opportunities and approve participants in their orgnaization
- Admins can add/remove managers from organizations
- Super Admin can do all operations to all organizations

role_id
organization_id
user_id
role { manager, admin, super_admin}

## Users

A user is a person with an email address who participates in opportunities

user_id
first_name
last_name
email
email_reminders
phone
phone_reminders
