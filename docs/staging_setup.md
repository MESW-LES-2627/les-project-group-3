# Action Required: Staging Infrastructure Setup (Issue #84)

## 1. Database (Neon)
We need a separate database so staging tests and migrations don't corrupt production data.
1. Go to [Neon](https://neon.tech/) account and create a new project called `patas-staging`.
2. Create a database role/user (e.g., `patas_admin`) and a database (e.g., `patas_db`).
3. Copy the new Postgres connection string. 

## 2. Storage (Cloudflare R2)
We need an isolated storage bucket so staging image uploads do not mix with production media.
1. Go to the Cloudflare Dashboard and navigate to **R2 Object Storage**.
2. Click **Create bucket** and name it something like `patas-media-staging`.
3. Click **Manage R2 API Tokens** and create a new API token.
4. Grant it **Object Read & Write** permissions specifically for the new staging bucket.
5. Copy the generated **Access Key ID**, **Secret Access Key**, and the bucket's **S3 Endpoint URL**.

## 3. Backend (Render)
We need a second API instance running the code from the `staging` branch.
1. Go to [Render](https://render.com/) account and create a new **Web Service**.
2. Connect it to our repository: `MESW-LES-2627/les-project-group-3`. 
*(Note: You may need to authorize Render to access this repo if you haven't already).*
3. **Crucial:** Set the **Branch** to `staging` (not `main`).
4. Add the environment variables:
  * `DATABASE_URL`: (The new Neon staging connection string from Step 1)
  * `JWT_SECRET`: (Generate a new random string, do not reuse the production secret)
  * `ALLOWED_ORIGINS`: (The Vercel URL we will create in step 4)
  * `AWS_ACCESS_KEY_ID`: (Your R2 Access Key ID from Step 2)
  * `AWS_SECRET_ACCESS_KEY`: (Your R2 Secret Access Key from Step 2)
  * `AWS_S3_ENDPOINT_URL`: (Your R2 S3 Endpoint URL from Step 2)
  * `AWS_STORAGE_BUCKET_NAME`: (The name of your new R2 bucket, e.g., `patas-media-staging`)
  * `ABLY_API_KEY`: (The API key of the Ably app `patas-staging`; one Ably app per environment, see ADR 0029)
5. Copy the new Render service URL (e.g., `https://patas-backend-staging.onrender.com`).

## 4. Frontend (Vercel)
1. Log into [Vercel](https://vercel.com/) account and click **Add New → Project**.
2. Import our deployment mirror repository: `ammp102/les-project-group-3-deploy`.
3. **Crucial:** Before clicking Deploy, open the **Framework Preset / Build and Output Settings**. Look for the **Root Directory** or **Git** settings and change the **Production Branch** to `staging`. (This makes Vercel build the staging branch as the main URL).
4. Open the **Environment Variables** section and add:
  * `NEXT_PUBLIC_API_URL`: (Your new Render staging URL)
  * `BACKEND_URL`: (Your new Render staging URL)
  * `ABLY_API_KEY`: (The same key as Render. Server only: never prefix it with `NEXT_PUBLIC_`)
5. Click **Deploy**. Vercel will give you a permanent URL for this staging app.
