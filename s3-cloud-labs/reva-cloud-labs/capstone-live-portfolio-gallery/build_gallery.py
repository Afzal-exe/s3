#!/usr/bin/env python3
"""
build_gallery.py - turn a PRIVATE S3 bucket into a gallery page on your website.

What it does, every time it runs:
  1. Lists the images in your S3 gallery bucket (using the EC2 instance's IAM role,
     so there are NO passwords or access keys anywhere).
  2. Downloads new or changed images into  <webroot>/gallery/
  3. Reads each image's metadata (x-amz-meta-title, x-amz-meta-description).
  4. Writes <webroot>/gallery.html with one album per folder.
  5. Removes local copies of images that were deleted from the bucket.

Folders listed in --exclude (default: Family/) are NEVER downloaded or published.

Usage:
  sudo python3 build_gallery.py --bucket r23bsc042-image-gallery
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
import tempfile
from urllib.parse import quote

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
except ImportError:
    sys.exit("❌ boto3 is not installed. Run:  sudo apt install -y python3-boto3")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALBUM_ORDER = ["Nature", "Events", "Travel", "Family"]
ALBUM_ICONS = {"Nature": "🌿", "Events": "🎉", "Travel": "✈️", "Family": "🏠"}


def parse_args():
    p = argparse.ArgumentParser(description="Build gallery.html from a private S3 bucket")
    p.add_argument("--bucket", required=True, help="Name of your S3 gallery bucket")
    p.add_argument("--region", default="ap-south-1", help="AWS region (default: ap-south-1)")
    p.add_argument("--webroot", default="/var/www/html", help="Apache document root")
    p.add_argument("--exclude", default="Family/",
                   help="Comma-separated folders to keep private (default: Family/)")
    return p.parse_args()


def pretty_name(key):
    """'Nature/mountain-dawn.jpg' -> 'Mountain Dawn'"""
    stem = os.path.splitext(os.path.basename(key))[0]
    return re.sub(r"[-_]+", " ", stem).strip().title() or key


def owner_name(webroot):
    """Read the name the student put into index.html (<meta name="author" ...>)."""
    try:
        with open(os.path.join(webroot, "index.html"), encoding="utf-8") as f:
            m = re.search(r'<meta name="author" content="([^"]*)"', f.read())
            if m and "{{" not in m.group(1):
                return html.unescape(m.group(1))
    except OSError:
        pass
    return "My"


def safe_local_path(gallery_dir, key):
    """Map an S3 key to a file inside gallery_dir, refusing anything that escapes it."""
    target = os.path.realpath(os.path.join(gallery_dir, key))
    if not target.startswith(os.path.realpath(gallery_dir) + os.sep):
        return None
    return target


def list_images(s3, bucket, excluded):
    images = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue  # a "folder" placeholder
            if os.path.splitext(key)[1].lower() not in IMAGE_EXTENSIONS:
                continue
            if any(key.startswith(prefix) for prefix in excluded):
                continue
            images.append({
                "key": key,
                "etag": obj["ETag"].strip('"'),
                "modified": obj["LastModified"].isoformat(),
                "size": obj["Size"],
            })
    return images


def render_page(owner, albums, bucket, excluded, total):
    now = datetime.datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    who = "My" if owner == "My" else f"{owner}'s"
    e = html.escape

    filter_links = "".join(
        f'<a class="chip" href="#{e(name.lower())}">{ALBUM_ICONS.get(name, "📁")} {e(name)} ({len(items)})</a>'
        for name, items in albums
    )

    sections, lightboxes = [], []
    n = 0
    for name, items in albums:
        cards = []
        for item in items:
            n += 1
            src = "gallery/" + quote(item["key"])
            title, desc = e(item["title"]), e(item["description"])
            cards.append(
                f'<figure class="photo"><a href="#p{n}"><img src="{src}" alt="{title}" loading="lazy"></a>'
                f'<figcaption><b>{title}</b><span>{desc}</span></figcaption></figure>'
            )
            lightboxes.append(
                f'<div class="lightbox" id="p{n}"><a class="close" href="#{e(name.lower())}" aria-label="Close">✕</a>'
                f'<img src="{src}" alt="{title}"><p><b>{title}</b>{" · " + desc if desc else ""}</p></div>'
            )
        sections.append(
            f'<section class="section album" id="{e(name.lower())}">'
            f'<h2>{ALBUM_ICONS.get(name, "📁")} {e(name)} <small>{len(items)} photo{"s" if len(items) != 1 else ""}</small></h2>'
            f'<div class="photos">{"".join(cards)}</div></section>'
        )

    if not sections:
        sections.append(
            '<section class="section locked"><div class="lock-icon">📭</div>'
            '<h1>No photos yet</h1><p>Upload images to your S3 gallery bucket. They will appear here automatically.</p></section>'
        )

    private = ", ".join(e(x.rstrip("/")) for x in excluded) or "none"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="120">
  <title>{e(who)} Gallery</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <nav class="nav">
    <a class="brand" href="index.html">{e(owner if owner != "My" else "Home")}</a>
    <div class="nav-links">
      <a href="index.html#about">About</a>
      <a href="index.html#skills">Skills</a>
      <a href="index.html#projects">Projects</a>
      <a href="gallery.html">Gallery</a>
    </div>
  </nav>
  <header class="section gallery-head">
    <h1>📷 {e(who)} <span class="accent">Cloud Gallery</span></h1>
    <p>{total} photos, served live from a private Amazon S3 bucket</p>
    <div class="filter">{filter_links}</div>
  </header>
  <main>
    {"".join(sections)}
  </main>
  {"".join(lightboxes)}
  <p class="sync-note">🔄 Last synced from <code>s3://{e(bucket)}</code> at {now} · 🔒 Private albums not published: {private}</p>
  <footer class="footer">
    <p>⚡ Apache on AWS EC2 · 🪣 Photos from Amazon S3 via an IAM role · no passwords stored anywhere</p>
  </footer>
</body>
</html>
"""


