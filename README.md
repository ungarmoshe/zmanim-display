# zmanim-display

Daily-updating zmanim image (JPEG) for ZIP 11205, rendered from Hebcal.com data.

A GitHub Actions workflow regenerates `zmanim.jpg` every morning (06:37 UTC),
commits it, and deploys it to GitHub Pages (Settings > Pages source must be
"GitHub Actions"). The image is served at a stable URL:
https://ungarmoshe.github.io/zmanim-display/zmanim.jpg

`generate.py` renders locally too: `python generate.py <zip> <out.jpg>`
(set `ZMANIM_NOW` to an ISO datetime to render a specific date).
