# Slide library

200 layouts to build content slides from. The template's 12 slides in `src/slides/` are the
default deck; this folder holds the alternatives. Cover and final stay as in the template (skill
`deck-cover-final`); everything between them is picked here or built from the same blocks.

```bash
npm run library                          # dist/library.html (animated) + shots/library-1..5.png
npm run slide:add -- hub 05-agents       # copies a layout into src/slides/05-agents, renames the id
npm run slide:add -- 67 06-flows         # the same by number
```

Look at the contact sheets `shots/library-1.png` to `library-5.png` before choosing. Every layout
is light, reads only `--deck-*` tokens, animates every element on entry and has a title that fits
one line.

## Choosing

1. Write the slide card first (skill `pitch-deck`): one thesis, one visual, the number.
2. Pick the layout whose visual *is* that thesis. Two neighbouring slides never share a layout;
   a deck uses at least eight different layouts and at least three kinds of visual: a chart, a
   diagram, a product screen, a big number.
3. Nothing fits: build the slide from the blocks and chart types below, then, if it is good and
   generic, add it here as the next `NNN-id` folder with placeholders.

## Catalog

### Problem and context

| # | Layout | Use it for |
| --- | --- | --- |
| 01 | `statement` | One claim the jury must remember, huge sentence with proof and source |
| 02 | `stats-visual` | Problem in three numbers around the object |
| 03 | `three-cards` | Why today's ways fail |
| 04 | `journey` | One role's day and the point where it breaks |
| 24 | `before-after` | The same case today and with the product |
| 100 | `iceberg` | Visible part of the work against the hidden part |
| 121 | `quote` | One user's words as the whole slide |
| 122 | `persona` | Who the user is, pains and what they get |
| 123 | `voices` | Three interview quotes, one shared pain |
| 135 | `big-number` | One giant number and what it means |
| 136 | `photo-full` | Full-bleed photo of the real place with a caption card |
| 143 | `zoom` | A document with the one wrong detail magnified |
| 149 | `cost-of-delay` | A clock and the money lost per day, counting up |
| 152 | `fishbone` | Six causes of one failure, the real one in red |
| 153 | `five-whys` | Five whys down to the root cause |
| 154 | `emotion-curve` | Customer journey as an emotion curve with the low point |
| 155 | `empathy-map` | What the user says, thinks, does and feels |
| 165 | `diff-table` | Two tables side by side with the mismatches |
| 181 | `callout-number` | One total split into its parts by callouts |
| 185 | `testimonial-metric` | Customer quote backed by a before and after bar |
| 187 | `jtbd` | Job to be done: when, I want, so that |

### Charts

