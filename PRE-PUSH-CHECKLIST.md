# Pre-Push Checklist ✅

Before pushing to GitHub, please review this checklist.

## ✅ Completed Tasks

### 1. Cleaned Up Sensitive Files
- [x] Removed `terraform.tfstate` (contains passwords)
- [x] Removed `terraform.tfvars` (contains credentials)
- [x] Removed `tfplan` files
- [x] Removed unused `app-service.tf`

### 2. Updated .gitignore
- [x] Added `docs/` - documentation stays local
- [x] Added `terraform.tfvars` - sensitive data
- [x] Added `tfplan` - terraform plans

### 3. Created CI/CD Pipelines
- [x] CI Pipeline (`ci.yml`) - Test, Lint, Build
- [x] CD Pipeline (`cd.yml`) - Deploy to ACI
- [x] Workflows README

### 4. Documentation
- [x] Terraform README
- [x] Workflows README
- [x] Main README updated

---

## 🔒 GitHub Secrets Required

Before the CI/CD pipelines will work, you need to add these secrets to GitHub:

### Navigate to: Repository → Settings → Secrets and variables → Actions

#### 1. AZURE_CREDENTIALS
Service Principal JSON from Azure:
```bash
az ad sp create-for-rbac \
  --name "github-actions-public-shop" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

#### 2. AZURE_CONTAINER_REGISTRY
```
acrpublicshoppoc.azurecr.io
```

#### 3. AZURE_CONTAINER_REGISTRY_USERNAME
```
acrpublicshoppoc
```

#### 4. AZURE_CONTAINER_REGISTRY_PASSWORD
```bash
az acr credential show --name acrpublicshoppoc --query "passwords[0].value" -o tsv
```

---

## 📂 What Will Be Pushed

### ✅ Will be pushed:
- Source code (`app/`, `migrations/`, `tests/`)
- CI/CD workflows (`.github/workflows/`)
- Terraform configurations (`infrastructure/terraform/*.tf`)
- Deployment scripts (`infrastructure/scripts/`)
- README and documentation in root
- Docker files (`Dockerfile`, `docker-compose.yml`)
- Python dependencies (`requirements.txt`)

### ❌ Will NOT be pushed (in .gitignore):
- `docs/` - Local documentation only
- `terraform.tfstate*` - Sensitive state files
- `terraform.tfvars` - Credentials
- `__pycache__/` - Python cache
- `.venv/` - Virtual environment
- `.env` - Environment variables

---

## 🚀 Git Commands

### Initial Commit
```bash
git add .
git commit -m "Initial commit: ACI-based deployment with CI/CD"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

### Regular Commits
```bash
git add .
git commit -m "Your commit message"
git push
```

---

## 🔍 Verify Before Push

Run these commands to verify:

### 1. Check what will be committed
```bash
git status
```

### 2. Verify .gitignore is working
```bash
# These should NOT appear in git status:
# - docs/
# - terraform.tfvars
# - terraform.tfstate*
```

### 3. Verify no sensitive data
```bash
git diff --cached
```
Look for:
- No passwords
- No API keys
- No personal information

---

## 🎯 After Push

### 1. Add GitHub Secrets
Follow the instructions above to add required secrets.

### 2. Trigger First Deployment
Push to `main` branch or manually trigger the CD workflow:
1. Go to GitHub → Actions
2. Select "CD Pipeline - ACI Deployment"
3. Click "Run workflow"
4. Select "poc" environment
5. Click "Run workflow"

### 3. Monitor Deployment
- Check GitHub Actions for build status
- View logs in Azure Portal
- Test application URL

---

## 📞 Need Help?

If you encounter issues:
1. Check GitHub Actions logs
2. View Azure container logs:
   ```bash
   az container logs \
     --resource-group rg-public-shop-poc \
     --name aci-app-public-shop-poc \
     --container-name app
   ```
3. Review Terraform outputs:
   ```bash
   cd infrastructure/terraform
   terraform output
   ```

---

## ✨ You're Ready!

Everything is configured and cleaned up. You can now safely push to GitHub.

**Command:**
```bash
git add .
git commit -m "Initial commit: Clean ACI deployment"
git push
```

Good luck! 🚀

