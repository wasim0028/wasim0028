#!/usr/bin/env python3
"""Generate a contribution-graph SVG and a trophy-card SVG for a GitHub profile.
Uses only the standard library. Set GITHUB_TOKEN and GH_LOGIN, or MOCK=1 for demo data."""
import json, os, urllib.request, datetime, math, random

LOGIN = os.environ.get("GH_LOGIN", "wasim0028")
OUT = os.environ.get("OUT_DIR", "profile-cards")
BG, PANEL, BLUE, TEXT, MUTED, GREEN = "#010D2A", "#000C2B", "#00A8FF", "#FFFFFF", "#8AA4C8", "#3FB950"

QUERY = """query($login:String!){user(login:$login){name followers{totalCount}
repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100){totalCount nodes{stargazerCount}}
pullRequests{totalCount} issues{totalCount}
contributionsCollection{totalCommitContributions contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def fetch():
    if os.environ.get("MOCK"):
        random.seed(3)
        days = [(datetime.date.today() - datetime.timedelta(days=i), random.choice([0, 0, 1, 2, 4, 7])) for i in range(30, -1, -1)]
        return dict(name="Md Wasim Akram", followers=12, repos=36, stars=4, prs=4, issues=0, commits=73, days=days)
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
    )
    u = json.load(urllib.request.urlopen(req, timeout=60))["data"]["user"]
    cal = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days = [(datetime.date.fromisoformat(d["date"]), d["contributionCount"]) for d in cal][-31:]
    return dict(
        name=u["name"] or LOGIN, followers=u["followers"]["totalCount"],
        repos=u["repositories"]["totalCount"], stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        prs=u["pullRequests"]["totalCount"], issues=u["issues"]["totalCount"],
        commits=u["contributionsCollection"]["totalCommitContributions"], days=days)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def graph(d):
    W, H, L, R, T, B = 880, 300, 56, 24, 56, 48
    pts = d["days"]
    vmax = max(4, max(c for _, c in pts))
    step = 1 if vmax <= 8 else math.ceil(vmax / 7)
    top = step * math.ceil(vmax / step)
    x = lambda i: L + i * (W - L - R) / (len(pts) - 1)
    y = lambda v: T + (H - T - B) * (1 - v / top)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI,Ubuntu,sans-serif">',
         f'<rect width="{W}" height="{H}" rx="6" fill="{PANEL}"/>',
         f'<text x="{W/2}" y="30" text-anchor="middle" font-size="16" font-weight="600" fill="#58A6FF">{esc(d["name"])}\'s Contribution Graph</text>']
    for v in range(0, top + 1, step):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v)}" y2="{y(v)}" stroke="#1B2E5A" stroke-dasharray="2 4"/>')
        s.append(f'<text x="{L-10}" y="{y(v)+4}" text-anchor="end" font-size="11" fill="#58A6FF">{v}</text>')
    for i, (dt, _) in enumerate(pts):
        s.append(f'<line y1="{T}" y2="{H-B}" x1="{x(i)}" x2="{x(i)}" stroke="#12234A" stroke-dasharray="2 4"/>')
        if i % 2 == 0:
            s.append(f'<text x="{x(i)}" y="{H-B+18}" text-anchor="middle" font-size="11" fill="#58A6FF">{dt.day}</text>')
    xy = [(x(i), y(c)) for i, (_, c) in enumerate(pts)]
    line = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in xy)
    area = line + f" L{xy[-1][0]:.1f},{y(0):.1f} L{xy[0][0]:.1f},{y(0):.1f} Z"
    s.append(f'<path d="{area}" fill="{GREEN}" fill-opacity="0.15"/>')
    s.append(f'<path d="{line}" fill="none" stroke="{GREEN}" stroke-width="2.5" stroke-linejoin="round"/>')
    s += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.5" fill="#fff"/>' for a, b in xy]
    s.append(f'<text x="{W/2}" y="{H-8}" text-anchor="middle" font-size="11" fill="#58A6FF">Days (last 30)</text>')
    s.append(f'<text transform="translate(14 {H/2}) rotate(-90)" text-anchor="middle" font-size="11" fill="#58A6FF">Contributions</text>')
    return "\n".join(s) + "\n</svg>\n"


RANKS = {  # thresholds for C, B, A, S and names
    "Repositories": ("repos", [1, 10, 30, 50], ["First Repository", "Super Repo Creator", "Deep Repo Creator", "God Repo Creator"]),
    "Commits": ("commits", [1, 100, 500, 1000], ["First Commit", "High Committer", "Hyper Committer", "God Committer"]),
    "Followers": ("followers", [1, 10, 40, 100], ["First Follower", "Middle User", "Active User", "Celebrity"]),
    "Stars": ("stars", [1, 10, 50, 100], ["First Star", "Middle Star", "High Star", "Super Star"]),
    "PullRequest": ("prs", [1, 10, 50, 100], ["First Pull", "Middle Puller", "Hyper Puller", "God Puller"]),
    "Issues": ("issues", [1, 10, 50, 100], ["First Issue", "Middle Reporter", "Hyper Reporter", "God Reporter"]),
}
RANK_COLOR = {"S": "#FFB45E", "A": "#2EE6A0", "B": "#8EE3FF", "C": "#6B7FD7", "-": "#4A5878"}


def trophy(cx, y, letter, color):
    return (f'<g transform="translate({cx} {y})"><path d="M-26,0 H26 V16 C26,36 14,46 0,46 C-14,46 -26,36 -26,16 Z" fill="{color}"/>'
            f'<path d="M-26,6 H-38 C-38,26 -30,30 -22,30 M26,6 H38 C38,26 30,30 22,30" fill="none" stroke="{color}" stroke-width="5"/>'
            f'<rect x="-5" y="46" width="10" height="12" fill="{color}"/><rect x="-20" y="58" width="40" height="8" rx="2" fill="{color}"/>'
            f'<circle cx="0" cy="22" r="13" fill="#F4F8FF"/><text y="29" text-anchor="middle" font-size="20" font-family="Courier New,monospace" fill="#222">{letter}</text></g>')


def trophies(d):
    CW, CH, G, COLS = 200, 200, 14, 4
    rows = math.ceil(len(RANKS) / COLS)
    W, H = COLS * CW + (COLS + 1) * G, rows * CH + (rows + 1) * G
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI,Ubuntu,sans-serif">']
    for n, (title, (key, th, names)) in enumerate(RANKS.items()):
        v = d[key]
        tier = sum(v >= t for t in th)  # 0..4
        letter = "-" if tier == 0 else "CBAS"[tier - 1]
        name = "Unranked" if tier == 0 else names[tier - 1]
        nxt = th[tier] if tier < 4 else th[-1]
        prev = th[tier - 1] if tier > 0 else 0
        prog = 1 if tier == 4 else (v - prev) / max(1, nxt - prev)
        c = RANK_COLOR[letter]
        x0, y0 = G + (n % COLS) * (CW + G), G + (n // COLS) * (CH + G)
        s.append(f'<rect x="{x0}" y="{y0}" width="{CW}" height="{CH}" rx="8" fill="{BG}"/>')
        s.append(f'<text x="{x0+CW/2}" y="{y0+30}" text-anchor="middle" font-size="20" font-weight="700" fill="{BLUE}">{title}</text>')
        s.append(trophy(x0 + CW / 2, y0 + 48, letter, c))
        s.append(f'<text x="{x0+CW/2}" y="{y0+142}" text-anchor="middle" font-size="15" font-weight="600" fill="#9DB8F0">{name}</text>')
        s.append(f'<text x="{x0+CW/2}" y="{y0+164}" text-anchor="middle" font-size="15" font-weight="700" fill="#9DB8F0">{v}pt</text>')
        s.append(f'<rect x="{x0+24}" y="{y0+176}" width="{CW-48}" height="5" rx="2.5" fill="#0A3A6B"/>')
        s.append(f'<rect x="{x0+24}" y="{y0+176}" width="{(CW-48)*prog:.1f}" height="5" rx="2.5" fill="{BLUE}"/>')
    return "\n".join(s) + "\n</svg>\n"


if __name__ == "__main__":
    data = fetch()
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "contribution-graph.svg"), "w", encoding="utf-8").write(graph(data))
    open(os.path.join(OUT, "trophies.svg"), "w", encoding="utf-8").write(trophies(data))
    print("ok", {k: v for k, v in data.items() if k != "days"})
