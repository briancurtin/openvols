------------------------ MODULE Waitlist ------------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Participants, Waitlist, Capacity
\* In the system, waitlist is a pseudonym for participants of an opportunity
\* who are approved=false. Approved users here are approved=true in the database.
VARIABLES waitlist, approved
vars == <<waitlist, approved>>

ASSUME Cardinality(Waitlist) >= 1

\* There's no builtin Range. Return a set of all items in the sequence.
Range(seq) == {seq[i]: i \in 1..Len(seq)}

NotApproved(participant) == participant \notin approved
NotInWaitlist(participant) == participant \notin Range(waitlist)
IsWaitlisted(participant) == participant \in Range(waitlist)

CancelParticipant(participant) ==
    /\ participant \in approved
    /\ approved' = approved \ {participant}
    /\ UNCHANGED waitlist

\* Pick a specific user from the waitlist and promote them
ManuallyPromote ==
    /\ waitlist /= <<>>
    /\ Cardinality(approved) < Capacity
    /\ \E participant \in Range(waitlist) :
       /\ approved' = approved \union {participant}
       \* TODO: This needs to be a Sequence, not a Set
       /\ waitlist' = {u \in Range(waitlist) : u /= participant}

\* Take the next user from the list and promote
AutoPromote ==
    /\ waitlist /= <<>>
    /\ Cardinality(approved) < Capacity
    /\ LET participant == Head(waitlist)
        IN  /\ approved' = approved \union {participant}
            /\ waitlist' = Tail(waitlist)

Next ==
    \E participant \in Participants :
        \/ CancelParticipant(participant)
        \/ AutoPromote
        \* \/ ManuallyPromote
        \/ UNCHANGED <<waitlist, approved>>

Init ==
    /\ waitlist = <<4>>
    /\ approved = {1, 2, 3}

\* waitlist is a sequence, not a set, because we currently need random choice promotion
\* Promotion can be automatic, taking Head(waitlist), or manual, taking a random user
\* (in reality it's a manager picking a specific user). It may eventually expand to use
\* something like a priority queue so automatic promotion can be smarter than just FIFO.
TypeInv ==
    /\ waitlist \in Seq(Waitlist)
    /\ approved \in SUBSET (Participants \union Waitlist)
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
