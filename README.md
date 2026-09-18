# Singapore English · Ethan

[Open the learning website](https://ethanldr.github.io/learn-sg-english/) · [Latest initialized lesson: Day 21](https://ethanldr.github.io/learn-sg-english/#day-21) · [Build and deployment runs](https://github.com/EthanLDR/learn-sg-english/actions)

A complete, searchable archive of daily 40-minute English-speaking lessons for work and everyday life in Singapore. English practice with concise Chinese explanations.

## Verified deployment — 2026-09-18

The first complete site is live. The cloud connection committed the site; GitHub Actions built and published it. Workflow [35324013344](https://github.com/EthanLDR/learn-sg-english/actions/runs/35324013344) completed successfully for commit `2ab1b802bea073fe04104888470e94c58cc601eb`.

The post-deployment HTTP test returned **200** for both the public homepage and `manifest.json`, confirmed the deployed commit, **21 complete lessons**, and the `#day-21` anchor. The earlier authorization failures and missing-site setup state are obsolete.

The build contains Day 1–21, 77 historical practice messages, original errata and setup notes. Desktop/mobile browser tests on the downloaded build passed: lesson counts, daily anchors, search, expanding a closed lesson from a search result, review cards, progress marking and dark mode. Browser/system support determines whether speech synthesis works.

## Source layout

```text
lessons/day-001.md ... day-021.md  Complete lesson source, never summaries
archive/live-review.md             Original 77-message practice transcript
archive/errata.md                  Original corrections and clarifications
archive/setup.md                   Original course settings and archive notes
content-lock.json                 Exact historical Git blob hashes
site-config.json                  Repository, minimum count and display titles
site/template.html                Accessible page layout
site/style.css                    Responsive and print styles
site/app.js                       Search, anchors, progress and reading tools
scripts/build.py                  Render, preserve and validate all content
.github/workflows/pages.yml       Build, deploy and verify live site
_site/                            Generated output; not edited by hand
```

The deployed `index.html` contains the full text, styles and interaction code. Every lesson has a stable `#day-NN` anchor. The website also offers original Markdown downloads under `sources/`, a review-card overview, full-text search, local browser progress, font controls, dark mode and optional selected-text speech. The HTML can be saved for offline reading; linked Markdown files and the deployment manifest are separate resources.

## Daily cloud update procedure

The existing ChatGPT task is scheduled for **09:00 Asia/Singapore**. Lesson generation occurs in that task; GitHub Actions only builds and publishes committed content. No company-computer `git push` is required.

1. Read the current default branch, README, `site-config.json` and lesson directory before writing.
2. Check dates in recent lesson files. If the Singapore date already exists, reuse that exact full lesson rather than creating a duplicate.
3. Add only the next complete lesson, such as `lessons/day-022.md`, with this format:

   ```markdown
   <!-- lesson-date: YYYY-MM-DD -->
   # Day 22 | A meaningful new speaking topic
   ...the exact complete lesson delivered in chat...
   ```

4. Commit using the authorized GitHub connection. A push affecting lesson/site/build files on `main` automatically triggers `pages.yml`.
5. Inspect that commit's workflow run. Success includes source preservation, complete rendering, Pages deployment, live HTTP 200, manifest commit verification and the latest daily anchor.
6. Report generated, committed, built and deployed status accurately. A pending/failed run or permission prompt is not a successful publication.

The next scheduled daily-generation-and-write run has not yet been observed as part of this setup. The cloud commit → build → deploy → live-verification path has been executed successfully. Do not confuse these two claims.

## Content preservation and privacy

Historical lessons are kept in full, including repeated exercises. `content-lock.json` prevents accidental deletion or modification of the 21 initial lessons and three appendices. Do not edit the lock to bypass a failure; add corrections separately or obtain explicit approval for a historical revision. Future lesson numbers must be consecutive and dates unique. Do not fabricate dates for undated older lessons.

This repository and site are public, not a private notebook. Only the English-learning archive explicitly requested for publication belongs here. Do not add unrelated personal/company data, credentials or new private practice transcripts. The page asks search engines not to index it, but that is not access control. Search and review state remain in the visitor's browser; they are not sent to an analytics service or synchronized across devices.

## Build and troubleshooting

The cloud workflow installs the pinned dependencies in `requirements.txt` and runs:

```sh
python scripts/build.py
```

It checks all historical source hashes, required appendices, numbering, dates, render-text preservation, unique/broken anchors and exact source-file copies. `_site/manifest.json` records the source commit, lesson dates and content hashes.

Pages is configured to use **GitHub Actions**. Do not switch to a Jekyll or branch-publishing template. The workflow has a manual Run workflow option for authorized maintenance, but normal lesson commits deploy automatically. A failed build does not replace the last successfully published site. Read the failing job logs before changing permissions or source content.
