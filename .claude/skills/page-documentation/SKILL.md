---
name: page-documentation
description: Write or update plain-English markdown documentation for a Streamlit page in docs/, plus reusable widget docs in docs/widgets/. Use whenever a UI page is added or edited.
---

# Page Documentation

Write for a beginner who wants to understand how the page works. Use plain English, short sentences, no unexplained jargon.

## 1. Page doc: `docs/<page_name>_page.md`
(for example `docs/exercises_page.md`) with these sections:

1. `# <Page Name> Page`
2. **File:** path of the page's source file.
3. `## What you see`: what the user sees and can do on the page.
4. `## How it works`: a short numbered list of what happens, in order. Put the real code snippet for each step directly under it (a fenced `python` block copied from the source, trimmed to the relevant lines).
5. `## Widgets used`: a bullet per Streamlit widget or element, linking to its widget doc, with one sentence on how this page uses it, for example: `[st.dataframe](widgets/st_dataframe.md): shows the exercise table`.
6. `## Core functions`: each important function used, as `name` (file): one sentence on what it does, plus a short snippet of how it is called. Include helpers like database functions.
7. `## Database tables used` (only if any): table names and what is read or written.

## 2. Widget docs: `docs/widgets/<st_widget_name>.md`
One file per Streamlit widget or element (`st.dataframe` becomes `st_dataframe.md`). They are shared across pages.

- Before documenting a widget, check whether its file already exists. If it does, **link to it and do not duplicate it**. Only add to it if this page uses a parameter the doc does not cover yet.
- If it does not exist, create it with:
  1. `# st.<widget>`
  2. One or two plain sentences on what it does.
  3. `## Basic example`: a minimal snippet.
  4. `## Parameters`: a table of only the parameters we actually use or are likely to use (`Parameter | What it does | Default`). Verify against the installed Streamlit version (`uv run python -c "import streamlit as st; help(st.<widget>)"`). Do not guess.
  5. `## Used in`: links to the page docs that use it. Add a link here whenever a new page uses the widget.
- Add the widget to the table in `docs/widgets/README.md`.

## Rules
- Update existing docs when a page changes. Do not leave stale docs or stale snippets.
- Snippets must match the source code. Never invent code.
- Describe behaviour, not line-by-line code.
- Keep each page doc to about one or two screens.
