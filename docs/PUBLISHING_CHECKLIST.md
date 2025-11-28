# PyPI Publishing Checklist

Quick reference for publishing MemoryGraph to PyPI.

## One-Time Setup (Do Once)

- [ ] Push workflows to GitHub: `git push origin main`
- [ ] Configure PyPI Trusted Publisher at https://pypi.org/manage/account/publishing/
  - PyPI Project: `memorygraph`
  - Owner: `gregorydickson`
  - Repository: `memory-graph`
  - Workflow: `publish.yml`
  - Environment: `pypi`
- [ ] Create GitHub environment at https://github.com/gregorydickson/memory-graph/settings/environments
  - Name: `pypi`
  - Add yourself as required reviewer
  - Restrict to `main` branch only

## Before Each Release

- [ ] All tests passing: `pytest tests/`
- [ ] Coverage acceptable: `pytest --cov=memorygraph tests/`
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Commit version bump: `git commit -m "chore: bump version to X.Y.Z"`
- [ ] Push to main: `git push origin main`
- [ ] Verify CI tests pass on GitHub

## Publishing

### Method 1: GitHub Release (Recommended)

- [ ] Go to https://github.com/gregorydickson/memory-graph/releases/new
- [ ] Create tag: `vX.Y.Z` (must match `pyproject.toml`)
- [ ] Title: `vX.Y.Z - Brief Description`
- [ ] Copy relevant CHANGELOG entries to description
- [ ] Target: `main` branch
- [ ] Click "Publish release"
- [ ] Watch workflow at https://github.com/gregorydickson/memory-graph/actions
- [ ] Approve deployment when prompted
- [ ] Verify success (green checkmark)

### Method 2: Manual Trigger

- [ ] Go to https://github.com/gregorydickson/memory-graph/actions/workflows/publish.yml
- [ ] Click "Run workflow"
- [ ] Select branch: `main`
- [ ] Click "Run workflow"
- [ ] Approve deployment when prompted
- [ ] Verify success (green checkmark)

## After Publishing

- [ ] Check package on PyPI: https://pypi.org/project/memorygraph/
- [ ] Test installation: `pip install memorygraph`
- [ ] Verify version: `memorygraph --version`
- [ ] Test CLI: `memorygraph --help`
- [ ] Check README badges: https://github.com/gregorydickson/memory-graph

## Troubleshooting

**Tests Failing?**
- Check logs: https://github.com/gregorydickson/memory-graph/actions
- Run locally: `pytest tests/`
- Fix issues before publishing

**Publish Failed?**
- Verify PyPI trusted publisher configured
- Check environment protection rules
- Ensure version doesn't already exist on PyPI

**Can't Approve Deployment?**
- Check you're added as required reviewer
- Check environment settings
- Verify you're logged into GitHub

## Quick Commands

```bash
# Run tests locally
pytest tests/ -v

# Check coverage
pytest --cov=memorygraph tests/

# Build package locally (testing)
python -m build

# Bump version (example)
# Edit pyproject.toml: version = "2.1.0"

# Commit and push
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 2.1.0"
git push origin main
```

## Important Notes

- Version format: `X.Y.Z` (semantic versioning)
- Tag format: `vX.Y.Z` (with 'v' prefix)
- Always tag from `main` branch
- Never overwrite existing PyPI versions
- Always update CHANGELOG.md
- Always run tests before publishing

## Resources

- Full Guide: [PYPI_SETUP_GUIDE.md](PYPI_SETUP_GUIDE.md)
- PyPI Package: https://pypi.org/project/memorygraph/
- GitHub Actions: https://github.com/gregorydickson/memory-graph/actions
- Environment Settings: https://github.com/gregorydickson/memory-graph/settings/environments
