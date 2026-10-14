# Tiny world

The profile shows an animated clay garden. The eight beds contain 48 live plots:
A–C across the back of each bed and D–F across the front. Visitors plant through
the linked GitHub issue form. Their public usernames appear in the gardener table.

## Run locally

Use Python 3.10 or later and install the pinned renderer dependency:

```sh
python3 -m pip install -r requirements.txt
python3 scripts/garden.py render
python3 scripts/garden.py preview
```

`render` draws the saved state. `preview` creates an example garden in the ignored
`preview/` folder. Example plants do not change the saved garden.

## Artwork and animation

- `garden/art/empty-world.gif` is the reusable animated landscape. Its beds are empty.
- Transparent PNGs in `garden/art/` contain the plant sprites.
- `garden/art/layout.json` maps each bed to its soil corners at 960 × 640 pixels.
- `scripts/garden_animation.py` positions sprites from `garden/state.json`, applies
  age-based growth, and composites every frame. It draws plots from back to front.
- The GIF has a shared palette and loops indefinitely. The README also links to
  `assets/garden-still.png` for a motion-free view.
- The rendered filename hashes the state, date, renderer and artwork. This prevents
  GitHub's image cache from showing an earlier planting state.
- Artwork was created through Higgsfield. The source model and job IDs are recorded
  in `garden/art/provenance.json`. Landscape trees outside the beds are scenery.
- Daily renders use only local files and Pillow. They make no generation calls and
  require no Higgsfield token or credits. Project covers remain SVG illustrations.

## Publish

Push to `main` in `gmarupilla/gmarupilla`. Enable Issues and GitHub Actions.
The workflow requires `contents: write` and `issues: write`.

The daily schedule and planting webhooks run the renderer, save the state and
artwork, then close processed requests. The source artwork is committed once;
only the current generated GIF is retained in the working tree.

## Behaviour

- All growth dates and daily planting limits use UTC.
- Each account can plant once per UTC day.
- A new plant appears as a sprout, grows after one day and matures after four.
- After 21 days, the plot returns to soil. Its caretaker remains in the history.
- GitHub can delay scheduled jobs. The animation is continuous, but planting state
  changes only when the workflow runs.
- Each run processes all open planting requests in issue-number order and includes
  the triggering webhook request if GitHub's issue listing has not caught up.
- Each request has a saved decision. Retries cannot plant it twice.
- A successful push must finish before requests close. Rejected requests also close;
  the README lists recent decisions.
- Issue content is data and never becomes a shell command.
- Unrelated issues do not trigger the workflow.

To pause the garden, disable **Tend the tiny world** in Actions. To restore a prior
planting state, restore `garden/state.json` from Git history and run the renderer.
