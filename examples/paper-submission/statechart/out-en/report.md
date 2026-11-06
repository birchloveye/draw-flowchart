# Submission

TLC reached 14 states and 21 steps. The chart draws 10 states and 14 arrows.
1 state outside the constraints ends a rule's path, and the chart includes it. TLC checks the rules in a state outside the constraints, but it does not explore past it.
The view hides 2 steps, so the chart does not draw them.
The chart marks only the deadlock that TLC reports. Under a CONSTRAINT or an ACTION_CONSTRAINT, a state with no step in the chart can still have steps that the constraints leave out, and TLC does not count it as a deadlock.

## NoDeadlock breaks
The shortest path has 5 steps:
0. Drafting
1. you finish the draft: Co-authors reading
2. everyone signs off: With the editor
3. sent to reviewers: Under review
4. months pass: Under review
5. a reviewer vanishes [after months]: Lost in the system

## NoDualSubmission breaks
The shortest path has 5 steps:
0. Drafting
1. you finish the draft: Co-authors reading
2. everyone signs off: With the editor
3. sent to reviewers: Under review
4. months pass: Under review
5. you submit elsewhere [after months of silence]: Under review at two journals

## Rules that hold
TypeOK
