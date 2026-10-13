# tychat.io: notes for agents

Static site on GitHub Pages, deployed by `.github/workflows/conformity.yml`. Several sessions work in this repo; changes reach `main` through pull requests only.

## Pull request flow

1. Branch from the current main: `git fetch origin && git switch -c <branch> origin/main`.
2. Run the gate dry run (below) until it prints `overall=pass`.
3. Push the branch and open the pull request. Merges are squash-only, so the title becomes the commit title. Never write the literal `[skip ci]` into a commit message, a pull request title, or the squash message: GitHub skips the run when the head commit message contains it anywhere, so the required check never reports and a merge starts no deploy. Only the bot commit carries it.
4. Wait for the `Conformity checks` job to pass on the pull request. It is the required check in the ruleset on `main`, so renaming the job blocks every merge until the ruleset names the new check.
5. Run the local reviewer before you report the pull request ready: `~/.config/powersuit/review-pr.sh uncovertechtalent/tychat.io <n>`. Read the saved comment and put the findings in your report; post it only on Stefan Coetzee's explicit go.
6. A merge needs one approval of the latest push, from an account other than the one that pushed it. Agent sessions push as the repository owner account, `uncovertechtalent`; Stefan Coetzee approves and merges from his personal account.

Never push to `main`. One automated writer does: conformity-bot (below). So `main` moves without you; the merge does not need an up-to-date branch, so rebase on `origin/main` only when GitHub reports a conflict.

## The run record and the deploy key

On `main`, the job `Commit the run record` commits `conformity/latest.json` and `conformity/index.html` after every run, a failed run included, as conformity-bot with `[skip ci]`. It is the only job that writes: it pushes over SSH with the deploy key `conformity-bot`, whose private key is the secret `CONFORMITY_PUSH_KEY` of the environment `main-push`. That environment allows the `main` branch only, so a pull request run or a manual run from another branch never receives the key. The job sets `deployment: false`, so it adds no deployment records. The branch rules on `main` let the deploy key through; every job's workflow token is read-only for contents. Without the secret the job is a dry run: it logs the change and a warning, pushes nothing, and the deploy goes ahead with the previous record. A rejected push or a failed rebase fails the job and skips the deploy; re-run all jobs, because a re-run of the record job alone reuses the run's artifact and stops if `main` already has a newer record. Pull request runs, and manual runs from another branch, commit nothing and deploy nothing. Key, secret, environment and ruleset changes are Stefan Coetzee's; a session never creates, reads or prints them.

## The deploy gate

Every pull request to `main` and every push to `main` run the conformity checks first (composite action from `uncovertechtalent/machinebehavior.io/.github/actions/conformity`, pinned to a commit of its main in `.github/workflows/conformity.yml`; the gate owner bumps that SHA on purpose, with the step in `conformity/README.md` of machinebehavior.io). The Pages deploy job depends on that job and on the record job: a failing check blocks the deploy and the previous build stays live. Findings are listed at https://tychat.io/conformity/ and in `conformity/latest.json`.

Blocking (deploy stops): rule hits in the blocking tier (`service-closer`, `filler-idiom`, `hook-opener`; see `conformity/site-tier.json`) on any HTML page or on `llms.txt`; placeholder text on a page (`TODO`, `TBD`, `[Voice pass ...]` and the like); a page missing from `sitemap.xml`; a page without `<link rel="canonical">`.

Warning (logged, never blocks): `praise-opener` hits, a page missing from `llms.txt`, pages without a date.

Not scanned, on purpose: `stance.txt`, `register.txt`, `agents.txt`. The lessons list phrases to avoid and quote fawn output as teaching material. Keep such phrases inside the lesson files; a page that quotes one needs it inside double quotes, `<code>`, `<q>` or a `<blockquote>`, which the scan exempts.

Relative links are allowed on this site (`require_root_absolute_links` is false in the config).

Every `uses:` reference is pinned to a full 40-character commit SHA with its release in a comment. Never add a tag or branch ref: the gate check `actions.pinned` blocks the deploy on one. Every outside action also needs its owner on `actions_owners_allow` in `conformity/site-tier.json` (check `actions.owners`); a new owner gets its own reviewed pull request. Dependabot (`.github/dependabot.yml`) proposes new pins monthly and leaves the conformity action alone. Workflow changes pass zizmor (`zizmor --offline .github`); an accepted finding gets an inline `# zizmor: ignore[<rule>]` comment on its line and an entry with its reason in `.github/zizmor.yml`.

Check locally before pushing (Python 3 and Node, no network; needs a checkout of machinebehavior.io next to this repo, at the commit the workflow pins):

```bash
python3 ../machinebehavior.io/.github/actions/conformity/run.py --root . --config conformity/site-tier.json --requirements conformity/requirements.json --out conformity --dry-run
```

## After the deploy: IndexNow

After each successful deploy, the job `Submit changed URLs to IndexNow` in `.github/workflows/conformity.yml` sends the changed URLs to `https://api.indexnow.org/indexnow`, which shares them with Bing and the other engines that take part. The range starts at the commit that triggered the last successful `github-pages` deployment before the run (`deployments: read`), so a push whose own run failed is covered by the next deploy. That commit comes before its run's bot commit, so `/conformity/` goes out with most submissions. The record job's environment makes no deployments, so it never moves the range. The job runs the tests first on its own checkout, so a broken URL selection submits nothing. The Pages upload is the whole repository, so `scripts/` is served at tychat.io/scripts/ like `CLAUDE.md` and `README.md`; keep secrets and private hosts out of it. `scripts/indexnow.py git` maps each changed file to its URL and keeps the ones listed in `sitemap.xml` (pages and the `.txt` lessons) plus `llms.txt`; the sitemap URL goes with every submission, removed files do not. The job logs `IndexNow HTTP <status>` (200 submitted, 202 received with the key check pending) and never fails the run. The key file `066dea709f9a1a3b3103ca2196ecae75.txt` at the root is public by design; keep it there. Tests: `python3 scripts/test_indexnow.py`, also run by `.github/workflows/scripts.yml` on every pull request and push that changes `scripts/`.

## Records and ownership

- Run records: workflow artifacts, 90 days. History and open findings: `conformity/latest.json` (git).
- Requirements under test: `conformity/requirements.json` (no self-assessment exists for this site yet; A and H rows show "not assessed"). Rule tiers and false-positive tests: `conformity/site-tier.json`.
- Owner of the gate: the legislation-track session (bead `vault-xyrs`); Stefan Coetzee decides tier changes.
- False positive: do not vendor or edit the rule table here. Note page, line and rule in bead `vault-xyrs` (`bd update vault-xyrs --append-notes`) or message the legislation-track session. Rewriting the sentence unblocks the deploy meanwhile.
