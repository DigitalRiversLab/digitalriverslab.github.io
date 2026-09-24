# digitalriverslab.github.io

Website for the **Digital Rivers Lab** at the University of Wyoming, built with [Hugo](https://gohugo.io/) and a small custom theme that lives in this repo (`layouts/` and `assets/css/main.css`). All content is Markdown in `content/`. Push to `main` and GitHub Actions rebuilds and deploys the site.

## Editing content

Each item is a folder containing an `index.md`. Images go in the same folder as the Markdown they belong to.

| What | Where | Notes |
| --- | --- | --- |
| Homepage intro + "Join" band | `content/_index.md` | Body text is the intro paragraph. |
| Research directions | `content/research/<slug>/index.md` | Put a `featured.png`, `.jpg`, or `.gif` in the folder. `weight` sets the order; `short` is the label used on publication chips. Add `image_fit: contain` for diagrams that shouldn't be cropped. |
| People | `content/people/<name>/index.md` | Put `avatar.jpg` or `avatar.png` in the folder. `group` must match one of the groups listed in `content/people/_index.md`. |
| Publications | `content/publications/<slug>/index.md` | Authors are plain names, and anyone with a People page is bolded automatically. `research: [remote-sensing]` links the paper to a research page. Add `abstract:` for an expandable abstract. |
| News | `content/news/<date-slug>/index.md` | Text above `<!--more-->` is the summary shown in lists. |
| Join page | `content/join/index.md` | |
| Open positions | `content/openings/<slug>/index.md` | Each opening is shown in full as a card on the Join page and listed in the homepage "Join" band. Start one with `hugo new openings/<slug>/index.md`. It stays hidden while `draft: true`. Setting `expiryDate` hides it automatically once the date passes, on the next build. If there are no openings, nothing extra shows. |
| Menu, footer contact info | `hugo.yaml` | |

The easiest way to add a publication, person, or news post is to copy an existing folder and edit it.

## The banner

`assets/media/banner.png` and `canal-tile.png` are generated from the logo art (`digitalrivers.png` and the unlettered `welcome.png`): the logo scene, then the canal below the dam continuing to the right. If the logo changes, regenerate them (requires Pillow):

```bash
python scripts/make_banner.py
```

## Local preview

```bash
brew install hugo
hugo server
```

Then open http://localhost:1313. The page reloads as you edit.

## Deployment

`.github/workflows/hugo.yml` builds and deploys on every push to `main`. In the repo's **Settings → Pages**, set the source to **GitHub Actions** (one-time setup).
