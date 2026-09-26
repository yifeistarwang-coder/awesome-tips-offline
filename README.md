# Awesome Tips [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of tips on various topics. **Every entry now links to locally archived, offline-readable content.**

- 中文版（Chinese）：[README-CN.md](README-CN.md)
- X/Twitter 完整串文归档：[threads/README.md](threads/README.md)（66 条 · 配图/GIF 本地化）
- 仓库正文中文整理：[中文离线阅读版.md](中文离线阅读版.md)
- 讲稿/幻灯片（Dropbox PPTX 已本地化）：[threads/slides/README.md](threads/slides/README.md)
- **静态网站**：`python3 scripts/build_site.py` 生成 `site/`（双语、离线搜索、可 `--serve` 预览）

## What is in here

| Path | Contents |
| --- | --- |
| [`threads/`](threads/README.md) | Full text of all 66 X/Twitter threads, one file per category. Every image, GIF and clip is stored locally in `threads/media/`; `t.co` links are expanded. |
| [`threads/zh/`](threads/zh/README.md) | Chinese translation of every thread. |
| [`threads/slides/`](threads/slides/README.md) | The two Dropbox decks (Harvard guest lecture, academic job workshop), extracted slide by slide. |
| Root `*.md` | The five long-form articles. [`中文离线阅读版.md`](中文离线阅读版.md) is their Chinese digest. |
| [`scripts/`](scripts) | The pipeline that produced all of the above. |

## Reading it

**Static site (recommended).** Bilingual, full-text search (`/` or `Cmd-K`), dark mode, clips autoplay while on screen:

```bash
python3 scripts/build_site.py            # writes site/
python3 scripts/build_site.py --serve    # ... and serves http://localhost:8000
```

It needs no network at all — no CDN, no web fonts, no tracking — so `site/index.html` also opens straight from `file://`.

**Plain Markdown.** Everything is readable as-is: start at [`threads/README.md`](threads/README.md) (English) or [`threads/zh/README.md`](threads/zh/README.md) (中文).

## Rebuilding the archive

```bash
python3 scripts/fetch_x_threads.py         # refresh threads + media from X (uses your browser session)
python3 scripts/prepare_zh_translation.py  # cut the text into translation batches
python3 scripts/render_x_threads_zh.py     # render the Chinese archive
python3 scripts/build_readmes.py           # regenerate README.md / README-CN.md from scripts/readme_index.json
python3 scripts/build_site.py              # regenerate the website
```

## Notes

- `threads/media/` holds 966 files (~251 MB). `site/media/` is hard-linked to it, so building the site costs almost no extra disk — but weigh that size before pushing the repository anywhere.
- `site/` is generated output and is gitignored; only the sources are tracked.
- The clips are muted H.264 conversions of the original GIFs. Autoplay stays the browser's decision: clips start once they are on screen, pause when they scroll away, and stay still when the OS asks for reduced motion.

## Contents

