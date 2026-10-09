"""Fetch real map data and openly licensed photos for the sign-reading scene.

Runs on a GitHub runner (the dev container can't reach these hosts).
Writes into OUT: osm.json (OpenStreetMap, ODbL), commons/*.jpg + commons.json
(Wikimedia Commons, per-file licenses), kartaview.json (probe only).
"""
import json, os, sys, time, urllib.parse, urllib.request

OUT = sys.argv[1]
os.makedirs(OUT + "/commons", exist_ok=True)
UA = {"User-Agent": "taiwan-mandarin-study/1.0 (https://github.com/lens0021/taiwan-mandarin)"}

def get(url, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

# Jiantan station to Shilin night market, a little wider
S, W, N, E = 25.0820, 121.5170, 25.0920, 121.5290
SKIP_OSM = os.environ.get("SKIP_OSM") == "1"
Q = f"""[out:json][timeout:90];
(
  way["highway"]({S},{W},{N},{E});
  way["railway"~"subway|rail|light_rail"]({S},{W},{N},{E});
  node["railway"~"station|subway_entrance"]({S},{W},{N},{E});
  nwr["public_transport"="station"]({S},{W},{N},{E});
  nwr["amenity"~"marketplace|place_of_worship|toilets"]({S},{W},{N},{E});
  nwr["name"~"夜市|慈諴宮|市場"]({S},{W},{N},{E});
  way["waterway"]({S},{W},{N},{E});
  way["building"]["name"]({S},{W},{N},{E});
);
out geom;"""
for ep in [] if SKIP_OSM else ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]:
    try:
        d = get(ep, urllib.parse.urlencode({"data": Q}).encode(), 180)
        j = json.loads(d)
        j["_source"] = ep
        open(OUT + "/osm.json", "w").write(json.dumps(j, ensure_ascii=False))
        print("osm ok", ep, len(j.get("elements", [])))
        break
    except Exception as e:
        print("osm fail", ep, e)

# Wikimedia Commons: files in a few categories, with license metadata
CATS = os.environ.get("CATS", "").split("|") if os.environ.get("CATS") else ["Shilin Night Market", "Jiantan Station", "Shilin Cixian Temple", "Signs in Taipei",
        "Taipei Metro signs", "Stinky tofu in Taiwan", "Bubble tea in Taiwan",
        "Night markets in Taipei", "Taipei Metro station signs", "Platform screen doors of Taipei Metro"]
meta = []
for c in CATS:
    try:
        p = {"action": "query", "format": "json", "generator": "categorymembers", "gcmtitle": "Category:" + c,
             "gcmtype": "file", "gcmlimit": "60", "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
             "iiurlwidth": "640"}
        j = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)))
        pages = (j.get("query") or {}).get("pages") or {}
        print("commons", c, len(pages))
        for pg in pages.values():
            ii = (pg.get("imageinfo") or [{}])[0]
            if not ii.get("mime", "").startswith("image/") or "thumburl" not in ii:
                continue
            em = ii.get("extmetadata", {})
            val = lambda k: (em.get(k) or {}).get("value", "")
            fn = f"c{len(meta):03d}.jpg"
            try:
                open(f"{OUT}/commons/{fn}", "wb").write(get(ii["thumburl"]))
            except Exception as e:
                print("img fail", pg["title"], e); continue
            meta.append({"file": fn, "category": c, "title": pg["title"], "page": ii.get("descriptionurl"),
                         "license": val("LicenseShortName"), "license_url": val("LicenseUrl"),
                         "artist": val("Artist"), "credit": val("Credit"), "desc": val("ImageDescription")[:400],
                         "w": ii.get("thumbwidth"), "h": ii.get("thumbheight")})
            time.sleep(0.2)
    except Exception as e:
        print("commons fail", c, e)
open(OUT + "/commons.json", "w").write(json.dumps(meta, ensure_ascii=False, indent=1))

# KartaView: probe whether public photos exist near the market (no download yet)
try:
    u = "https://api.openstreetcam.org/2.0/photo/?" + urllib.parse.urlencode(
        {"lat": 25.0878, "lng": 121.5242, "radius": 400, "itemsPerPage": 50})
    open(OUT + "/kartaview.json", "wb").write(get(u))
    print("kartaview ok")
except Exception as e:
    print("kartaview fail", e)
