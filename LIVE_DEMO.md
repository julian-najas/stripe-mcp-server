# 🌐 Live Demo Setup

## Quick Deploy with Cloudflare Tunnel (Free)

**No signup required. Works instantly.**

### 1. Start your API locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Install Cloudflare Tunnel (one-time)

**macOS:**
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Linux:**
```bash
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

**Windows:**
Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

### 3. Create tunnel

```bash
cloudflared tunnel --url http://localhost:8000
```

You'll get a URL like:
```
https://blue-bird-92.trycloudflare.com
```

### 4. Test it

```bash
curl https://blue-bird-92.trycloudflare.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "debug": true
}
```

---

## Alternative: Railway (Persistent Deployment)

See main README for Railway deployment instructions.

**Cloudflare Tunnel is perfect for:**
- Quick demos
- Testing webhooks locally (Stripe can reach your localhost)
- Portfolio demonstrations
- No credit card needed

**Railway is better for:**
- Production deployments
- Persistent URLs
- Environment variable management