### Doing Research
- [How to make steady research progress?](steady-progress.md)
- [How to do experiments?](threads/doing-research.md#how-to-do-experiments)
- [How to get unstuck?](threads/doing-research.md#how-to-get-unstuck)
- [How to decide what to work on?](threads/doing-research.md#how-to-decide-what-to-work-on)
- [How to keep track of literature?](threads/doing-research.md#how-to-keep-track-of-literature)
- [How to come up with research ideas?](threads/doing-research.md#how-to-come-up-with-research-ideas)
- [How to cope with paper rejection?](threads/doing-research.md#how-to-cope-with-paper-rejection)
- [The Road to Becoming an AI Ninja (guest lecture at Harvard University)](threads/slides/ninja.en.md)
- [How to Drive Your Research Forward](threads/bsky-how-to-drive-your-research-forward.md)
- [How to Get Citations?](threads/doing-research.md#how-to-get-citations)

### Working with your mentors
- [How to share progress with your mentors/collaborators?](threads/working-with-your-mentors.md#how-to-share-progress-with-your-mentorscollaborators)
- [How to meet with your advisor?](threads/working-with-your-mentors.md#how-to-meet-with-your-advisor)
- [How to work with my mentors effectively?](working-with-mentor.md)
- [How to work with your advisor?](threads/working-with-your-mentors.md#how-to-work-with-your-advisor)
- [How to work with a busy advisor?](threads/working-with-your-mentors.md#how-to-work-with-a-busy-advisor)
- [How to work with your senior advisor?](threads/working-with-your-mentors.md#how-to-work-with-your-senior-advisor)

### Writing
- [How to write the Introduction?](threads/writing.md#how-to-write-the-introduction)
- [How to write the Related Work?](related-work.md)
- [How to write papers that are easy to read?](paper-writing.md)
- [How to write a paper that looks like a good one?](threads/writing.md#how-to-write-a-paper-that-looks-like-a-good-one)
- [How to write clear and concise sentences?](threads/writing.md#how-to-write-clear-and-concise-sentences)
- [How to draw an overview figure?](threads/writing.md#how-to-draw-an-overview-figure)
- [How to create a good table?](threads/writing.md#how-to-create-a-good-table)
- [How to write math in a paper?](threads/writing.md#how-to-write-math-in-a-paper)
- [How to prepare journal response letter?](threads/writing.md#how-to-prepare-journal-response-letter)
- [How to prepare supplementary material?](threads/writing.md#how-to-prepare-supplementary-material)
- [How to cite papers?](threads/writing.md#how-to-cite-papers)

### Presentation
- [How to start a presentation?](threads/presentation.md#how-to-start-a-presentation)
- [How to end a presentation?](threads/presentation.md#how-to-end-a-presentation)
- [How to handle questions in a presentation?](threads/presentation.md#how-to-handle-questions-in-a-presentation)
- [How to present a line plot?](threads/presentation.md#how-to-present-a-line-plot)
- [How to prepare your presentation slides?](threads/presentation.md#how-to-prepare-your-presentation-slides)
- [How to organize your talk?](threads/presentation.md#how-to-organize-your-talk)
- [How to design your presentation?](threads/presentation.md#how-to-design-your-presentation)
- [How to avoid common mistakes in your presentation?](threads/presentation.md#how-to-avoid-common-mistakes-in-your-presentation)
- [How to structure your talk with a story?](threads/presentation.md#how-to-structure-your-talk-with-a-story)

### Poster Presentation
- [How to make a research poster?](threads/poster-presentation.md#how-to-make-a-research-poster)
- [How to present a poster at a conference?](threads/poster-presentation.md#how-to-present-a-poster-at-a-conference)
- [How to revise an academic poster?](threads/poster-presentation.md#how-to-revise-an-academic-poster)

### Communication
- [How to present your work via videos?](threads/communication.md#how-to-present-your-work-via-videos)
- [How to disseminate your research?](threads/communication.md#how-to-disseminate-your-research)
- [How to ask research questions?](threads/communication.md#how-to-ask-research-questions)
- [How to make a research poster?](threads/poster-presentation.md#how-to-make-a-research-poster)（已收录于 Poster Presentation）
- [How to improve asynchronous communication?](threads/communication.md#how-to-improve-asynchronous-communication)
- [How to communicate clearly?](threads/communication.md#how-to-communicate-clearly)
- [How to set up a good calendar invite?](threads/communication.md#how-to-set-up-a-good-calendar-invite)
- [How to get remembered?](threads/communication.md#how-to-get-remembered)
- [How to schedule a meeting?](threads/communication.md#how-to-schedule-a-meeting)

### Career
- [How to prepare your Curriculum Vitae?](threads/career.md#how-to-prepare-your-curriculum-vitae)
- [How to find a research internship?](threads/career.md#how-to-find-a-research-internship)
- [How to intern?](threads/career.md#how-to-intern)
- [How to find research opportunities?](threads/career.md#how-to-find-research-opportunities)
- [How to prepare for a graduate school interview?](threads/career.md#how-to-prepare-for-a-graduate-school-interview)
- [How to improve graduate application after submission?](threads/career.md#how-to-improve-graduate-application-after-submission)
- [How do I maximize my chance for PhD programs?](threads/career.md#how-do-i-maximize-my-chance-for-phd-programs)
- [How to ask for a letter of recommendation?](threads/career.md#how-to-ask-for-a-letter-of-recommendation)
- [How to survive the first year of PhD?](threads/career.md#how-to-survive-the-first-year-of-phd)
- [How to prepare a phone interview for faculty positions?](threads/career.md#how-to-prepare-a-phone-interview-for-faculty-positions)
- [How to get a tenure-track faculty job?](threads/career.md#how-to-get-a-tenure-track-faculty-job)
- [How to email faculty as a prospective student?](threads/career.md#how-to-email-faculty-as-a-prospective-student)
- [Fantastic Faculty Jobs and How to Get Them?](threads/slides/faculty.en.md)
- [How to find a good PhD advisor?](threads/career.md#how-to-find-a-good-phd-advisor)
- [How to write an email to a potential advisor?](threads/career.md#how-to-write-an-email-to-a-potential-advisor)
- [How to invite yourself to give a talk?](threads/career.md#how-to-invite-yourself-to-give-a-talk)
- [How to get people to know you?](threads/career.md#how-to-get-people-to-know-you)
- [How to schedule your defense?](threads/career.md#how-to-schedule-your-defense)

### Productivity
- [How to manage your time?](threads/productivity.md#how-to-manage-your-time)
- [How to be productive?](threads/productivity.md#how-to-manage-your-time)（已收录于 Productivity）
- [How to develop a productive routine?](threads/productivity.md#how-to-develop-a-productive-routine)
- [How to multitask?](threads/productivity.md#how-to-multitask)
- [How to know when to stop working on a project?](threads/productivity.md#how-to-know-when-to-stop-working-on-a-project)

### Networking
- [How to network in a in-person conference?](threads/networking.md#how-to-network-in-a-in-person-conference)
- [How to network in a virtual conference?](threads/networking.md#how-to-network-in-a-virtual-conference)
- [How to write good cold emails?](cold-emails.md)
- [How do I get professors to answer my emails?](threads/networking.md#how-do-i-get-professors-to-answer-my-emails)

### Financial
- [How to save for retirement as a graduate student (in the US)?](threads/financial.md#how-to-save-for-retirement-as-a-graduate-student-in-the-us)