| # | Layout | Chart | Use it for |
| --- | --- | --- | --- |
| 15 | `kpi-bars` | ranked bars | How much data, from where |
| 16 | `bars-table` | bars and example | Classifier or source confidence |
| 17 | `versus-bars` | paired bars | Faster or cheaper by N times |
| 18 | `line-chart` | hand-drawn line | Forecast against fact |
| 19 | `scatter` | points | Trade-off map, chosen option |
| 28 | `market` | nested rings | Market size |
| 35 | `column-peak` | `columns` | One period stands out, with a target line |
| 36 | `ranking` | `bars` | We are first in a ranking |
| 37 | `stacked-time` | `stacked` | Composition changing over time |
| 38 | `share-bars` | `share` | Shares by segment, 100% rows |
| 39 | `waterfall` | `waterfall` | Where a total comes from, item by item |
| 40 | `lollipop` | `lollipop` | One cause dominates |
| 41 | `dumbbell` | `dumbbell` | Before and after per item |
| 42 | `bullet` | `bullet` | Fact against target per metric |
| 43 | `histogram` | `histogram` | Distribution with p50 and p95 marks |
| 44 | `lines-compare` | `line` | We grow, others stay flat |
| 45 | `area-growth` | `line` with `area` and `marks` | Growth with release milestones |
| 46 | `slope` | `slope` | Every group moved between two moments |
| 47 | `spark-kpis` | `spark` | Four metric cards with trends |
| 48 | `step-line` | `line` with `step` | Thresholds that change in steps |
| 49 | `clusters` | `scatter` with groups | Segments found in data |
| 50 | `bubbles` | `scatter` with sizes | Market map with sizes |
| 51 | `strip` | `strip` | Spread of individual cases, before and after |
| 52 | `boxplot` | `boxplot` | Distributions of versions |
| 53 | `candles` | `candles` | Price action for trading products |
| 54 | `donut` | `donut` with legend | Where time or money goes |
| 55 | `gauge` | `gauge` | One value against a threshold |
| 56 | `rings` | `rings` | Progress of three goals |
| 57 | `radar` | `radar` | Capabilities against analogues |
| 58 | `polar-bars` | `polar` | Load by hour of day |
| 59 | `heatmap` | `heatmap` | Day by hour intensity |
| 61 | `cohorts` | `heatmap` with values | Retention by cohort |
| 62 | `waffle` | `waffle` | Share out of 100 |
| 63 | `unit-dots` | `dots` | One in a thousand |
| 64 | `pictogram` | `pictogram` | N people out of ten |
| 65 | `calendar` | `calendar` | Activity every day |
| 66 | `treemap` | `treemap` | Budget or composition by area |
| 67 | `sankey` | `sankey` | Where requests or money flow |
| 68 | `conversion` | `funnel` | Conversion funnel with step rates |
| 69 | `gantt` | `gantt` | Pilot plan in weeks |
| 72 | `pareto` | `pareto` | Few causes, most losses |
| 73 | `big-trend` | `spark` behind a number | One number with its trend |
| 74 | `forecast-band` | `band` | Forecast with an error corridor |
| 75 | `small-multiples` | six `spark` | Same trend in six groups |
| 76 | `diverging` | `diverging` | Praise against complaints |
| 80 | `cost-stack` | `stacked` | Cost per request by part |
| 117 | `dashboard` | `columns` and `donut` | A product dashboard rebuilt in the deck |
| 133 | `market-bars` | bars | TAM, SAM, SOM as lengths |
| 166 | `price-chart` | `line` with marks | Price curve with buy and now marks, KPI panel |
| 167 | `growth-chart` | `columns` | Monthly growth with the multiplier |
| 168 | `retention-curve` | `line` | Retention against the market, plateau zone |
| 169 | `cumulative-savings` | `line` | Savings that accumulate, payback mark |
| 170 | `heat-week` | `heatmap` | Errors by weekday and hour, hottest cell marked |
| 171 | `share-donuts` | `donut` | Three shares as three rings |
| 172 | `speedometers` | `gauge` | Manual against product on two gauges |
| 178 | `token-cost` | treemap blocks | Cost per request by part, margin below |
| 179 | `benchmark-bars` | `columns` | Us against analogues on three tasks |
| 180 | `radial-progress` | `donut` | Readiness of each module |
| 193 | `latency-breakdown` | segmented bar | Latency by stage with the target mark |
| 194 | `uptime-bar` | day bars | Uptime for a month with the one incident |

### Quality and evidence

| # | Layout | Use it for |
| --- | --- | --- |
| 14 | `kpi-grid` | Six results from the stand |
| 32 | `evidence-levels` | Stand, tests, in progress |
| 60 | `confusion` | Classifier confusion matrix |
| 70 | `roc` | ROC curve with AUC |
| 71 | `ab-test` | A/B test with confidence intervals |
| 77 | `benchmark` | Table with inline bars, best highlighted |
| 78 | `leaderboard` | Rank among teams or systems |
| 79 | `latency-slo` | p50, p90, p99 against an SLO line |
| 81 | `ablation` | Each component's contribution |
| 82 | `error-analysis` | Error categories with an example and a fix |
| 83 | `pr-curve` | Precision and recall with the chosen threshold |
| 84 | `percent-hero` | One share as a giant number and bar |
| 86 | `dataset-split` | Train, tune, test and how it was split |
| 87 | `kpi-hero` | One metric hero with three context numbers |
| 88 | `two-numbers` | Old number struck out, new number, multiplier |
| 90 | `versions` | Metric across versions with what changed |
| 119 | `checklist` | Requirements ticked, where each is shown |
| 120 | `criteria-map` | Jury criteria by weight mapped to slides |
| 139 | `limitations` | Limitation and what we do about it |
| 150 | `summary` | Three verified facts before the final |
| 160 | `weighted-score` | Options scored by weighted criteria |
| 183 | `versus-numbers` | Today and with the product, metric by metric |
| 188 | `hypothesis-board` | Hypotheses, how each was tested, verdict |
| 189 | `experiment-log` | Experiments over time with what changed |
| 192 | `eval-matrix` | Quality by input type and field |
| 195 | `security-checklist` | Shield and four data protection measures |
| 196 | `compliance` | Regulations as stamps, done and planned |
| 197 | `milestone-numbers` | Hackathon in numbers as a bento grid |

