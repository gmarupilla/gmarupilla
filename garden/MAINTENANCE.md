# Tiny world

The README contains an SVG island and links to a GitHub issue form. Visitors choose a plot and seed. Their public usernames appear beside their plants.

The garden has 48 plots: six rows (A–F) and eight columns (1–8).

## Run locally

Use Python 3.10 or later. No third-party packages are required.

```sh
python3 scripts/garden.py render
python3 scripts/garden.py preview
```

`render` draws the real saved state. `preview` creates a separate example garden in the ignored `preview/` directory.

Open `preview/index.html` to review the design. Its example plants do not change the real garden state.

## Artwork

`scripts/garden_art.py` draws the island, pixel sprites, and project covers. All artwork is original and self-contained SVG.

`scripts/garden_layout.py` defines the shared plot grid. If you change the grid, also update the issue form options and request validation.

Edit `SPRITES` and `PALETTE` to change the plants. Plot labels render above the plants so mature trees cannot hide them.

Fireflies have a subtle opacity animation. The SVG disables this animation when the viewer prefers reduced motion.

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
