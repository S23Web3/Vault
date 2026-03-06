# RESEARCH TASK — New Chat Execution Prompt
**Created:** 2026-03-05
**Purpose:** Self-contained prompt to give to a new Claude chat to execute the full log research task

---

## COPY THIS ENTIRE BLOCK INTO A NEW CHAT

---

## TASK: Chronological Log Research

You are a master researcher, not a builder. Your job is to read every session log in this vault, chronologically, and build a neutral factual picture of what has been done, what has changed, what has been decided, and what remains open. You will do this one file at a time.

**Output file:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md`

---

## RULES — NON-NEGOTIABLE

1. **One file at a time.** Read one file. Write findings. Then move to the next. Never batch-read multiple files in one step.
2. **Chronological order.** Oldest file first. Sequence is defined in the file list below.
3. **Write findings immediately** after reading each file, before moving to the next.
4. **Neutral.** No interpretation, no conclusions, no angles. Record what the file says. Facts only.
5. **APPEND to findings document.** Never overwrite. Each file gets its own section added to the bottom.
6. **If a Python script or code file is referenced** as a key deliverable in the log, read it too and note its actual state (does it exist, does it match what the log claims).
7. **No skipping.** If a file is short, still read it and record it. Every file counts.
8. **Do not summarise the project** until every file is read. The synthesis comes last.
9. **Track open vs closed decisions** as you go. If a log says "decision made: X" — record it. If a later log contradicts or changes it — record that too.

---

## FINDINGS DOCUMENT FORMAT

Each file gets this block appended:

```
---
## [filename]
**Date:** [date from filename or file content]
**Type:** [Session log / Build session / Strategy spec / Audit / Planning / Other]

### What happened
[Factual summary of what was done or discussed]

### Decisions recorded
[Any explicit decisions made — list them. If none, write "None."]

### State changes
[What changed vs what was previously known — code built, specs created, bugs found, bugs fixed]

### Open items recorded
[Anything explicitly listed as pending, unresolved, or next step]

### Notes
[Anything that contradicts a previous log, or updates a prior decision]
```

---

## FILE LIST — READ IN THIS ORDER

Work through this list top to bottom. The INDEX.md at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md` is the master reference — read it first to orient yourself, but do not write findings for it. It is a navigation tool only.

### Phase 1 — Origins (Jan 2025 – Jan 2026)
1. `Session-2025-01-21.md`
2. `2026-01-24.md`
3. `2026-01-25-trading-dashboard.md`
4. `2026-01-28-Jacky-VPS-Setup.md`
5. `2026-01-28-n8n-webhook-testing.md`
6. `2026-01-29-pine-script-review.md`
7. `2026-01-29-session-summary.md`
8. `2026-01-29-strategy-refinement-session.md`
9. `2026-01-30-tradingview-indicator-development.md`
10. `2026-01-31-quad-rotation-session.md`
11. `2026-01-31-session-summary.md`

