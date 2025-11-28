# PyPI Publishing Setup Guide

This guide walks you through setting up automated PyPI publishing for MemoryGraph using GitHub Actions and PyPI Trusted Publishers (OIDC).

## What Was Created

### GitHub Actions Workflows

**1. `.github/workflows/publish.yml`**
- Publishes to PyPI when you create a GitHub release
- Can also be triggered manually via workflow dispatch
- Uses PyPI Trusted Publishers (OIDC) - no API tokens needed
- Requires GitHub environment approval for safety
- Two-stage process: build → publish

**2. `.github/workflows/test.yml`**
- Runs automatically on push to main and all PRs
- Tests on Python 3.10, 3.11, and 3.12
- Runs full test suite (409 tests)
- Checks code coverage (minimum 60%)
- Provides CI status before publishing

**3. README.md Updates**
- Added CI/CD status badges
- Shows test status and PyPI version

### Commit Details
- **Commit**: `092d3fb4d1a981007d7e9a57021f7114489e1257`
- **Files Added**:
  - `.github/workflows/publish.yml` (58 lines)
  - `.github/workflows/test.yml` (36 lines)
  - `README.md` (updated badges)

---

## Setup Steps

### Step 1: Push Workflows to GitHub

```bash
cd /Users/gregorydickson/claude-code-memory
git push origin main
```

This pushes the workflows to GitHub, making them available for configuration.

### Step 2: Configure PyPI Trusted Publisher

**Why Trusted Publishers?**
- No long-lived API tokens to manage
- Automatic credential rotation
- Scoped to specific repository and workflow
- Recommended security best practice by PyPI

**Steps:**

1. **Create/Login to PyPI Account**
   - Go to: https://pypi.org/account/login/
   - Create account if needed: https://pypi.org/account/register/

2. **Add Pending Trusted Publisher**
   - Go to: https://pypi.org/manage/account/publishing/
   - Click: **"Add a new pending publisher"**
   - Fill in the form:
     ```
     PyPI Project Name:    memorygraph
     Owner:                gregorydickson
     Repository name:      memory-graph
     Workflow name:        publish.yml
     Environment name:     pypi
     ```
   - Click: **"Add"**

   **Important**: Use "pending publisher" because the package doesn't exist on PyPI yet. After the first successful publish, this becomes a permanent trusted publisher.

3. **Verify Configuration**
   - You should see the pending publisher listed
   - It will show: `gregorydickson/memory-graph` → `memorygraph`

### Step 3: Create GitHub Environment

**Why an Environment?**
- Adds approval gate before publishing to PyPI
- Prevents accidental publishes
- Provides audit trail

**Steps:**

1. **Go to Repository Settings**
   - Navigate to: https://github.com/gregorydickson/memory-graph/settings/environments

2. **Create New Environment**
   - Click: **"New environment"**
   - Name: `pypi` (must match workflow configuration)
   - Click: **"Configure environment"**

3. **Add Protection Rules** (Recommended)
   - **Required reviewers**: Add yourself
     - Ensures you manually approve each publish
   - **Deployment branches**: Select "Selected branches"
     - Add rule: `main` only
     - Prevents publishing from feature branches
   - Click: **"Save protection rules"**

4. **Verify Setup**
   - Environment should show: `pypi` with protection rules
   - Status: Active

---

## Publishing to PyPI

### Option 1: Create GitHub Release (Recommended)

This is the standard way to publish new versions:

1. **Prepare Release**
   ```bash
   # Ensure all changes are committed
   git status

   # Ensure you're on main branch
   git checkout main
   git pull
   ```

2. **Create Release on GitHub**
   - Go to: https://github.com/gregorydickson/memory-graph/releases/new

   - **Tag**: `v2.0.0`
     - Use semantic versioning (vX.Y.Z)
     - Must match version in `pyproject.toml`

   - **Release Title**: `v2.0.0 - MemoryGraph Rename`

   - **Description**: Copy relevant sections from `CHANGELOG.md`:
     ```markdown
     ## What's New

     - Package renamed from `claude-code-memory` to `memorygraph`
     - Simpler installation: `pip install memorygraph`
     - Command renamed: `memorygraph` (was `claude-code-memory`)
     - Zero-config SQLite backend by default
     - Optional Neo4j/Memgraph for advanced use cases

     ## Breaking Changes

     - Package name changed (uninstall old package first)
     - Command name changed in MCP configuration

     See [MIGRATION.md](MIGRATION.md) for upgrade instructions.
     ```

   - **Target**: `main` branch

   - Click: **"Publish release"**

3. **Monitor Workflow**
   - Go to: https://github.com/gregorydickson/memory-graph/actions
   - Watch the "Publish to PyPI" workflow run
   - **Build job**: Compiles package (no approval needed)
   - **Publish job**: Waits for your approval (if environment protection enabled)

4. **Approve Deployment** (if required reviewers configured)
   - You'll receive notification
   - Click: **"Review deployments"**
   - Check: `pypi` environment
   - Click: **"Approve and deploy"**
   - Workflow continues and publishes to PyPI

