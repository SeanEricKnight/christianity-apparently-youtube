#!/usr/bin/env python3
"""
Back up public metadata for the Christianity, apparently YouTube channel.

Uses yt-dlp (no YouTube API key required) to:
- enumerate videos + Shorts
- fetch detailed public metadata for each video
- write raw JSON plus readable Markdown/CSV snapshots

This intentionally backs up public metadata only. Private Studio-only analytics,
comments moderation state, drafts, permissions, and unpublished videos are not exposed.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL

CHANNEL_HANDLE = "ChristianityApparently"
CHANNEL_URL = f"https://www.youtube.com/@{CHANNEL_HANDLE}"
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = ROOT / "snapshots"


def clean(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False)


def ydl(opts=None):
    base = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "socket_timeout": 30,
        "retries": 3,
    }
    if opts:
        base.update(opts)
    return YoutubeDL(base)


def collect_ids(tab_url: str) -> set[str]:
    ids: set[str] = set()
    with ydl({"extract_flat": True}) as client:
        info = client.extract_info(tab_url, download=False)
    if not info:
        return ids
    for entry in info.get("entries") or []:
        if not entry:
            continue
        vid = entry.get("id")
        if vid:
            ids.add(vid)
    return ids


def fetch_video(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with ydl() as client:
        info = client.extract_info(url, download=False)
    return info or {}


def pick_channel_metadata(videos: list[dict]) -> dict:
    first = next((v for v in videos if v), {})
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "handle": f"@{CHANNEL_HANDLE}",
        "url": CHANNEL_URL,
        "channel_id": first.get("channel_id"),
        "channel": first.get("channel"),
        "channel_url": first.get("channel_url"),
        "channel_follower_count": first.get("channel_follower_count"),
        "uploader": first.get("uploader"),
        "uploader_id": first.get("uploader_id"),
        "uploader_url": first.get("uploader_url"),
        "video_count_captured": len(videos),
    }


def slim_video(info: dict) -> dict:
    keys = [
        "id", "title", "description", "channel", "channel_id", "channel_url",
        "uploader", "uploader_id", "uploader_url", "upload_date", "timestamp",
        "release_timestamp", "duration", "view_count", "like_count",
        "comment_count", "availability", "live_status", "webpage_url",
        "original_url", "thumbnail", "tags", "categories",
        "channel_follower_count", "age_limit", "language",
    ]
    return {k: info.get(k) for k in keys}


def write_csv(path: Path, videos: list[dict]) -> None:
    fields = [
        "video_id", "title", "upload_date", "duration_seconds", "view_count",
        "like_count", "comment_count", "description", "tags", "categories",
        "webpage_url",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for v in videos:
            writer.writerow({
                "video_id": v.get("id", ""),
                "title": v.get("title", ""),
                "upload_date": v.get("upload_date", ""),
                "duration_seconds": v.get("duration", ""),
                "view_count": v.get("view_count", ""),
                "like_count": v.get("like_count", ""),
                "comment_count": v.get("comment_count", ""),
                "description": v.get("description", ""),
                "tags": "; ".join(v.get("tags") or []),
                "categories": "; ".join(v.get("categories") or []),
                "webpage_url": v.get("webpage_url", ""),
            })


def write_channel_md(path: Path, channel: dict, videos: list[dict]) -> None:
    lines = [
        "# Christianity, apparently — public YouTube snapshot",
        "",
        f"Captured: {channel['captured_at']}",
        "",
        "## Channel",
        "",
        f"- Handle: {channel.get('handle') or ''}",
        f"- Channel ID: {channel.get('channel_id') or ''}",
        f"- Channel name: {channel.get('channel') or ''}",
        f"- URL: {channel.get('channel_url') or channel.get('url') or ''}",
        f"- Public follower count reported by extractor: {channel.get('channel_follower_count') or ''}",
        f"- Public videos captured: {len(videos)}",
        "",
        "## Videos",
        "",
    ]
    for v in sorted(videos, key=lambda x: x.get("upload_date") or "", reverse=True):
        title = (v.get("title") or "(untitled)").replace("\n", " ")
        lines.append(f"- **{title}** — {v.get('id') or ''} — {v.get('upload_date') or ''}")
    lines += [
        "",
        "## Notes",
        "",
        "This snapshot contains public metadata returned by YouTube through yt-dlp.",
        "It does not contain private YouTube Studio analytics, unpublished videos, or account permissions.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    out = SNAPSHOT_ROOT / today
    out.mkdir(parents=True, exist_ok=True)

    video_ids = set()
    for tab in ("videos", "shorts"):
        video_ids |= collect_ids(f"{CHANNEL_URL}/{tab}")

    if not video_ids:
        print("No public videos found. Refusing to write an empty snapshot.", file=sys.stderr)
        return 2

    videos = []
    for i, video_id in enumerate(sorted(video_ids), start=1):
        print(f"[{i}/{len(video_ids)}] {video_id}")
        info = fetch_video(video_id)
        if info:
            videos.append(slim_video(info))

    if not videos:
        print("Video IDs were found, but detailed metadata could not be fetched.", file=sys.stderr)
        return 3

    videos.sort(key=lambda x: (x.get("upload_date") or "", x.get("id") or ""))
    channel = pick_channel_metadata(videos)

    (out / "channel.json").write_text(
        json.dumps(channel, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out / "videos.json").write_text(
        json.dumps(videos, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_csv(out / "videos.csv", videos)
    write_channel_md(out / "channel.md", channel, videos)

    latest = SNAPSHOT_ROOT / "latest.json"
    latest.write_text(
        json.dumps(
            {
                "captured_at": channel["captured_at"],
                "snapshot": today,
                "channel_id": channel.get("channel_id"),
                "video_count": len(videos),
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"Captured {len(videos)} public videos into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
