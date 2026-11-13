# Kya Bache — Daily Bal Hanuman Ji Stories

This repository generates one Hindi children's story video about Bal Hanuman Ji and uploads one video to YouTube.

## Daily schedule

GitHub Actions runs at `00:30 UTC`, which is `06:00 AM Asia/Kolkata`. You can also start a run manually from **Actions → Kya Bache Daily YouTube Automation → Run workflow**.

## Story safety and uniqueness

- Gemini is required. There is no offline or animal-story fallback.
- Each story must contain exactly 12 scenes.
- Every scene must explicitly mention Bal Hanuman Ji.
- Previously accepted story titles and text are stored in `output/story_history.json` and committed to the repository by the workflow.
- The generator retries up to four times when a response is invalid or looks too similar to a previous story.
- If Gemini is unavailable, a response is invalid, or all attempts look repeated, the workflow fails and the upload step is not run.
- Similarity checks are automated safeguards, not a guarantee of perfect semantic originality. Review the video before relying on unattended public publishing.

## Required GitHub Actions secrets

Repository **Settings → Secrets and variables → Actions → New repository secret**:

- `GEMINI_API_KEY`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

Never put API keys, OAuth client secrets or refresh tokens in source files or commit them to Git.

## YouTube publishing

The workflow uploads exactly one file: `output/daily_video.mp4`. It does not attempt to upload `daily_short.mp4`. The current workflow sets visibility to `public` and declares the video as made for kids. Confirm the audience setting is accurate for each video and review content before enabling unattended public uploads. You can change `YOUTUBE_PRIVACY` in the workflow to `private` for safer testing.

## Visual output

`image_generator.py` draws Bal Hanuman Ji in every scene. `video_editor.py` adds gentle zoom movement to the illustrations. This is an illustrated motion video, not full 3D character animation.

## Run locally

Install Python dependencies and FFmpeg, set `GEMINI_API_KEY`, then run:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Local story history is stored in `output/story_history.json`. Keep that file when moving the project to another machine so previous stories remain known.
