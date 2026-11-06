// Reader's words for the Submission model (English). Colours: blue / yellow / purple / tan,
// which draw-flowchart maps to blue / cream / lavender / wood.
export const title = "A submission";

const NAMES = {
  draft: "Drafting", coauthors: "Co-authors reading", editor: "With the editor", review: "Under review",
  minor: "Minor revision", major: "Major revision", accepted: "Accepted", rejected: "Rejected",
  limbo: "Lost in the system",
};

export const state = (v) => (v.elsewhere ? "Under review at two journals" : NAMES[v.paper]);

// Steps that are their own actions in the spec
const STEPS = {
  ReviseMajor: "you revise and resubmit",
  TryAnotherJournal: "you try another journal", MonthsPass: "months pass",
  SubmitElsewhere: "you submit elsewhere [after months of silence]",
  ReviewerVanishes: "a reviewer vanishes [after months]",
};

// Simple stage changes all come from the Move helper in the spec, so name them by from > to
const MOVES = {
  "draft>coauthors": "you finish the draft",
  "coauthors>draft": "they ask for changes",
  "coauthors>editor": "everyone signs off",
  "editor>rejected": "desk reject",
  "editor>review": "sent to reviewers",
  "review>minor": "reviews: minor",
  "review>major": "reviews: major",
  "review>rejected": "reviews: reject",
  "minor>accepted": "you fix the small things",
};

export const step = (action, from, to) =>
  action === "Done" ? null : action === "Move" ? MOVES[`${from.paper}>${to.paper}`] : STEPS[action];

export const group = (v) => {
  if (v.elsewhere || v.paper === "rejected" || v.paper === "limbo") return "setback";
  if (v.paper === "draft" || v.paper === "coauthors") return "writing";
  if (v.paper === "accepted") return "done";
  return "journal";
};

export const colors = { writing: "blue", journal: "yellow", done: "purple", setback: "tan" };
