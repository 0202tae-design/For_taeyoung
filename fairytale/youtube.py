"""Upload rendered videos to YouTube via the Data API v3 (no extra dependencies).

Needs these environment variables (see README):
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

  python3 youtube.py auth-url                 # step 1: open the printed URL and approve
  python3 youtube.py exchange "<redirect URL or code>"   # step 2: prints the refresh token
  python3 youtube.py upload out/001_..._ko.json [--privacy private|unlisted|public] [--publish-at ISO8601]
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

REDIRECT = "http://localhost"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl"


def _post(url, data=None, headers=None, body=None, method="POST"):
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded", **(headers or {})}
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        return urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url.split('?')[0]}: {e.read().decode(errors='replace')}")


def auth_url():
    q = {
        "client_id": os.environ["YT_CLIENT_ID"],
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    print("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q))


def exchange(code_or_url):
    if code_or_url.startswith("http"):
        code_or_url = urllib.parse.parse_qs(urllib.parse.urlparse(code_or_url).query)["code"][0]
    r = _post("https://oauth2.googleapis.com/token", data={
        "code": code_or_url,
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    })
    tok = json.load(r)
    print("YT_REFRESH_TOKEN=" + tok["refresh_token"])


def access_token():
    r = _post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    return json.load(r)["access_token"]


def upload(meta_path, privacy="private", publish_at=None, playlist=None):
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    base = os.path.dirname(os.path.abspath(meta_path))

    def local(p):
        return p if os.path.isabs(p) and os.path.exists(p) else os.path.join(base, os.path.basename(p))

    token = access_token()
    auth = {"Authorization": "Bearer " + token}
    status = {
        "privacyStatus": "private" if publish_at else privacy,
        "selfDeclaredMadeForKids": meta.get("madeForKids", True),
        "embeddable": True,
        "containsSyntheticMedia": meta.get("containsSyntheticMedia", False),
    }
    if publish_at:
        status["publishAt"] = publish_at
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta.get("categoryId", "1"),
            "defaultLanguage": meta["defaultLanguage"],
            "defaultAudioLanguage": meta["defaultAudioLanguage"],
        },
        "status": status,
    }
    video_path = local(meta["video"])
    size = os.path.getsize(video_path)
    r = _post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        body=json.dumps(body).encode(),
        headers={**auth, "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
    )
    session = r.headers["Location"]
    with open(video_path, "rb") as f:
        r = _post(session, body=f.read(), headers={**auth, "Content-Type": "video/mp4"}, method="PUT")
    video = json.load(r)
    vid = video["id"]
    print(f"uploaded: https://youtu.be/{vid} ({status['privacyStatus']})")

    thumb = local(meta.get("thumbnail", ""))
    if thumb and os.path.exists(thumb):
        with open(thumb, "rb") as f:
            _post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                  body=f.read(), headers={**auth, "Content-Type": "image/jpeg"})
        print("thumbnail set")

    caps = local(meta.get("captions", ""))
    if caps and os.path.exists(caps):
        boundary = "fairytale-caption-boundary"
        part_meta = json.dumps({"snippet": {"videoId": vid, "language": meta["defaultLanguage"],
                                            "name": meta["defaultLanguage"]}})
        with open(caps, "rb") as f:
            payload = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{part_meta}\r\n"
                       f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + f.read() + \
                      f"\r\n--{boundary}--".encode()
        _post("https://www.googleapis.com/upload/youtube/v3/captions?uploadType=multipart&part=snippet",
              body=payload, headers={**auth, "Content-Type": f"multipart/related; boundary={boundary}"})
        print("captions uploaded")

    if playlist:
        _post("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
              body=json.dumps({"snippet": {"playlistId": playlist,
                                           "resourceId": {"kind": "youtube#video", "videoId": vid}}}).encode(),
              headers={**auth, "Content-Type": "application/json"})
        print("added to playlist")
    return vid


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth-url")
    ex = sub.add_parser("exchange")
    ex.add_argument("code")
    up = sub.add_parser("upload")
    up.add_argument("meta")
    up.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    up.add_argument("--publish-at")
    up.add_argument("--playlist")
    a = ap.parse_args()
    if a.cmd == "auth-url":
        auth_url()
    elif a.cmd == "exchange":
        exchange(a.code)
    else:
        upload(a.meta, a.privacy, a.publish_at, a.playlist)


if __name__ == "__main__":
    main()
