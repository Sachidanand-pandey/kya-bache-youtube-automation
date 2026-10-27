# Kya Bache — Daily AI YouTube Video

This starter project creates a short Hindi children's story, generates four AI illustrations, creates narration, renders a vertical MP4, and uploads it to YouTube using the YouTube Data API.

## Important
- The default upload setting is **private**. Review videos before making them public.
- OpenAI text, image, and audio API calls can incur charges and require API access/billing.
- Google OAuth authorization is required. YouTube uploads cannot be authorized with an API key alone.
- The workflow uses GitHub Actions and runs daily at 9:00 AM Asia/Kolkata, plus manual runs.
- First-time uploads from some API projects may be restricted to private visibility until the project is audited by Google.
- Generated output is a narrated illustrated story video, not full-motion character animation.

## 1. Create the repository
Create a GitHub repository and upload all files from this folder. Ensure `.github/workflows/daily-video.yml` is included.

## 2. Set up OpenAI
Create an API key in the OpenAI developer platform. Add it to GitHub repository Settings → Secrets and variables → Actions as:
- `OPENAI_API_KEY`

## 3. Set up YouTube API and OAuth
1. Open Google Cloud Console and create/select a project.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen. Add your Google account as a test user if the app is in Testing mode.
4. Create OAuth credentials of type **Desktop app** and download the JSON file.
5. Save it as `client_secret.json` in this folder on your own computer. Do not upload it to GitHub.
6. Install local setup dependency: `pip install google-auth-oauthlib`
7. Run `python oauth_setup.py` and complete the Google authorization in your browser.
8. Copy the printed values into GitHub repository Settings → Secrets and variables → Actions:
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`

Keep secrets private. If the OAuth app is in Testing mode, refresh tokens may expire after seven days for external apps; set up the consent screen appropriately and verify your app configuration.

## 4. Run
Open GitHub → your repository → Actions → **Kya Bache Daily AI Video** → Run workflow.

The scheduled workflow runs every day at 9:00 AM India time. GitHub scheduled runs can sometimes be delayed. The default video visibility is private.

## 5. Make public only after reviewing
Once you have reviewed the output and are comfortable with the content, change `YOUTUBE_PRIVACY` in the workflow from `private` to `public`. For a safer workflow, keep it private and publish manually.

## Troubleshooting
- `OPENAI_API_KEY is missing`: add the GitHub secret with that exact name.
- OAuth errors: recheck client ID, client secret, refresh token, YouTube Data API v3, and consent-screen configuration.
- Image/audio generation errors: check API access, billing, quotas, and model availability.
- FFmpeg errors: confirm the install step succeeded and inspect the Actions log.
