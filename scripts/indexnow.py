#!/usr/bin/env python3
"""The IndexNow request body for one deploy of a static site.

    python3 indexnow.py git BEFORE AFTER OUT [--repo DIR]
    python3 indexnow.py tree OLD NEW OUT

git:  the site is the repository as committed (DIR, default: the repository that holds this script). Lists the files
      that changed between the commits BEFORE and AFTER.
tree: the site is a built folder (NEW, for example Hugo's public/). Lists the files in NEW that are new or differ from
      OLD, the build of the previously deployed commit.

A changed file counts when its URL is listed in the site's sitemap.xml (path/index.html is path/, any other file is
its own path), or when it is llms.txt. The sitemap URL goes with every submission. Removed files are left out; they
leave the sitemap too. OUT gets the request body: host (from the site's CNAME file), key, keyLocation and urlList.

Exit 0: OUT written, the URLs printed. Exit 3: nothing a search engine reads changed, or BEFORE is the null commit of a
new branch; OUT not written. Exit 2: an error (no key file or more than one, an unknown commit, a missing file).

The key is public by design: a search engine fetches /<key>.txt from the site root to check that a submission comes
from the site's owner. The key is the name of the one file at the site root whose name is 32 hex characters plus .txt
and whose content is that name. Stdlib only. Tests: test_indexnow.py next to this file.

One script for the sites of the same owner: tychat.io uses git mode, uncovertechtalent.com (a Hugo build) uses tree
mode. Keep both modes in every copy, so the copies stay identical.
"""
import filecmp, json, re, subprocess, sys
from pathlib import Path

MAX_URLS = 10000  # IndexNow accepts up to 10,000 URLs per request
KEY_RE = re.compile(r'^[0-9a-f]{32}\.txt$')
LOC_RE = re.compile(r'<loc>\s*([^<\s]+)\s*</loc>')


def fail(msg):
    print('indexnow: ' + msg, file=sys.stderr)
    sys.exit(2)


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout


def key(site):
    keys = [p.stem for p in site.iterdir() if p.is_file() and KEY_RE.match(p.name) and p.read_text().strip() == p.stem]
    if len(keys) != 1:
        fail(f'expected one key file at the site root, found {len(keys)}')
    return keys[0]


def url_for(path, base):
    """The public URL of a file at this path under the site root."""
    if path == 'index.html':
        return base + '/'
    if path.endswith('/index.html'):
        return base + '/' + path[:-len('index.html')]
    return base + '/' + path


def changed_git(repo, before, after):
    if re.fullmatch(r'0{40}', before):
        return None
    try:
        for sha in (before, after):
            git(repo, 'cat-file', '-e', sha + '^{commit}')
        out = git(repo, 'diff', '--name-only', '--no-renames', '--diff-filter=d', '-z', before, after)
    except subprocess.CalledProcessError as e:
        fail(f'git {" ".join(e.cmd[3:])} failed: {e.stderr.strip()}')
    return [p for p in out.split('\0') if p]


def changed_tree(old, new):
    files = sorted(p.relative_to(new).as_posix() for p in new.rglob('*') if p.is_file())
    return [f for f in files if not (old / f).is_file() or not filecmp.cmp(old / f, new / f, shallow=False)]


def main(argv):
    args = argv[1:]
    mode = args[0] if args else ''
    if mode == 'git' and len(args) in (4, 6) and (len(args) == 4 or args[4] == '--repo'):
        before, after, out = args[1:4]
        site = Path(args[5]) if len(args) == 6 else Path(git(Path(__file__).resolve().parent, 'rev-parse', '--show-toplevel').strip())
        changed, span = changed_git(site, before, after), f'{before[:8]}..{after[:8]}'
        if changed is None:
            print('indexnow: no previous commit (new branch); nothing to submit')
            return 3
    elif mode == 'tree' and len(args) == 4:
        old, site, out = Path(args[1]), Path(args[2]), args[3]
        if not site.is_dir():
            fail(f'no built site at {site}')
        changed, span = changed_tree(old, site), f'{old} -> {site}'
    else:
        fail('usage: indexnow.py git BEFORE AFTER OUT [--repo DIR] | indexnow.py tree OLD NEW OUT')
    try:
        host = (site / 'CNAME').read_text().strip()
        listed = set(LOC_RE.findall((site / 'sitemap.xml').read_text()))
    except OSError as e:
        fail(f'cannot read the site: {e}')
    base = 'https://' + host
    urls = sorted({u for u in (url_for(p, base) for p in changed) if u in listed or u == base + '/llms.txt'})
    urls = [u for u in urls if u != base + '/sitemap.xml']
    if not urls and 'sitemap.xml' not in changed:
        print(f'indexnow: {len(changed)} changed files, none of them a URL in the sitemap or llms.txt; nothing to submit')
        return 3
    if len(urls) >= MAX_URLS:  # keep room for the sitemap URL
        print(f'indexnow: {len(urls) + 1} URLs, over the limit of {MAX_URLS} per request; the first {MAX_URLS - 1} and the sitemap are sent')
        urls = urls[:MAX_URLS - 1]
    urls.append(base + '/sitemap.xml')
    k = key(site)
    body = {'host': host, 'key': k, 'keyLocation': f'{base}/{k}.txt', 'urlList': urls}
    Path(out).write_text(json.dumps(body, indent=1) + '\n')
    print(f'indexnow: {len(urls)} URLs from {len(changed)} changed files ({span})')
    for u in urls:
        print('  ' + u)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
