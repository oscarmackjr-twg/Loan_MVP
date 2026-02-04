# GitHub Repository Setup Guide

This guide will help you create a GitHub repository and push your code to it.

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Fill in the repository details:
   - **Repository name**: `cursor-loan-engine` (or your preferred name)
   - **Description**: "Loan processing pipeline for structured finance products"
   - **Visibility**: Choose **Private** (recommended) or **Public**
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these commands in your terminal:

### Option A: If you haven't created the repository yet (recommended)

```powershell
# Navigate to your project directory
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine

# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cursor-loan-engine.git

# Rename branch to main (if needed)
git branch -M main

# Push your code
git push -u origin main
```

### Option B: If you already created the repository with a README

```powershell
# Navigate to your project directory
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine

# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/cursor-loan-engine.git

# Pull and merge (if repository has initial files)
git pull origin main --allow-unrelated-histories

# Push your code
git push -u origin main
```

## Step 3: Verify Push

1. Go to your GitHub repository page
2. You should see all your files listed
3. The README.md should be visible on the repository homepage

## Authentication

If you're prompted for credentials:

### Option 1: Personal Access Token (Recommended)
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` scope
3. Use the token as your password when pushing

### Option 2: GitHub CLI
```powershell
# Install GitHub CLI (if not installed)
winget install GitHub.cli

# Authenticate
gh auth login

# Then push normally
git push -u origin main
```

### Option 3: SSH Key (Advanced)
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
2. Add to GitHub: Settings → SSH and GPG keys → New SSH key
3. Change remote URL: `git remote set-url origin git@github.com:YOUR_USERNAME/cursor-loan-engine.git`

## Future Updates

After making changes to your code:

```powershell
# Stage changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push
```

## Branch Protection (Optional)

For production repositories, consider setting up branch protection:
1. Go to repository Settings → Branches
2. Add rule for `main` branch
3. Require pull request reviews before merging

## Troubleshooting

### "Repository not found" error
- Check that the repository name matches exactly
- Verify you have access to the repository
- Ensure you're using the correct GitHub username

### "Authentication failed"
- Use a Personal Access Token instead of password
- Or set up SSH keys

### "Updates were rejected"
- Pull latest changes first: `git pull origin main`
- Resolve any conflicts
- Push again: `git push`

## Next Steps

1. ✅ Create GitHub repository
2. ✅ Push initial code
3. ⬜ Add collaborators (if needed)
4. ⬜ Set up GitHub Actions for CI/CD (optional)
5. ⬜ Configure branch protection (optional)
6. ⬜ Add repository topics/tags for discoverability