### Phase 2 — February (Indicator Build, Backtester, ML Foundation)
12. `2026-02-02.md`
13. `2026-02-02-atr-sl-trailing-tp-build-spec.md`
14. `2026-02-02-atr-sl-trailing-tp-session.md`
15. `2026-02-02-avwap-anchor-assistant-framework.md`
16. `2026-02-02-dashboard-framework.md`
17. `2026-02-02-ripster-volume-status-build.md`
18. `2026-02-03.md`
19. `2026-02-03-quad-rotation-stochastic-spec-review.md`
20. `2026-02-03-quad-rotation-v4-fast-build-session.md`
21. `2026-02-04.md`
22. `2026-02-04-four-pillars-strategy-specification.md`
23. `2026-02-04-indicator-review-session.md`
24. `2026-02-04-quad-rotation-fast-v1.3-build.md`
25. `2026-02-05.md`
26. `2026-02-05-strategy-analysis-session.md`
27. `2026-02-06.md`
28. `2026-02-07.md`
29. `2026-02-07-backtest-results.md`
30. `2026-02-07-progress-review.md`
31. `2026-02-08.md`
32. `2026-02-09.md`
33. `2026-02-09-session-handoff.md`
34. `2026-02-10.md`
35. `2026-02-10-session1.md`
36. `2026-02-10-session2.md`
37. `2026-02-11.md`
38. `2026-02-11-v38-build-session.md`
39. `2026-02-11-v382-avwap-trailing-build.md`
40. `2026-02-11-vince-ml-architecture.md`
41. `2026-02-11-vince-ml-Session Log.md`
42. `2026-02-11-WEEK-2-MILESTONE.md`
43. `2026-02-12.md`
44. `2026-02-12-project-review-direction.md`
45. `2026-02-13.md`
46. `2026-02-13-full-project-review.md`
47. `2026-02-13-project-audit.md`
48. `2026-02-13-data-pipeline-build.md`
49. `2026-02-13-vince-ml-build-session.md`
50. `2026-02-13-vault-sweep-review.md`
51. `2026-02-14-bbw-full-session.md`
52. `2026-02-14-bbw-layer1-build.md`
53. `2026-02-14-bbw-layer2-build.md`
54. `2026-02-14-bbw-layer3-audit-pass3.md`
55. `2026-02-14-bbw-layer3-journal.md`
56. `2026-02-14-bbw-layer3-results.md`
57. `2026-02-14-bbw-layer4-audit-and-sync.md`
58. `2026-02-14-bbw-layer4-audit.md`
59. `2026-02-14-bbw-layer4-results.md`
60. `2026-02-14-bbw-layer5-audit.md`
61. `2026-02-14-bbw-layer5-v2-build-session.md`
62. `2026-02-14-bbw-layer6-audit.md`
63. `2026-02-14-bbw-uml-research.md`
64. `2026-02-14-dashboard-v31-build.md`
65. `2026-02-14-operational-logic-audit.md`
66. `2026-02-14-project-flow-update.md`
67. `2026-02-14-vault-sweep-review.md`
68. `2026-02-16-bbw-layer4b-plan.md`
69. `2026-02-16-bbw-layer4b-results.md`
70. `2026-02-16-bbw-v2-fundamental-corrections.md`
71. `2026-02-16-bbw-v2-layer4-5-prebuild-analysis.md`
72. `2026-02-16-bbw-v2-layer4-build-journal.md`
73. `2026-02-16-bbw-v2-layer4b-build-journal.md`
74. `2026-02-16-bbw-v2-layer5-logic-analysis.md`
75. `2026-02-16-full-project-review.md`
76. `2026-02-16-portfolio-bugfix.md`
77. `2026-02-16-portfolio-v3-audit.md`
78. `2026-02-16-project-status-data-strategy.md`
79. `2026-02-16-strategy-actual-implementation.md`
80. `2026-02-16-trade-flow-uml.md`
81. `2026-02-17-bbw-project-completion-status.md`
82. `2026-02-17-dashboard-v391-audit.md`
83. `2026-02-17-pdf-diagram-alignment.md`
84. `2026-02-17-pdf-export-optimization.md`
85. `2026-02-17-pdf-orientation-fix.md`
86. `2026-02-17-project-clarity-and-vince-architecture.md`
87. `2026-02-17-python-skill-update.md`
88. `2026-02-17-uml-diagrams-creation.md`
89. `2026-02-17-uml-logic-debugging.md`
90. `2026-02-17-vince-ml-strategy-exposure-audit.md`
91. `2026-02-18-dashboard-audit.md`
92. `2026-02-18-dashboard-v392-build.md`
93. `2026-02-18-vince-ml-build.md`
94. `2026-02-18-vince-ml-build-plan.md`
95. `2026-02-18-vince-scope-session.md`
96. `2026-02-19-engine-audit.md`
97. `2026-02-19-vince-scope.md`
98. `2026-02-20-bingx-architecture-session.md`
99. `2026-02-20-bingx-connector-build.md`
100. `2026-02-20-vince-scope.md`
101. `2026-02-20-youtube-transcript-analyzer-build.md`
102. `2026-02-23-dashboard-v393-bug-fix.md`
103. `2026-02-23-four-pillars-strategy-scoping.md`
104. `2026-02-23-screener-scope.md`
105. `2026-02-24-countdown-to-live-session.md`
106. `2026-02-24-fault-report-step1-build-review.md`
107. `2026-02-24-screener-scope.md`
108. `2026-02-24-vince-todo.md`
109. `2026-02-24-vince-v2-ml-spec-review.md`
110. `2026-02-24-weex-screener-scope.md`
111. `2026-02-25-bingx-connector-session.md`
112. `2026-02-25-lifecycle-test-session.md`
113. `2026-02-25-telegram-connection-session.md`
114. `2026-02-25-test-telegram-github-note.md`
115. `2026-02-26-bingx-audit-session.md`
116. `2026-02-26-vault-vps-migration-session.md`
117. `2026-02-26-vps-migration-part-a-violation.md`
118. `2026-02-26-yt-analyzer-gui-session.md`
119. `2026-02-27-bingx-api-docs-scraper-session.md`
120. `2026-02-27-bingx-automation-build.md`
121. `2026-02-27-bingx-trade-analysis.md`
122. `2026-02-27-bingx-ws-and-breakeven.md`
123. `2026-02-27-dash-skill-creation.md`
124. `2026-02-27-project-overview-session.md`
125. `2026-02-27-vince-concept-doc-update-and-plugin-spec.md`
126. `2026-02-27-vince-concept-lock-final.md`
127. `2026-02-27-vince-ml-yt-findings.md`
128. `2026-02-27-yt-analyzer-v2-build.md`
129. `2026-02-28-b2-api-types-research.md`
130. `2026-02-28-b3-enricher-research-audit.md` *(in plans/ subfolder — check both locations)*
131. `2026-02-28-bingx-be-fix.md`
132. `2026-02-28-bingx-dashboard-v1-1-build.md`
133. `2026-02-28-bingx-dashboard-v1-2-build.md`
134. `2026-02-28-bingx-dashboard-v1-3-patch.md`
135. `2026-02-28-bingx-dashboard-vince-planning.md`
136. `2026-02-28-bingx-trade-analysis-be-session.md`
137. `2026-02-28-bingx-ttp-research.md`
138. `2026-02-28-dash-skill-v12-community-audit.md`
139. `2026-02-28-dashboard-v393-promote.md`
140. `2026-02-28-parquet-data-catchup.md`
141. `2026-02-28-vince-b1-scope-audit.md`
142. `2026-02-28-vince-b4-scope-audit.md`

