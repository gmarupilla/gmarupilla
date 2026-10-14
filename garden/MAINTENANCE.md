# Tiny world

The README contains an SVG island and links to a GitHub issue form. Visitors choose a plot and seed. Their public usernames appear beside their plants.

## Run locally

Use Python 3.10 or later. No third-party packages are required.

```sh
python3 scripts/garden.py render
python3 scripts/garden.py preview
```

`render` draws the real saved state. `preview` creates a separate example garden in the ignored `preview/` directory.

## Publish

Merge the reviewed files into `main` in `gmarupilla/gmarupilla`. Enable Issues and GitHub Actions. The workflow requires `contents: write` and `issues: write`.

Run **Tend the tiny world** manually once. Then submit one planting request. Verify that its workflow passes, the plant appears in the profile, and the issue closes.

## Behaviour

- All growth dates and daily planting limits use UTC.
- Plants sprout immediately, grow after one day, and mature after four days.
- Plants return to soil after 21 days. Their caretakers remain in the state history.
- Weather follows a fixed four-day cycle. It does not use real weather data or affect growth.
- The daily schedule refreshes growth and clears expired plots. GitHub can delay scheduled jobs.
- Every run processes all open planting requests in issue-number order. This recovers requests when GitHub replaces pending workflow runs.
- Each issue receives a saved decision. Retries do not plant twice.
- A successful push must finish before processed issues close. Rejected requests also close; the README lists recent decisions.
- Issue titles and bodies are read as data. They never become shell commands.
- Unrelated issues remain open and do not trigger garden changes.

The workflow uses the repository's built-in token. No hosting account or external service is required. Project covers are illustrations, not measured research results.

To pause the garden, disable **Tend the tiny world** in the Actions tab. To restore an earlier state, restore `garden/state.json` from Git history and run the renderer.
