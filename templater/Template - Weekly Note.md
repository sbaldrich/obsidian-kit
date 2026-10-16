---
register: true
---
<%*
tR = '';
const weekNum = tp.date.now("WW");
const year = parseInt(tp.date.now("GGGG"));
const weekStart = window.moment().isoWeekYear(year).isoWeek(parseInt(weekNum)).startOf('isoWeek').format('YYYY-MM-DD');
const weekEnd = window.moment().isoWeekYear(year).isoWeek(parseInt(weekNum)).endOf('isoWeek').format('YYYY-MM-DD');
await tp.file.move(`weekly/Week ${weekNum}`);

const planContent = `---\ntags:\n  - weekly-plan\nweek: ${weekNum}\nyear: ${year}\nweekly_note: "[[Week ${weekNum}]]"\n---\n\n## To-Do\n\n- [ ] \n\n## Notes\n\n`;
await tp.file.create_new(planContent, `Week ${weekNum} - Plan`, false, 'weekly');
%>---
tags:
  - weekly
week: <% weekNum %>
year: <% year %>
week_start: "[[<% weekStart %>]]"
week_end: "[[<% weekEnd %>]]"
---

## Plan
![[Week <% weekNum %> - Plan]]

## On This Week
![[Weekly.base]]
