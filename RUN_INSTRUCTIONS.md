# NanoTrade Local Run & Deployment Instructions

This guide provides instructions on how to run the NanoTrade backend locally via Docker, how to expose it for frontend consumption, and how to deploy it to production platforms like Railway.

## 1. Local Demo Setup (Docker)

To run the entire backend (API, Background Worker, Engine, Redis) locally using a single command:

### Prerequisites
- Docker installed
- Docker Compose installed

### Steps
1. **Configure Environment**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Fill out the `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET`, and `SIMULATOR_SECRET` with your development keys. 
   *(Note: The `REDIS_URL` is pre-configured for Docker and should not be changed.)*

2. **Start the System**
   ```bash
   docker-compose up --build
   ```

3. **Accessing the Services**
   - The FastAPI server will be available at: `http://localhost:8000`
   - Interactive API Docs: `http://localhost:8000/docs`
   - The matching engine and celery workers will run continuously in the background.

---

## 2. Exposing the API via Tunnel (For Vercel Frontends)

If your frontend is deployed (e.g. on Vercel) and needs to talk to your local backend, you can expose the local API using a tunneling service.

### Using ngrok
```bash
ngrok http 8000
```
Then, update your frontend's `NEXT_PUBLIC_API_URL` to point to the `https://<your-id>.ngrok.app` URL provided by ngrok.

### Using Cloudflare Tunnel
```bash
cloudflared tunnel --url http://localhost:8000
```

---

## 3. Production Deployment (Railway)

Railway allows deploying this repository directly since we have a root `Dockerfile`.

### Steps
1. Push your code to GitHub.
2. In Railway, click **New Project** → **Deploy from GitHub repo**.
3. Select this `NanoTrade` repository.
4. **Environment Variables**: Add your `SUPABASE_*` credentials and `SIMULATOR_SECRET` in the variables tab.

### Architecture on Railway
Since Railway uses the single `Dockerfile`, you will need to create **three separate services** inside the same Railway project (from the same repo) by overriding the **Start Command**:

1. **API Service**:
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
2. **Celery Worker**:
   - Start Command: `celery -A app.workers.celery_app worker --loglevel=info`
3. **Engine Daemon**:
   - Start Command: `python -m app.workers.engine_daemon`

*(Note: Don't forget to provision a Redis instance on Railway and link its `REDIS_URL` variable to all three services!)*
