#!/usr/bin/env python3
"""Tests for indexnow.py next to this file: git mode on a small repository and tree mode on two small folders, both
built in a temporary folder. Stdlib and git only.

    python3 test_indexnow.py

Exits 1 when a case fails.
"""
import contextlib, io, json, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in the repository
sys.path.insert(0, str(Path(__file__).resolve().parent))
import indexnow  # noqa: E402

KEY = '0123456789abcdef0123456789abcdef'
BASE = 'https://example.test'
SITEMAP = '<urlset>' + ''.join(f'<url><loc>{BASE}{u}</loc></url>' for u in ('/', '/a/', '/a/b/', '/lesson.txt')) + '</urlset>\n'
SITE = {'CNAME': 'example.test\n', 'sitemap.xml': SITEMAP, f'{KEY}.txt': KEY + '\n', 'index.html': '0',
        'a/index.html': '0', 'a/b/index.html': '0', 'orphan/index.html': '0', 'lesson.txt': '0', 'llms.txt': '0',
        'scripts/x.py': '0', 'a/style.css': '0'}


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), '-c', 'user.name=test', '-c', 'user.email=test@example.test', *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def write(root, files):
    for path, text in files.items():
        p = root / path
        if text is None:
            p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)


def commit(root, files, msg):
    write(root, files)
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', msg)
    return git(root, 'rev-parse', 'HEAD')


def run(out, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            rc = indexnow.main(['indexnow.py', *args, str(out)] if args[0] == 'tree' else ['indexnow.py', *args[:3], str(out), *args[3:]])
        except SystemExit as e:
            rc = e.code
    body = json.loads(out.read_text()) if rc == 0 else None
    if out.exists():
        out.unlink()
    return rc, body and body['urlList'], body


def main():
    failures = []

    def case(name, got, want):
        print(('ok   ' if got == want else 'FAIL ') + name)
        if got != want:
            failures.append(f'{name}: got {got!r}, want {want!r}')

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        out = tmp / 'body.json'

        # git mode: the repository is the site
        repo = tmp / 'repo'
        repo.mkdir()
        git(repo, 'init', '-q')
        g = lambda before, after: run(out, 'git', before, after, '--repo', str(repo))  # noqa: E731
        c0 = commit(repo, SITE, 'base')
        c1 = commit(repo, {'a/b/index.html': '1', 'orphan/index.html': '1', 'scripts/x.py': '1', 'a/style.css': '1'},
                    'nested page, a page outside the sitemap, a script and a stylesheet')
        rc, urls, body = g(c0, c1)
        case('git: nested page in the sitemap; the others left out', (rc, urls), (0, [f'{BASE}/a/b/', f'{BASE}/sitemap.xml']))
        case('git: host, key and key location', body and (body['host'], body['key'], body['keyLocation']),
             ('example.test', KEY, f'{BASE}/{KEY}.txt'))
        c2 = commit(repo, {'scripts/x.py': '2'}, 'script only')
        case('git: no URL changed: exit 3', g(c1, c2)[0], 3)
        c3 = commit(repo, {'index.html': '3', 'llms.txt': '3', 'lesson.txt': '3'}, 'home page, llms.txt and a text lesson')
        case('git: home page, llms.txt and a text file in the sitemap', g(c2, c3)[1],
             [f'{BASE}/', f'{BASE}/lesson.txt', f'{BASE}/llms.txt', f'{BASE}/sitemap.xml'])
        c4 = commit(repo, {'a/index.html': None, 'sitemap.xml': SITEMAP.replace(f'<url><loc>{BASE}/a/</loc></url>', '')},
                    'page removed')
        case('git: removed page left out; the changed sitemap still goes', g(c3, c4)[1], [f'{BASE}/sitemap.xml'])
        case('git: range over several commits', g(c0, c3)[1],
             [f'{BASE}/', f'{BASE}/a/b/', f'{BASE}/lesson.txt', f'{BASE}/llms.txt', f'{BASE}/sitemap.xml'])
        case('git: null commit of a new branch: exit 3', g('0' * 40, c4)[0], 3)
        case('git: unknown commit: exit 2', g('1' * 40, c4)[0], 2)
        c5 = commit(repo, {'fedcba9876543210fedcba9876543210.txt': 'fedcba9876543210fedcba9876543210', 'index.html': '5'},
                    'second key file')
        case('git: two key files: exit 2', g(c4, c5)[0], 2)

        # tree mode: the site is a built folder, compared with the build of the previous deploy
        old, new = tmp / 'old', tmp / 'new'
        write(old, SITE)
        shutil.copytree(old, new)
        t = lambda: run(out, 'tree', str(old), str(new))  # noqa: E731
        case('tree: identical builds: exit 3', t()[0], 3)
        write(new, {'a/b/index.html': '1', 'orphan/index.html': '1', 'index.xml': '1'})
        case('tree: changed page in the sitemap; the others left out', t()[1], [f'{BASE}/a/b/', f'{BASE}/sitemap.xml'])
        write(new, {'c/index.html': '1', 'sitemap.xml': SITEMAP.replace('</urlset>', f'<url><loc>{BASE}/c/</loc></url></urlset>')})
        case('tree: new page and the changed sitemap', t()[1], [f'{BASE}/a/b/', f'{BASE}/c/', f'{BASE}/sitemap.xml'])
        case('tree: no previous build: every URL in the sitemap', run(out, 'tree', str(tmp / 'none'), str(new))[1],
             [f'{BASE}/', f'{BASE}/a/', f'{BASE}/a/b/', f'{BASE}/c/', f'{BASE}/lesson.txt', f'{BASE}/llms.txt', f'{BASE}/sitemap.xml'])
        case('tree: missing build: exit 2', run(out, 'tree', str(old), str(tmp / 'none'))[0], 2)

    for f in failures:
        print(f, file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
