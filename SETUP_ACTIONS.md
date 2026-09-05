# GitHub Actions / Pages setup

## 1. Required repository layout

GitHub only discovers workflows located at the repository root under:

```text
.github/workflows/sync-rules.yml
```

The repository root should look like:

```text
.github/
  workflows/
    sync-rules.yml
config/
scripts/
tests/
docs/
rules/
README.md
...
```

Do **not** upload everything into another `surge-rule-hub/` subfolder inside the repository.

## 2. macOS warning: `.github` is hidden

Finder hides names beginning with a dot. If you manually drag files into GitHub, `.github` may be omitted.

Recommended upload methods:

### Method A - Git command line (recommended)

After extracting the ZIP, open Terminal in that folder and run:

```bash
git init
git add -A
git commit -m "Initial Surge Rule Hub"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```

`git add -A` includes `.github` automatically.

### Method B - GitHub website

If the repository is already uploaded but Actions cannot find a workflow:

1. Open the repository on GitHub.
2. Choose **Add file -> Create new file**.
3. Enter this exact filename:
   `.github/workflows/sync-rules.yml`
4. Copy the contents of the root-level `SYNC_RULES_WORKFLOW.yml` file into it.
5. Commit directly to the default branch.

The root-level `SYNC_RULES_WORKFLOW.yml` is only a visible backup. GitHub does **not** run it from the repository root.

## 3. Enable Actions

Open:

`Settings -> Actions -> General`

Make sure GitHub Actions is enabled for the repository. If the **Actions** tab itself is missing, Actions may be disabled by repository or organization policy.

## 4. Enable Pages deployment

Open:

`Settings -> Pages -> Build and deployment -> Source -> GitHub Actions`

The workflow deploys the generated `docs/` directory using the official Pages actions.

## 5. First run

Open:

`Actions -> Sync and Build Surge Rules -> Run workflow`

The workflow will:

1. test the parser;
2. fetch/mirror upstream rules with retries;
3. reject any active upstream that fetches/parses to zero rules;
4. convert, filter, merge and de-duplicate;
5. reject any active service whose final rule count is zero;
6. generate `dist/RuleSnippet.conf`;
7. regenerate README + Pages from that canonical file;
8. commit last-known-good mirrors/generated outputs;
9. deploy `docs/` to GitHub Pages.

A successful V6 run is intentionally strict: it must not publish a page where only iFAST is populated.

## 6. Scheduled updates

The workflow runs automatically every 6 hours at minute 37.

## 7. How to tell whether Pages is really from Actions

After a successful run, the Pages home page must show:

- a real GitHub source commit (7-character SHA), **not** `local`;
- an Actions Run link;
- `Active sources: N/N OK`;
- `Services: 48/48 non-empty`;
- the generated `RULE-SET` URLs must contain your real Pages base URL, not `<GITHUB_USER>` / `<REPO>`.

If the page still says `local`, `PRE-ACTION LOCAL BUILD`, `WAITING_FOR_FIRST_SUCCESSFUL_ACTIONS_BUILD`, or contains placeholder URLs, you are looking at a pre-build/stale branch deployment. Check `Settings -> Pages -> Source -> GitHub Actions`, then run the workflow again and wait for both the **build** and **deploy** jobs to be green.

## V8 canonical-build guard

V8 treats `dist/RuleSnippet.conf` as the canonical build artifact. The workflow now checks that this file exists, is non-empty, and contains a `[Rule]` header immediately after `scripts/build.py` finishes. README synchronization only runs after this guard passes.

If the guard reports that the canonical artifact is missing, replace `scripts/build.py`, `scripts/readme_sync.py`, `scripts/verify.py`, and `.github/workflows/sync-rules.yml` together from the same release instead of mixing files from older packages.

The Action log also prints the pipeline version and SHA-256 hashes of the three scripts before building, which makes version-mismatch diagnosis straightforward.
