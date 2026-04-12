# GEE debug thumbnails

When **`SAVE_GEE_THUMBNAILS=true`** in `backend/.env` and you call **`GET /building/{id}?live_cv=true`**, each successful Earth Engine fetch writes a PNG here:

`{building_id}.png`

Restart **`uvicorn`** after changing `.env`. The first request per building id creates the file (responses are cached in memory afterward).

`*.png` files are gitignored; this README is committed so the folder is easy to find in the repo.
