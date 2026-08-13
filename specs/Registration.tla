------------------------ MODULE Registration ------------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Participants, Capacity
\* In the system, waitlist is a pseudonym for participants of an opportunity
\* who are approved=false. Approved users here are approved=true in the database.
VARIABLES waitlist, approved
vars == <<waitlist, approved>>

\* There's no builtin Range. Return a set of all items in the sequence.
Range(seq) == {seq[i]: i \in 1..Len(seq)}

NotApproved(participant) == participant \notin approved
NotInWaitlist(participant) == participant \notin Range(waitlist)
IsWaitlisted(participant) == participant \in Range(waitlist)

\* They're not approved and not in the waitlist, but we're over capacity to approve
WaitlistParticipant(participant) ==
    /\ NotApproved(participant)
    /\ NotInWaitlist(participant)
    /\ Cardinality(approved) >= Capacity
    /\ waitlist' = Append(waitlist, participant)
    /\ UNCHANGED approved

\* They're not approved and not in the wait list, and there's capacity to approve
AutoApproveParticipant(participant) ==
    /\ NotApproved(participant)
    /\ NotInWaitlist(participant)
    /\ Cardinality(approved) < Capacity
    /\ approved' = approved \union {participant}
    /\ UNCHANGED waitlist

Next ==
    \E participant \in Participants :
        \/ WaitlistParticipant(participant)
        \/ AutoApproveParticipant(participant)
        \/ UNCHANGED <<waitlist, approved>>

Init ==
    /\ waitlist = <<>>
    /\ approved = {}

\* waitlist is a sequence, not a set, because we currently need random choice promotion
\* Promotion can be automatic, taking Head(waitlist), or manual, taking a random user
\* (in reality it's a manager picking a specific user). It may eventually expand to use
\* something like a priority queue so automatic promotion can be smarter than just FIFO.
TypeInv ==
    /\ waitlist \in Seq(Participants)
    /\ approved \in SUBSET Participants
    /\ Cardinality(approved) <= Capacity
    \* Uniqueness check to ensure no two waitlist items are the same
    \* If the indexes are different it implies that the values are different
    /\ \A i, j \in 1..Len(waitlist) : i /= j => waitlist[i] /= waitlist[j]

\* Ensure that we can't have a participant that is both approved and waitlisted
\* This state won't be possible in the database itself since it's represented
\* by the approved boolean, but here in the spec or in the application layer
\* we need to ensure we can't have them on both sides.
SingleStateInv ==
    \A participant \in Participants :
        IsWaitlisted(participant) => NotApproved(participant)


Spec == Init /\ [][Next]_vars
=================================================================
