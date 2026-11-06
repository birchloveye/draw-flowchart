# Submission

TLC reached 14 states and 21 steps. The chart draws 10 states and 14 arrows.
1 state outside the constraints ends a rule's path, and the chart includes it. TLC checks the rules in a state outside the constraints, but it does not explore past it.
The view hides 2 steps, so the chart does not draw them.
The chart marks only the deadlock that TLC reports. Under a CONSTRAINT or an ACTION_CONSTRAINT, a state with no step in the chart can still have steps that the constraints leave out, and TLC does not count it as a deadlock.

## NoDeadlock breaks
The shortest path has 5 steps:
0. 写初稿
1. 你写完初稿: 合作者在看
2. 大家都同意: 在编辑手上
3. 送审: 审稿中
4. 几个月过去: 审稿中
5. 审稿人失联 [几个月后]: 石沉大海

## NoDualSubmission breaks
The shortest path has 5 steps:
0. 写初稿
1. 你写完初稿: 合作者在看
2. 大家都同意: 在编辑手上
3. 送审: 审稿中
4. 几个月过去: 审稿中
5. 你另投一家 [几个月没消息]: 同时在两家期刊审稿

## Rules that hold
TypeOK
