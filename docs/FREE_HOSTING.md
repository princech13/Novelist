# Free personal hosting: Render + Neo4j Aura

This setup uses Render's free static site and free Docker web service, plus
Neo4j AuraDB Free. Docker Compose remains the local development setup.

## 1. Publish the current code to your Git repository

Commit and push the current application changes to a GitHub/GitLab/Bitbucket
repository accessible to Render. A private repository is fine. Do not commit
`.env`, downloaded Aura credentials, or database exports.

## 2. Create the database

1. Open https://console.neo4j.io/ and create an AuraDB **Free** instance.
2. Save its connection URI, username, and password securely.
3. Wait for the instance to be running.

The URI should look like `neo4j+s://YOUR-INSTANCE.databases.neo4j.io`.
Aura calls the username variable `NEO4J_USERNAME` in some downloaded credential
files; this application expects `NEO4J_USER` instead.

This creates an empty cloud database. Local users, books, and articles are not
copied automatically. Register a new account after deployment, or plan a separate
data migration if you want your existing data.

## 3. Deploy the backend on Render

Open https://dashboard.render.com/ and select **New > Web Service**. Connect the
repository and select the branch containing the latest changes.

| Setting | Value |
| --- | --- |
| Name | Any available name, for example `novelist-api` |
| Language/runtime | Docker |
| Root directory | Leave blank (repository root) |
| Dockerfile path | `./Dockerfile` |
| Docker build context | Repository root (`.`), if asked |
| Docker command override | `uvicorn app.main:app --host 0.0.0.0 --port 10000` |
| Instance type | **Free** |
| Health check path | `/actuator/health` |

Add environment variables before deploying:

| Variable | Value |
| --- | --- |
| `NEO4J_URI` | Aura's `neo4j+s://...` connection URI |
| `NEO4J_USER` | Aura's username, usually `neo4j` |
| `NEO4J_PASSWORD` | Aura's generated database password |
| `JWT_SECRET_KEY` | A private random secret; use Render's generator or the command below |
| `CORS_ORIGINS` | Initially `https://example.invalid`; replace with the actual frontend origin in step 5 |

To generate your own JWT secret locally:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Store it only as the backend's environment variable. Never add it to frontend
variables. Keep this secret stable across deployments.

Deploy, then open `https://YOUR-API.onrender.com/actuator/health`.
It should return `{"status":"UP"}`. Also check `/docs`.
Copy the actual API URL Render assigns; names may receive a suffix.

## 4. Deploy the frontend on Render

Select **New > Static Site**, then connect the same repository and branch.

| Setting | Value |
| --- | --- |
| Root directory | `ui` |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |
| Environment variable `NODE_VERSION` | `24` |
| Environment variable `VITE_API_BASE_URL` | The actual API URL, e.g. `https://YOUR-API.onrender.com` |

Do not append `/backend` or `/api/v1` to that API URL. The frontend adds endpoint
paths itself. Vite embeds this URL at build time; rebuild the frontend if it changes.

In the static site's **Redirects/Rewrites**, add:

| Source | Destination | Action |
| --- | --- | --- |
| `/*` | `/index.html` | Rewrite |

This lets direct links and refreshes work on routes such as `/books` and `/articles`.

## 5. Connect the two services

Copy the actual frontend URL, for example `https://YOUR-SITE.onrender.com`.
Update the backend's `CORS_ORIGINS` to that exact origin, with no trailing slash
or path, and save/redeploy the backend.

Open the frontend URL, register an account, add a book, post a review, and publish
an article. Refresh an article or book detail URL to verify the rewrite works.

## Free-tier behavior and troubleshooting

- Select **Free**, not a time-limited paid trial, when creating both services.
- Render's free API sleeps after 15 idle minutes; waking it can take about a minute.
  Open its health URL and wait before retrying the frontend if the first request fails.
- AuraDB Free automatically pauses after 72 hours of inactivity. Resume it in
  Aura before using the app again. Check Aura's current retention policy and export
  data you want to keep before leaving the project unused for a long period.
- Free plans have monthly usage and database-size limits. Check the provider dashboards.
- Health check fails: verify Aura is running and all three Neo4j credentials match.
- Browser reports CORS: check the backend allows the actual frontend HTTPS origin.
- Frontend calls localhost or `/backend`: correct `VITE_API_BASE_URL`, then rebuild it.
- Page refresh gives 404: add the static-site rewrite above.

## Official references

- Render free services: https://render.com/docs/free
- Render Docker deployment: https://render.com/docs/docker
- Render static sites: https://render.com/docs/static-sites
- Aura instance creation: https://neo4j.com/docs/aura/getting-started/create-instance/
- Aura connection settings: https://neo4j.com/docs/python-manual/current/connect/
- Aura inactivity behavior: https://neo4j.com/docs/aura/managing-instances/instance-actions/

These steps prepare a deployment; no cloud resources have been created by Codex.
