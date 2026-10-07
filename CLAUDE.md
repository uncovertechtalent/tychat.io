# tychat.io: notes for agents

Static site on GitHub Pages, deployed by `.github/workflows/conformity.yml`. Several sessions push this repo.

## Before every push

```bash
git pull --rebase
```

A bot commits `conformity/latest.json` and `conformity/index.html` after every run (`[skip ci]`), so HEAD moves without you. Push without the rebase and the push is rejected.

## The deploy gate

Every push to `main` runs the conformity checks first (composite action from `uncovertechtalent/machinebehavior.io/.github/actions/conformity`). The Pages deploy job depends on that job: a failing check blocks the deploy and the previous build stays live. Findings are listed at https://tychat.io/conformity/ and in `conformity/latest.json`.

Blocking (deploy stops): rule hits in the blocking tier (`service-closer`, `filler-idiom`, `hook-opener`; see `conformity/site-tier.json`) on any HTML page or on `llms.txt`; placeholder text on a page (`TODO`, `TBD`, `[Voice pass ...]` and the like); a page missing from `sitemap.xml`; a page without `<link rel="canonical">`.

Warning (logged, never blocks): `praise-opener` hits, a page missing from `llms.txt`, pages without a date.

Not scanned, on purpose: `stance.txt`, `register.txt`, `agents.txt`. The lessons list phrases to avoid and quote fawn output as teaching material. Keep such phrases inside the lesson files; a page that quotes one needs it inside double quotes, `<code>`, `<q>` or a `<blockquote>`, which the scan exempts.

Relative links are allowed on this site (`require_root_absolute_links` is false in the config).

Check locally before pushing (Python 3 and Node, no network; needs a checkout of machinebehavior.io next to this repo):

```bash
python3 ../machinebehavior.io/.github/actions/conformity/run.py --root . --config conformity/site-tier.json --requirements conformity/requirements.json --out conformity --dry-run
```

## Records and ownership

- Run records: workflow artifacts, 90 days. History and open findings: `conformity/latest.json` (git).
- Requirements under test: `conformity/requirements.json` (no self-assessment exists for this site yet; A and H rows show "not assessed"). Rule tiers and false-positive tests: `conformity/site-tier.json`.
- Owner of the gate: the legislation-track session (bead `vault-xyrs`); Stefan Coetzee decides tier changes.
- False positive: do not vendor or edit the rule table here. Note page, line and rule in bead `vault-xyrs` (`bd update vault-xyrs --append-notes`) or message the legislation-track session. Rewriting the sentence unblocks the deploy meanwhile.
