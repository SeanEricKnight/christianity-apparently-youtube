# Christianity, apparently — YouTube

Working metadata and SEO-notes repo for the YouTube channel:

https://www.youtube.com/@ChristianityApparently

Website:

https://christianityapparently.com

## Purpose

This repo preserves channel copy, video metadata, scripts, SEO notes, and future revisions separately from the Christianity, apparently website code.

## Not a backup

An automated weekly metadata backup (`scripts/backup_youtube.py`, run by a GitHub Actions workflow) was **retired on 2026-10-08**. Every run had failed because YouTube blocked automated requests from GitHub's servers, and it never produced a snapshot. The script and `requirements.txt` are kept for reference only; nothing runs them. Channel metadata is recorded separately by a private collector that is not in this repo. This repo is **not** an independent backup of the channel.

## Historical baseline

The original pre-SEO snapshot is preserved in:

- `BASELINE-2026-10-02.md`

Do not rewrite that file when the live channel changes. It is the historical “before” record.

## Working files

- `channel.md` — current recommended channel profile copy and keywords
- `videos.csv` — video-title inventory and working SEO notes
- `seo-notes.md` — channel SEO rules and priorities
- `scripts/` — finalized scripts as they are preserved
- `assets/` — channel artwork / thumbnails when added
