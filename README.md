# zmanim-display

Zmanim JPEG images for ZIP 11205, rendered from Hebcal.com data.

- Portrait: https://ungarmoshe.github.io/zmanim-display/zmanim.jpg
- Landscape, 1920 x 1200: https://ungarmoshe.github.io/zmanim-display/zmanim-landscape.jpg

The GitHub Actions workflow is configured to generate and deploy both images at 06:37 UTC each day, with manual dispatch available. Manual generation and deployment have been tested. Unattended scheduled execution remains unverified. A failed or late run can leave the previous dated image online. Check the printed date before use. GitHub Pages caching can delay visible updates.

Calculation methods are displayed on the images and have not been confirmed for the intended religious use. The image URL does not establish touchscreen, fullscreen or automatic-refresh compatibility.

Local rendering requires Pillow, Noto Sans Hebrew and DejaVu Sans fonts:

```
python generate.py 11205 zmanim.jpg
python generate_landscape.py 11205 zmanim-landscape.jpg
```

`ZMANIM_NOW` can override the civil day and generation timestamp for layout testing. The Shabbos API request always returns the current upcoming Shabbos, so an overridden date is not a complete historical or future-date simulation.

Pages source must be GitHub Actions. Only the two JPEG files are staged for Pages deployment.
