------------------------ MODULE Registration ------------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Participants, Capacity
\* In the system, waitlist is a pseudonym for participants of an opportunity
\* who are approved=false. Approved users here are approved=true in the database.
VARIABLES waitlist, approved
vars == <<waitlist, approved>>

NotApproved(participant) == participant \notin approved
NotInWaitlist(participant) == \A u \in 1..Len(waitlist) : waitlist[u] /= participant
IsWaitlisted(participant) == \E u \in 1..Len(waitlist) : participant = waitlist[u]

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

\* There's no builtin Range. Return a set of all items in the sequence.
Range(seq) == {seq[i]: i \in 1..Len(seq)}


StillWaiting(participant) ==
{i \in 1..Len(waitlist) : waitlist[i] /= participant}

\* Pick a specific user from the waitlist and promote them
ManuallyPromote ==
    /\ waitlist /= <<>>
    /\ Cardinality(approved) < Capacity
    /\ \E participant \in Range(waitlist) :
       /\ approved' = approved \union {participant}
       /\ waitlist' = {u \in waitlist : u /= participant}

\* Take the next user from the list and promote
AutoPromote ==
    /\ waitlist /= <<>>
    /\ Cardinality(approved) < Capacity
    /\ LET participant == Head(waitlist)
        IN  /\ approved' = approved \union {participant}
            /\ waitlist' = Tail(waitlist)


\* CancelParticipation(participant) ==
\*     /\ \/ participant \in approved
\*        \/ \E u \in 1..Len(waitlist) : participant = waitlist[u]
\*     /\ approved' = approved \ {participant}
\*     /\ waitlist' = waitlist \ {participant}

Next ==
    \/ UNCHANGED <<waitlist, approved>>
    \/ \E participant \in Participants :
            \/ WaitlistParticipant(participant)
            \/ AutoApproveParticipant(participant)
            \/ ManuallyPromote
            \/ AutoPromote

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

ParticipantNotDroppedInv == IF /\ waitlist /= <<>>
                               /\ Cardinality(approved) > 1
                            THEN \A participant \in Participants : NotApproved(participant) => IsWaitlisted(participant)
                            ELSE TRUE

Spec == Init /\ [][Next]_vars
=================================================================
