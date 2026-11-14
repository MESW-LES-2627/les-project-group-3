# Action Required: Staging Infrastructure Setup (Issue #84)

## 1. Database (Neon)
We need a separate database so staging tests and migrations don't corrupt production data.
1. Go to [Neon](https://neon.tech/) account and create a new project called `patas-staging`.
2. Create a database role/user (e.g., `patas_admin`) and a database (e.g., `patas_db`).
3. Copy the new Postgres connection string. 

## 2. Backend (Render)
We need a second API instance running the code from the `staging` branch.
1. Go to [Render](https://render.com/) account and create a new **Web Service**.
2. Connect it to our repository: `MESW-LES-2627/les-project-group-3`. 
*(Note: You may need to authorize Render to access this repo if you haven't already).*
3. **Crucial:** Set the **Branch** to `staging` (not `main`).
4. Add the environment variables:
  * `DATABASE_URL`: (The new Neon staging connection string from Step 1)
  * `JWT_SECRET`: (Generate a new random string, do not reuse the production secret)
  * `ALLOWED_ORIGINS`: (The Vercel URL we will create in step 3)
5. Copy the new Render service URL (e.g., `https://patas-backend-staging.onrender.com`).

## 3. Frontend (Vercel)
1. Log into [Vercel](https://vercel.com/) account and click **Add New → Project**.
2. Import our deployment mirror repository: `ammp102/les-project-group-3-deploy`.
3. **Crucial:** Before clicking Deploy, open the **Framework Preset / Build and Output Settings**. Look for the **Root Directory** or **Git** settings and change the **Production Branch** to `staging`. (This makes Vercel build the staging branch as the main URL).
4. Open the **Environment Variables** section and add:
  * `NEXT_PUBLIC_API_URL`: (Your new Render staging URL)
  * `BACKEND_URL`: (Your new Render staging URL)
5. Click **Deploy**. Vercel will give you a permanent URL for this staging app.