5. **Verify Success**
   - Workflow shows green checkmark
   - Visit: https://pypi.org/project/memorygraph/
   - Should show version `2.0.0`

### Option 2: Manual Workflow Dispatch

For republishing or testing without creating a release:

1. **Navigate to Workflow**
   - Go to: https://github.com/gregorydickson/memory-graph/actions/workflows/publish.yml

2. **Run Workflow**
   - Click: **"Run workflow"** button (top right)
   - Select branch: `main`
   - Click: **"Run workflow"** (green button)

3. **Follow Steps 3-5** from Option 1 above

---

## Verification & Testing

### After First Publish

1. **Check PyPI**
   ```bash
   # Visit in browser
   open https://pypi.org/project/memorygraph/

   # Should show:
   # - Version: 2.0.0
   # - Description from README.md
   # - Links to GitHub
   ```

2. **Test Installation**
   ```bash
   # Create fresh virtual environment
   python -m venv test-env
   source test-env/bin/activate

   # Install from PyPI
   pip install memorygraph

   # Verify version
   memorygraph --version
   # Should output: MemoryGraph 2.0.0

   # Test CLI
   memorygraph --help

   # Cleanup
   deactivate
   rm -rf test-env
   ```

3. **Verify CI Badges**
   - Visit: https://github.com/gregorydickson/memory-graph
   - README should show:
     - Tests badge (passing/failing)
     - PyPI version badge (2.0.0)

### Monitor CI/CD

**Test Workflow**
- Runs on every push to `main`
- Runs on all pull requests
- View results: https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml

**Publish Workflow**
- Only runs on releases or manual trigger
- View history: https://github.com/gregorydickson/memory-graph/actions/workflows/publish.yml

---

## Troubleshooting

### Issue: "Pending publisher not found"

**Cause**: You configured PyPI before pushing workflows to GitHub.

**Fix**:
1. Ensure workflows are pushed: `git push origin main`
2. Delete pending publisher on PyPI
3. Re-add with correct configuration

### Issue: "Environment protection rules failed"

**Cause**: Trying to publish from non-main branch or missing approval.

**Fix**:
1. Ensure you're on `main` branch
2. Check environment protection rules
3. Approve deployment if required reviewers enabled

### Issue: "id-token permission not granted"

**Cause**: GitHub Actions permissions misconfigured.

**Fix**:
1. Check `.github/workflows/publish.yml`
2. Ensure `permissions: id-token: write` exists
3. Re-push workflow if needed

### Issue: "Package version already exists"

**Cause**: Trying to republish same version.

**Fix**:
1. PyPI doesn't allow overwriting versions
2. Bump version in `pyproject.toml`
3. Create new release with new version tag

### Issue: Tests failing on specific Python version

**Cause**: Code incompatibility or missing dependencies.

**Fix**:
1. Check test logs in Actions tab
2. Run tests locally: `pytest tests/`
3. Fix compatibility issues
4. Update dependencies in `pyproject.toml`

---

## Future Releases

### Workflow for New Versions

1. **Update Version**
   ```bash
   # Edit pyproject.toml
   # version = "2.1.0"  # or 2.0.1, 3.0.0, etc.
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [2.1.0] - 2025-XX-XX

   ### Added
   - New feature description

   ### Fixed
   - Bug fix description
   ```

3. **Commit Changes**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 2.1.0"
   git push
   ```

4. **Create Release**
   - Follow "Option 1: Create GitHub Release" above
   - Use new version tag: `v2.1.0`
   - Copy new CHANGELOG entries to description

5. **Workflow Runs Automatically**
   - Tests run first (must pass)
   - Build creates package
   - Publish waits for approval
   - Package appears on PyPI

---

## Security Best Practices

### What We're Using
- **OIDC/Trusted Publishers**: No long-lived tokens
- **Environment Protection**: Manual approval required
- **Scoped Permissions**: `id-token: write` only
- **Branch Protection**: Only `main` can publish

### What to Avoid
- **Never** commit API tokens to repository
- **Never** disable environment protection for production
- **Never** skip tests before publishing
- **Never** publish from feature branches

### Audit Trail
- All publishes logged in GitHub Actions
- Deployment history in environment page
- PyPI shows publication timestamp and source

---

## Next Steps

1. **Push workflows to GitHub** (if not done):
   ```bash
   git push origin main
   ```

2. **Configure PyPI Trusted Publisher** (see Step 2 above)

3. **Create GitHub Environment** (see Step 3 above)

4. **Create First Release** (see Publishing Option 1 above)

5. **Verify Installation** (see Verification section above)

---

## Resources

- **PyPI Trusted Publishers**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **GitHub Environments**: https://docs.github.com/en/actions/deployment/targeting-different-environments
- **Semantic Versioning**: https://semver.org/

---

**Questions or Issues?**
- Check troubleshooting section above
- Review GitHub Actions logs
- Check PyPI trusted publisher configuration
- Verify environment protection rules
