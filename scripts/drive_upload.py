"""Upload a finished edit to the 1001 Clips Drive folder through Dylan's Apps Script web app (Windows/macOS/Linux, stdlib only).
usage: python drive_upload.py FILE [NAME]
needs HYPE_UPLOAD_KEY (the script's SECRET) in the environment; HYPE_UPLOAD_URL defaults to Dylan's web app.
Finals only: never upload previews or v1..vN review cuts."""
import json, os, sys, urllib.request
URL = os.environ.get("HYPE_UPLOAD_URL", "https://script.google.com/macros/s/AKfycbxnQKMIk9GTq1iRRNhjx7GmkTeIADc6oN6pvU-Qgwh3UwbHx7PLJxN6ApN2jEczHVFU/exec")
f = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(f)
key = os.environ.get("HYPE_UPLOAD_KEY") or sys.exit("set HYPE_UPLOAD_KEY in the environment")
body = json.dumps({"key": key, "name": name, "size": os.path.getsize(f), "mimeType": "video/mp4"}).encode()
r = json.load(urllib.request.urlopen(urllib.request.Request(URL, body, {"Content-Type": "application/json"}), timeout=60))
if not r.get("ok"): sys.exit("upload refused: " + str(r.get("error")))
with open(f, "rb") as fh:
    req = urllib.request.Request(r["uploadUrl"], fh.read(), {"Content-Type": "video/mp4"}, method="PUT")
out = json.load(urllib.request.urlopen(req, timeout=600))
print("uploaded:", out.get("name"), "id", out.get("id"))
