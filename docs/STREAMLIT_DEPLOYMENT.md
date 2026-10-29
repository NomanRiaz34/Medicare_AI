# Streamlit Community Cloud deployment

1. Extract the project and push the contents of `mediguide_ai` to your GitHub repository root.
2. Confirm `app.py`, `requirements.txt`, `.streamlit/config.toml`, `src/`, and `assets/fonts/DejaVuSans.ttf` are included.
3. Do not include `.env`, API keys, `.streamlit/secrets.toml`, `.data`, virtual environments, patient records or downloaded patient reports.
4. At https://share.streamlit.io, create an app from the repository and branch.
5. Select `app.py` as the main file and choose Python 3.12 in Advanced settings. If the repository includes the outer folder, select `mediguide_ai/app.py` instead.
6. Deploy. Dependencies are installed from `requirements.txt` next to the entrypoint or at repository root.
7. Open the deployed HTTPS URL. It must show **Welcome to MediGuide** and **Verify key & continue** before any assessment form.
8. Each visitor enters their own OpenAI key. There is no required shared key in Cloud secrets.

## First deployment checks

- Missing or rejected key: assessment dashboard stays hidden.
- Valid key with metadata access to the configured model: dashboard opens.
- Normal widget changes: the key is not reverified every time.
- Open another private browser window: it must start at the connection screen.
- Sign out: key and patient session disappear, welcome screen returns.
- Test a fictional assessment and a sample PDF.
- Test real microphone permission on the deployed HTTPS origin; check transcription permissions and quota.
- Test Urdu output and both themes on desktop and a narrow viewport.

## Troubleshooting

**Key accepted but generation fails:** The welcome check validates authentication and model metadata access, not billing, generation quota or every endpoint permission. Check those at OpenAI. A restricted key may need permission to retrieve the configured model.

**Model unavailable during welcome:** Check the default configured in `src/config.py` and the key's project/model access. Metadata lookup is performed before the model can be changed in the connected sidebar.

**Build fails:** Confirm Python 3.12, read the dependency-installation log, and use the provided `requirements.txt`. Development tests are in `requirements-dev.txt` and do not need to be installed by the deployed app.

**Font missing:** Commit the entire `assets/fonts` directory, including the font and license.

**Voice unavailable:** Allow microphone permission and use HTTPS or localhost. Keys must also have transcription access. Typed symptom input remains available.

**SQLite/history disappears:** Cloud local files and browser-session memory are not durable patient storage. This is expected; use downloads for fictional demo reports.

**App opens without the welcome page:** Confirm the deployed branch points to this edition, then reboot the app and open a fresh browser session. The old `.env` key does not bypass the new gate.

The package is prepared for deployment. Publishing it to your own GitHub/Streamlit accounts and live API verification are separate steps and have not been performed for you.
