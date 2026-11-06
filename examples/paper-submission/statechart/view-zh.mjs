// Submission 模型的中文视角。颜色 blue / yellow / purple / tan 在 draw-flowchart 里对应 blue / cream / lavender / wood。
export const title = "一次投稿";

const NAMES = {
  draft: "写初稿", coauthors: "合作者在看", editor: "在编辑手上", review: "审稿中",
  minor: "小修", major: "大修", accepted: "接收", rejected: "被拒", limbo: "石沉大海",
};

export const state = (v) => (v.elsewhere ? "同时在两家期刊审稿" : NAMES[v.paper]);

// Steps that are their own actions in the spec
const STEPS = {
  ReviseMajor: "你改完重投",
  TryAnotherJournal: "你换一家期刊", MonthsPass: "几个月过去",
  SubmitElsewhere: "你另投一家 [几个月没消息]", ReviewerVanishes: "审稿人失联 [几个月后]",
};

// Simple stage changes all come from the Move helper in the spec, so name them by from > to
const MOVES = {
  "draft>coauthors": "你写完初稿",
  "coauthors>draft": "他们要求修改",
  "coauthors>editor": "大家都同意",
  "editor>rejected": "编辑直接拒稿",
  "editor>review": "送审",
  "review>minor": "审稿意见：小修",
  "review>major": "审稿意见：大修",
  "review>rejected": "审稿意见：拒稿",
  "minor>accepted": "你改完小问题",
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