### Mechanism and architecture

| # | Layout | Use it for |
| --- | --- | --- |
| 05 | `pipeline` | How data flows through the product |
| 06 | `two-tracks` | One engine, two scenarios |
| 07 | `flowchart` | Answer only after a check, otherwise a refusal |
| 08 | `transform` | Messy input becomes structured data |
| 09 | `hub` | Orchestrator with agents |
| 10 | `boundary` | Closed loop, offline, on-prem |
| 11 | `lanes` | Who does what: human, model, code |
| 12 | `cycle` | Iterative loop |
| 13 | `formula` | The math, step by step |
| 21 | `reasoning` | Recommendation with justification |
| 29 | `stack` | Technologies and why each |
| 30 | `replaceable` | Ports and adapters |
| 85 | `data-sources` | Five sources merged into one base |
| 91 | `layers` | Architecture layers with the core highlighted |
| 92 | `sequence` | Sequence diagram of one request |
| 93 | `states` | State machine with a failure state |
| 94 | `decision-tree` | Questions that lead to an answer |
| 95 | `hierarchy` | Taxonomy or classes |
| 96 | `er-model` | Data model entities and relations |
| 97 | `knowledge-graph` | Network of entities with a risky link |
| 98 | `venn` | We sit in the intersection |
| 99 | `pyramid` | Value levels, where we are |
| 101 | `onion` | Security layers around the data |
| 102 | `honeycomb` | Feature map, ready and planned |
| 103 | `rag` | Retrieval, selection, answer with citations |
| 104 | `agent-trace` | Tool calls of an agent on a timeline |
| 105 | `orbit` | Integrations around the product |
| 108 | `kanban` | A task moving across the board by itself |
| 109 | `risk-matrix` | Risks by likelihood and impact |
| 110 | `balance` | Trade-off that tips one way |
| 144 | `queue` | Documents flowing through a check |
| 145 | `flywheel` | Growth loop |
| 146 | `wipe-compare` | Chaos wiped into a clean table |
| 158 | `metric-tree` | North star metric and its levers |
| 173 | `process-wheel` | Six-step cycle around one duration |
| 174 | `swimlane-time` | Participants on lanes along a time axis |
| 177 | `data-pipeline` | Data cleaning stages and where records went |
| 190 | `guardrails` | Model behind input, rule and human barriers |
| 191 | `prompt-anatomy` | What the model receives, by token share |

### Product and screens

| # | Layout | Use it for |
| --- | --- | --- |
| 22 | `screenshot` | Real screen with numbered pins |
| 23 | `chat` | Assistant dialogue with tool badges |
| 25 | `table` | Roles, inputs and outputs |
| 31 | `demo` | Live demo plan with plan B |
| 111 | `code-diff` | Forty lines replaced by one |
| 112 | `terminal` | One command brings up the stand |
| 113 | `api-call` | Request and response with the reason inside |
| 114 | `log-stream` | Logs with the caught anomaly |
| 115 | `phone` | Answer arrives in a messenger |
| 116 | `browser` | One screen with a cursor click |
| 118 | `alerts` | The system calls a human only when needed |
| 137 | `video-frame` | Backup recording, labelled as a recording |
| 138 | `try-it` | QR and three steps to try it now |
| 147 | `wizard` | Three screens to the result |
| 148 | `status-board` | Every service of the stand is up |
| 161 | `search-results` | Search box with ranked results and scores |
| 162 | `doc-highlight` | Document with fields highlighted by the model |
| 163 | `notification-stack` | Phone lock screen with product notifications |
| 164 | `form-autofill` | Scan turned into a filled form |

### People and team

| # | Layout | Use it for |
| --- | --- | --- |
| 33 | `team` | Four person cards |
| 124 | `team-grid` | Six people with roles |
| 125 | `team-photo` | Team photo with names |
| 126 | `team-skills` | People by skills matrix |
| 127 | `team-ownership` | Who owns which part of the product |
| 128 | `team-cards` | Three people, each with a measured result |
| 157 | `org-chart` | Who decides on the purchase, our champion |
| 186 | `logo-wall` | Customers as a logo wall with open slots |
| 200 | `thanks-contacts` | QR and team contacts after the defense |

