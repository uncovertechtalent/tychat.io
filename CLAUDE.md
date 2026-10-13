# tychat.io: notes for agents

Static site on GitHub Pages, deployed by `.github/workflows/conformity.yml`. Several sessions push this repo.

## Before every push

```bash
git pull --rebase
```

A bot commits `conformity/latest.json` and `conformity/index.html` after every run (`[skip ci]`), so HEAD moves without you. Push without the rebase and the push is rejected.

## The deploy gate

Every push to `main` runs the conformity checks first (composite action from `uncovertechtalent/machinebehavior.io/.github/actions/conformity`, pinned to a commit of its main in `.github/workflows/conformity.yml`; the gate owner bumps that SHA on purpose, with the step in `conformity/README.md` of machinebehavior.io). The Pages deploy job depends on that job: a failing check blocks the deploy and the previous build stays live. Findings are listed at https://tychat.io/conformity/ and in `conformity/latest.json`.

Blocking (deploy stops): rule hits in the blocking tier (`service-closer`, `filler-idiom`, `hook-opener`; see `conformity/site-tier.json`) on any HTML page or on `llms.txt`; placeholder text on a page (`TODO`, `TBD`, `[Voice pass ...]` and the like); a page missing from `sitemap.xml`; a page without `<link rel="canonical">`.

Warning (logged, never blocks): `praise-opener` hits, a page missing from `llms.txt`, pages without a date.

Not scanned, on purpose: `stance.txt`, `register.txt`, `agents.txt`. The lessons list phrases to avoid and quote fawn output as teaching material. Keep such phrases inside the lesson files; a page that quotes one needs it inside double quotes, `<code>`, `<q>` or a `<blockquote>`, which the scan exempts.

Relative links are allowed on this site (`require_root_absolute_links` is false in the config).

Every `uses:` reference is pinned to a full 40-character commit SHA with its release in a comment. Never add a tag or branch ref: the gate check `actions.pinned` blocks the deploy on one. Every outside action also needs its owner on `actions_owners_allow` in `conformity/site-tier.json` (check `actions.owners`); a new owner gets its own reviewed pull request. Dependabot (`.github/dependabot.yml`) proposes new pins monthly and leaves the conformity action alone.

Check locally before pushing (Python 3 and Node, no network; needs a checkout of machinebehavior.io next to this repo, at the commit the workflow pins):

```bash
python3 ../machinebehavior.io/.github/actions/conformity/run.py --root . --config conformity/site-tier.json --requirements conformity/requirements.json --out conformity --dry-run
```

## After the deploy: IndexNow

After each successful deploy, the job `Submit changed URLs to IndexNow` in `.github/workflows/conformity.yml` sends the changed URLs to `https://api.indexnow.org/indexnow`, which shares them with Bing and the other engines that take part. The range starts at the last successful `github-pages` deployment before the run (`deployments: read`), so a push whose own run failed is covered by the next deploy. `scripts/indexnow.py git` maps each changed file to its URL and keeps the ones listed in `sitemap.xml` (pages and the `.txt` lessons) plus `llms.txt`; the sitemap URL goes with every submission, removed files do not. The job logs `IndexNow HTTP <status>` (200 submitted, 202 received with the key check pending) and never fails the run. The key file `066dea709f9a1a3b3103ca2196ecae75.txt` at the root is public by design; keep it there. Tests: `python3 scripts/test_indexnow.py`, also run by the job `Script tests`.

## Records and ownership

- Run records: workflow artifacts, 90 days. History and open findings: `conformity/latest.json` (git).
- Requirements under test: `conformity/requirements.json` (no self-assessment exists for this site yet; A and H rows show "not assessed"). Rule tiers and false-positive tests: `conformity/site-tier.json`.
- Owner of the gate: the legislation-track session (bead `vault-xyrs`); Stefan Coetzee decides tier changes.
- False positive: do not vendor or edit the rule table here. Note page, line and rule in bead `vault-xyrs` (`bd update vault-xyrs --append-notes`) or message the legislation-track session. Rewriting the sentence unblocks the deploy meanwhile.
