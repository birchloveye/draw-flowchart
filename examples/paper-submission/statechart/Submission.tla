---- MODULE Submission ----
\* A paper on its way to a journal. Used to show draw-flowchart's pstack statechart path:
\* TLC finds two ways the process goes wrong, and the poster marks them.

VARIABLES paper, elsewhere, waited
vars == <<paper, elsewhere, waited>>

Stages == {"draft", "coauthors", "editor", "review", "minor", "major", "accepted", "rejected", "limbo"}

TypeOK == paper \in Stages /\ elsewhere \in BOOLEAN /\ waited \in BOOLEAN

Init == paper = "draft" /\ elsewhere = FALSE /\ waited = FALSE

Move(from, to) == paper = from /\ paper' = to /\ UNCHANGED <<elsewhere, waited>>

FinishDraft         == Move("draft", "coauthors")
CoauthorsAskChanges == Move("coauthors", "draft")
CoauthorsSignOff    == Move("coauthors", "editor")
DeskReject          == Move("editor", "rejected")
SendOut             == Move("editor", "review")
ReviewsMinor        == Move("review", "minor")
ReviewsMajor        == Move("review", "major")
ReviewsReject       == Move("review", "rejected")
ReviseMinor         == Move("minor", "accepted")
ReviseMajor         == paper = "major" /\ paper' = "review" /\ waited' = FALSE /\ UNCHANGED elsewhere
TryAnotherJournal   == paper = "rejected" /\ paper' = "draft" /\ waited' = FALSE /\ UNCHANGED elsewhere
MonthsPass          == paper = "review" /\ ~waited /\ waited' = TRUE /\ UNCHANGED <<paper, elsewhere>>
\* The tempting shortcut after months of silence
SubmitElsewhere     == paper = "review" /\ waited /\ ~elsewhere /\ elsewhere' = TRUE /\ UNCHANGED <<paper, waited>>
\* A reviewer never answers and nobody chases it
ReviewerVanishes    == paper = "review" /\ waited /\ paper' = "limbo" /\ UNCHANGED <<elsewhere, waited>>
\* Accepted is the end
Done                == paper = "accepted" /\ UNCHANGED vars

Next == FinishDraft \/ CoauthorsAskChanges \/ CoauthorsSignOff \/ DeskReject \/ SendOut
        \/ ReviewsMinor \/ ReviewsMajor \/ ReviewsReject \/ ReviseMinor \/ ReviseMajor
        \/ TryAnotherJournal \/ MonthsPass \/ SubmitElsewhere \/ ReviewerVanishes \/ Done

Spec == Init /\ [][Next]_vars

\* Rule: a paper is never under review at two journals at once
NoDualSubmission == ~(elsewhere /\ paper \in {"editor", "review", "minor", "major"})

\* Stop a path once it breaks the rule, so the chart ends there
Explore == NoDualSubmission
====