### Business and plan

| # | Layout | Use it for |
| --- | --- | --- |
| 26 | `competitors` | Criteria matrix against analogues |
| 27 | `matrix-2x2` | Positioning quadrant |
| 34 | `roadmap` | From prototype to pilot |
| 89 | `goal-progress` | Progress bar to a goal with milestones |
| 106 | `timeline-vertical` | Hackathon hours or project history |
| 107 | `milestones` | Year in five points |
| 129 | `unit-economics` | LTV, CAC and payback as an equation |
| 130 | `pricing` | Three tiers, the middle one chosen |
| 131 | `business-model` | Who pays whom and for what |
| 132 | `go-to-market` | Channels in order |
| 140 | `asks` | Three things we need |
| 142 | `versus-split` | Them and us as two halves |
| 151 | `swot` | Strengths, weaknesses, opportunities, threats |
| 156 | `value-fit` | Each pain closed by a feature |
| 159 | `now-next-later` | Roadmap in three horizons |
| 175 | `comparison-cards` | Three ways to solve it, ours highlighted |
| 176 | `spectrum` | Position between two extremes |
| 182 | `progress-steps` | Maturity levels as a staircase |
| 184 | `map-regions` | Pilot cities on a map with counts |
| 198 | `next-steps` | Next four weeks, one row each |

### Structure

| # | Layout | Use it for |
| --- | --- | --- |
| 20 | `funnel-circles` | Many options, few pass, one chosen |
| 134 | `chapter` | Section divider in a long deck or appendix |
| 141 | `appendix-index` | Links to appendix slides for Q&A |
| 199 | `manifesto` | Two-line belief that closes the story |

## Chart engine

A chart is a `div` with `data-viz` and data attributes. The engine (`src/core/js/viz*.js`,
`src/core/css/viz*.css`) draws it as SVG at the element's size and animates it with the deck
classes, so `?static`, `?print` and reduced motion show the final frame.

```html
<div class="chart-box" data-viz="columns" data-from="weekly_load" data-labels="Пн;Вт;Ср;Чт;Пт" data-accent="4" data-unit=" ч"></div>
```

| Attribute | Meaning |
| --- | --- |
| `data-values` | Numbers separated by commas or spaces; series or rows separated by `\|`. In the library only: real decks use `data-from` |
| `data-from` | Key in `src/data/numbers.json` whose `value` is an array (a series) or an array of arrays (rows); the build fills `data-values` and checks the source |
| `data-labels` | Category labels separated by `;`, empty items allowed |
| `data-names` | Series or row names separated by `;` |
| `data-accent`, `data-danger` | Indexes of the highlighted items or series |
| `data-unit`, `data-digits` | Value formatting in the deck language |
| `data-min`, `data-max` | Fixed scale |
| `data-delay` | Start of the choreography in seconds |
| `data-no-ticks`, `data-no-values` | Hide the axis labels or the value labels |

| Type | Data | Extra attributes |
| --- | --- | --- |
| `columns` | one series or several | `data-target`, `data-target-label`, `data-gap`, `data-accent-values` (label only the accented series) |
| `bars`, `lollipop` | one series | `data-label-width` |
| `stacked` | one row per segment | |
| `share` | one row per category, parts sum to 100% | `data-rows` (rows to ring) |
| `waterfall` | start, changes, end | |
| `dumbbell` | two rows: before, after | the new dot slides from the old value |
| `bullet` | rows: actual, target, maximum | `data-goal-label` |
| `funnel`, `pareto`, `diverging`, `histogram` | one series | `data-marks="index:label;..."` on `histogram` |
| `line` | one series or several | `data-area`, `data-curve`, `data-step` (all, or indexes of stepped series), `data-diagonal`, `data-zone="from,to"`, `data-marks`, `data-point-values` |
| `band` | rows: fact, low, high, forecast | `data-now` |
| `slope` | two rows | |
| `spark` | one series | |
| `scatter` | rows `x y [size] [group]` | `data-xname`, `data-yname`, `data-xmin` and the other bounds, `data-accent-group`, `data-hulls` |
| `strip`, `boxplot`, `candles`, `interval` | rows of points, `min q1 median q3 max`, `open high low close`, `low mid high` | `data-mean-label` on `strip`, `data-marks` on `candles`, `data-ref` and `data-ref-label` on `interval` |
| `donut`, `gauge`, `rings`, `radar`, `polar` | one series or rows | `data-center`, `data-caption`, `data-legend`, `data-zones`, `data-target`, `data-target-label` |
| `heatmap`, `calendar` | rows of cells | `data-show-values`, `data-mark="row:col;..."`, `data-scale="low;high"` |
| `waffle`, `dots`, `pictogram` | counts | `data-total`, `data-cols`, `data-icon` |
| `treemap` | one series | |
| `sankey` | rows `source target value` | `data-cols` with the column of each node |
| `gantt` | rows `start end` | `data-now`, `data-now-label`, `data-durations` |
| `network` | rows `a b` (edges) | `data-center`, `data-seed`, `data-pos="x y\|..."` (0..1), `data-alert` (edge indexes) |