def main():
    args = parse_args()
    excluded = [x.strip().strip("/") + "/" for x in args.exclude.split(",") if x.strip()]
    gallery_dir = os.path.join(args.webroot, "gallery")
    manifest_path = os.path.join(gallery_dir, ".manifest.json")
    os.makedirs(gallery_dir, exist_ok=True)

    s3 = boto3.client("s3", region_name=args.region)

    try:
        images = list_images(s3, args.bucket, excluded)
    except NoCredentialsError:
        sys.exit("❌ No AWS credentials found. Attach the IAM role to this EC2 instance "
                 "(EC2 → Actions → Security → Modify IAM role), wait 10 seconds, and run again.")
    except EndpointConnectionError:
        sys.exit("❌ Cannot reach S3. Check the --region value and the instance's internet access.")
    except ClientError as err:
        code = err.response["Error"]["Code"]
        if code in ("AccessDenied", "403"):
            sys.exit(f"❌ AccessDenied listing '{args.bucket}'. Check that the IAM policy names "
                     "this exact bucket, and that the role is attached to this instance.")
        if code == "NoSuchBucket":
            sys.exit(f"❌ Bucket '{args.bucket}' does not exist. Check the spelling (S3 → Buckets).")
        sys.exit(f"❌ S3 error: {code}: {err}")

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        manifest = {}

    downloaded, new_manifest = 0, {}
    for img in images:
        key = img["key"]
        local = safe_local_path(gallery_dir, key)
        if local is None:
            print(f"⚠️  Skipping unsafe key: {key}")
            continue
        cached = manifest.get(key, {})
        unchanged = (cached.get("etag") == img["etag"] and cached.get("modified") == img["modified"]
                     and os.path.exists(local))
        if unchanged:
            img["title"], img["description"] = cached["title"], cached["description"]
        else:
            try:
                meta = s3.head_object(Bucket=args.bucket, Key=key).get("Metadata", {})
                os.makedirs(os.path.dirname(local), exist_ok=True)
                fd, tmp = tempfile.mkstemp(dir=os.path.dirname(local))
                os.close(fd)
                s3.download_file(args.bucket, key, tmp)
                os.chmod(tmp, 0o644)
                os.replace(tmp, local)
            except ClientError as err:
                print(f"⚠️  Could not fetch {key}: {err.response['Error']['Code']}")
                continue
            img["title"] = meta.get("title") or pretty_name(key)
            img["description"] = meta.get("description", "")
            downloaded += 1
            print(f"⬇️  {key}  ·  {img['title']}")
        new_manifest[key] = {k: img[k] for k in ("etag", "modified", "title", "description")}

    # Remove local copies of images that are gone from S3 (or are now excluded)
    removed = 0
    for key in set(manifest) - set(new_manifest):
        local = safe_local_path(gallery_dir, key)
        if local and os.path.exists(local):
            os.remove(local)
            removed += 1
            print(f"🗑️  removed {key}")

    # Group into albums by top-level folder
    groups = {}
    for img in images:
        if img["key"] not in new_manifest:
            continue
        album = img["key"].split("/", 1)[0] if "/" in img["key"] else "Unsorted"
        groups.setdefault(album, []).append(img)
    order = [a for a in ALBUM_ORDER if a in groups] + sorted(a for a in groups if a not in ALBUM_ORDER)
    albums = [(a, sorted(groups[a], key=lambda i: i["modified"], reverse=True)) for a in order]

    page = render_page(owner_name(args.webroot), albums, args.bucket, excluded, len(new_manifest))
    for path, content in ((os.path.join(args.webroot, "gallery.html"), page),
                          (manifest_path, json.dumps(new_manifest, indent=2))):
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)

    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"✅ [{stamp}] {len(new_manifest)} photos published "
          f"({downloaded} downloaded, {removed} removed) → {args.webroot}/gallery.html")


if __name__ == "__main__":
    main()
