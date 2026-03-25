# 🧠 Vidora AI 

Vidora AI is an intelligent video analysis platform built with Next.js and FastAPI, powered by a Hybrid AI strategy (Local + Cloud).

## 🚀 Repository Details & Rules

This is a monorepo containing both the Frontend and Backend. 
*   **Frontend (Next.js):** Runs on port `3000`
*   **Backend (FastAPI):** Runs on port `8000`

### 🤝 Git Collaboration Rules

To ensure a smooth, conflict-free workflow during this tight 3-day sprint, **follow these rules strictly**:

1.  **Do NOT code directly on the `main` branch.**
    *   `main` is protected. It should only contain stable, working code.
2.  **Use the `dev` branch for integration.**
    *   `dev` is where both Frontend and Backend code is merged and tested together.
3.  **Always use Feature Branches.**
    *   Before starting a new task, branch off from `dev`.
    *   **Naming Convention:** `feat/backend-[feature-name]` or `feat/frontend-[feature-name]`
    *   Example: `git checkout -b feat/backend-upload-api`
4.  **Commit Often, Push Often.**
    *   Make small, incremental commits so you don't lose work.
5.  **Review Before Merging.**
    *   Create a Pull Request against `dev`. Make sure it works locally before pushing.

---

## 🛠️ Git Commands Cheatsheet

**1. Initializing & Pushing this Repository to GitHub (Do this ONCE to start):**
```bash
# 1. Initialize Git in this root folder
git init

# 2. Add all current files
git add .

# 3. Make your first commit
git commit -m "Initial commit - scaffold project"

# 4. Rename the default branch to 'main'
git branch -M main

# 5. Link your GitHub repository (REPLACE WITH YOUR ACTUAL REPO URL)
git remote add origin https://github.com/your-username/vidora-ai.git

# 6. Push to GitHub
git push -u origin main

# 7. Immediately create and switch to the 'dev' integration branch
git checkout -b dev
git push -u origin dev
```

**2. Starting a New Feature (Daily Workflow):**
```bash
# Always start from dev and pull latest changes
git checkout dev
git pull origin dev

# Create your feature branch
git checkout -b feat/your-feature-name

# ... Do your coding ...

# Add and commit your work
git add .
git commit -m "Brief description of what you built"

# Push to your feature branch on GitHub
git push origin feat/your-feature-name

# -> Then go to GitHub.com and open a Pull Request into the 'dev' branch!
```

---

## 📁 Directory Structure

*   **/backend** - FastAPI application (Python)
*   **/frontend** - Next.js web application (TypeScript)
*   **/docs** - Architecture, PRD, and API contracts
*   **docker-compose.yml** - For spinning up both services locally

## ⚡ Quick Start (Locally)

Once Docker is fully set up, you will be able to run both applications simultaneously using:
```bash
docker-compose up --build
```
This is the ultimate goal by Day 3. For Day 1, you will likely run them separately using `npm run dev` and `uvicorn main:app --reload`.