## Blocks

Shared classes in `src/core/css/blocks.css`, already styled in the product tokens. A custom slide
uses them before writing its own CSS; its `style.css` only positions and sizes.

| Block | Classes |
| --- | --- |
| Content area | `.body` (below the title, above the callout), `.body.is-tall`, `.foot` (callout row) |
| Layout | `.grid.is-2 / is-3 / is-4 / is-split / is-split-r / is-rows-2`, `.stack`, `.stack.is-center` |
| Surfaces | `.card`, `.card.is-accent`, `.card.is-sunken`, `.eyebrow` |
| Numbers | `.kpi`, `.kpi-value`, `.kpi-label`, `.kpi-note`, `.kpi.is-accent`, `.kpi.is-lg`, `.strike` |
| Bars | `.meter`, `.meter-row` (`is-ours`, `is-danger`), `.meter-track`, `.meter-fill` with `--w` from 0 to 1 |
| Process | `.steps` (`--tile` sets the circle size), `.flow`, `.dg` + `.dg-node` (`--x`, `--y`, `--w`, `--anchor`) |
| Tables | `.tbl`, `.tbl-row` (`is-head`, `is-ours`), `--cols` for the grid |
| Marks | `.badge` (`is-accent`, `is-success`, `is-warning`, `is-danger`), `.tile` (`is-accent`, `is-danger`), `.n`, `.pin`, `.legend` |
| Lists | `.list`, `.list.is-icons` |
| Media | `.screen` (`is-empty` placeholder) with an `img` or `video` from `src/img/` |
| Charts | `[data-viz]` above; hand-drawn `svg.chart` with `.axis`, `.grid-line`, `.zone`, `.dot` |
| Shared from `parts.css` | `.chips`, `.chip`, `.trace`, `.node`, `.ping`, `.runner`, `.limit`, `.proof`, `.qr` |

Icons: `<span class="ico" data-icon="name"></span>`, filled at runtime from `<template
id="deck-icons">` in `src/shell.html` (Lucide paths, ISC licence). Names: check, x, minus,
arrow-right, arrow-down, user, users, database, server, file, search, filter, sliders, shield,
lock, message, bot, cpu, layers, clock, zap, alert, target, trending, chart, refresh, globe, code,
play, monitor, flag, wallet, plug, eye, sparkle. A missing icon is added to the template with the
product's own path data (same set as the frontend `Icon`), never drawn as a glyph.

## Rules for every layout

- Light by default: the whole deck follows `<html data-theme>` in `src/shell.html`. No slide sets
  its own theme, no literal colors; the build fails on both.
- The title fits one line: at most 40 characters and 8 words, the build fails otherwise.
- No hidden steps: everything arrives in the entry choreography within 2.5 s, in speaking order,
  and a key press always changes the slide. The build fails on `data-steps`, `data-s`, `data-at`.
- Motion classes from skill `deck-motion` on every element (`.a`, `.f`, `.s`, `.pop`, `.w`, `.dr`,
  `.meter-fill` and charts grow by themselves). Slide-level keyframes use `#id.play .part`.
- Placeholders stay in `{{…}}` until real text and numbers replace them; numbers on the final deck
  go through `data-num` and `data-from` (`npm run build:final` fails otherwise).
- Text is captions to the visual: title, at most about 25 words more, nothing under 20 px.
