# Deployment Guide

## Local Development

See [Quick Start in README](../README.md#quick-start).

## HuggingFace Spaces (Production)

### 1. Create Space

- Go to huggingface.co → New Space
- SDK: **Docker**
- Visibility: **Public**
- Name: `polafusion-api`

### 2. Push Code

```bash
git clone https://huggingface.co/spaces/EkcupKadakChai/polafusion-api
cd polafusion-api
cp -r path/to/polafusion/backend/* .
echo ".env" >> .gitignore
git add .
git commit -m "Deploy PolaFusion API"
git push
```

### 3. Set Secret

Space Settings → Variables and secrets → New secret:
```
Name:  HF_TOKEN
Value: hf_your_token_here
```

### 4. Update Extension URL

In `extension/background.js` and `extension/popup/popup.js`:
```javascript
const API_BASE = "https://ekcupkadakchai-polafusion-api.hf.space";
```

### Hardware

The free CPU Basic tier works for fallback mode (~5-10s). For ensemble mode upgrade to:
- **CPU Upgrade** — ~30-60s ensemble
- **T4 Small GPU** — ~5-15s ensemble (recommended)

### Checking Build Logs

Go to your Space → **Logs** tab to monitor the Docker build. Common issues:
- `pip install` failures → check requirements.txt versions
- `HF_TOKEN not found` → check secret name is exactly `HF_TOKEN`
- Port errors → Dockerfile must `EXPOSE 7860` and `CMD` must use port 7860