### Phase 3 — March (Live Bot, Vince Build Chain, Architecture)
143. `2026-03-02-b2-api-types-build.md`
144. `2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md`
145. `2026-03-03-bingx-dashboard-v1-4-patches.md`
146. `2026-03-03-cuda-dashboard-v394-build.md`
147. `2026-03-03-cuda-dashboard-v394-planning.md`
148. `2026-03-03-daily-bybit-updater.md`
149. `2026-03-03-session-handoff.md`
150. `2026-03-03-signal-rename-architecture-session.md`
151. `2026-03-03-ttp-integration-build.md`
152. `2026-03-03-ttp-integration-plan.md`
153. `2026-03-04-bingx-v1-5-full-audit-upgrade.md`
154. `2026-03-04-position-management-study.md`
155. `2026-03-05-bingx-bot-session.md`
156. `2026-03-05-bingx-data-fetcher-and-updater.md`
157. `2026-03-05-next-chat-prompt-audit.md`
158. `2026-03-05-project-review-volume-uml.md`

### Undated / Non-standard (read last)
159. `BUILD-JOURNAL-2026-02-13.md`
160. `build_journal_2026-02-11.md`
161. `PENDING-TASKS-MASTER.md`
162. `commission-rebate-analysis.md`

### Plans subdirectory (read last)
163. All files in `plans/` subdirectory — list them first with `filesystem:list_directory` then read each one

---

## SYNTHESIS — ONLY AFTER ALL FILES READ

Once every file is read and findings are recorded, write a final section at the bottom of RESEARCH-FINDINGS.md titled:

```
---
# SYNTHESIS
```

This section answers:

1. **What is this project trying to achieve?** (goal, not implementation)
2. **What is the current state of each major component?**
   - Four Pillars Backtester (Python)
   - BingX Live Bot
   - Vince ML pipeline (B1–B6)
   - Pine Script indicators
   - Infrastructure (VPS, n8n, dashboards)
3. **What is the primary blocker today?**
4. **What decisions have been made and are locked?**
5. **What decisions are still open?**
6. **What has been built that is confirmed working?**
7. **What has been built that is not yet tested or confirmed?**
8. **What was planned but never executed?**

---

## BEFORE YOU START — CONFIRM THIS

Read the INDEX at:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`

Then confirm:
- You understand the file list
- You will read one file at a time
- You will write findings before moving to the next file
- You will not batch
- You will not write synthesis until all files are done

State this confirmation, then begin with file 1: `Session-2025-01-21.md`

All files are located at:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\`

Use the `filesystem:read_text_file` tool to read each file.
Use the `filesystem:write_file` tool with APPEND logic to update the findings document — or use `filesystem:edit_file` to append each new section.

---

*End of prompt*
