# Vercel Deployment Guide

This guide will help you deploy the Story Booker frontend to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. The Vercel CLI (optional, for command-line deployment)
3. Your FastAPI backend deployed or accessible via a public URL

## Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push your code to GitHub/GitLab/Bitbucket**
   - Make sure your `frontend/` directory is in the repository

2. **Import Project in Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your repository
   - Select the repository containing the frontend

3. **Configure Project Settings**
   - **Root Directory**: Set to `frontend` (since frontend is a subdirectory)
   - **Framework Preset**: Next.js (should auto-detect)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)
   - **Install Command**: `npm install` (default)

4. **Set Environment Variables**
   - In the Vercel project settings, go to "Environment Variables"
   - Add the following variable:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend-api-url.com
     ```
   - Replace `https://your-backend-api-url.com` with your actual FastAPI backend URL
   - For local testing during development, you can use:
     ```
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```
   - Set it for all environments (Production, Preview, Development)

5. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your app will be live at `https://your-project.vercel.app`

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

4. **Deploy**
   ```bash
   vercel
   ```
   - Follow the prompts
   - When asked for environment variables, add:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend-api-url.com
     ```

5. **Deploy to Production**
   ```bash
   vercel --prod
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | URL of your FastAPI backend | `http://localhost:8000` (local) or `https://api.example.com` (production) |

### Setting Environment Variables

1. **Via Dashboard:**
   - Go to your project → Settings → Environment Variables
   - Add each variable for the appropriate environments

2. **Via CLI:**
   ```bash
   vercel env add NEXT_PUBLIC_API_URL
   ```

## Important Notes

### Root Directory Configuration

If your `frontend/` is a subdirectory (not the root), you need to configure the root directory in Vercel:

1. Go to Project Settings → General
2. Under "Root Directory", click "Edit"
3. Select `frontend` folder
4. Save

### Backend CORS Configuration

Make sure your FastAPI backend has CORS configured to allow requests from your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-project.vercel.app",
        "http://localhost:3000",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Follow the DNS configuration instructions

## Troubleshooting

### Build Fails

- Check build logs in Vercel dashboard
- Ensure all dependencies are in `package.json`
- Verify Node.js version compatibility (Next.js 16 requires Node 18+)

### API Connection Issues

- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend CORS settings
- Ensure backend is accessible from the internet

### Environment Variables Not Working

- Restart the deployment after adding env variables
- Ensure variable names start with `NEXT_PUBLIC_` for client-side access
- Check that variables are set for the correct environment (Production/Preview/Development)

## Local Development

For local development with the Vercel environment:

1. Create `.env.local` file in `frontend/` directory:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. Start the Next.js dev server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Ensure your FastAPI backend is running on `http://localhost:8000`

## Continuous Deployment

Vercel automatically deploys:
- **Production**: On push to main/master branch
- **Preview**: On push to other branches or pull requests

You can configure this in Project Settings → Git.
