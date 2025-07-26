# Release Process

This document describes how to release new versions of mcp-deadmansnitch.

## Release Types

### Beta Releases (Test on TestPyPI First)
For testing releases on TestPyPI before production:

```bash
# Create a beta release tag
git tag v0.1.2-beta1
git push origin v0.1.2-beta1
```

This will:
1. Build the package
2. Publish to TestPyPI only
3. Run basic smoke tests
4. **NOT** publish to production PyPI

Test the package:
```bash
# Install from TestPyPI
uvx --from https://test.pypi.org/simple/ mcp-deadmansnitch==0.1.2-beta1

# Or with pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-deadmansnitch==0.1.2-beta1
```

### Production Releases
Once tested via beta on TestPyPI:

```bash
# Create a production release tag
git tag v0.1.2
git push origin v0.1.2
```

This will:
1. Build the package
2. Publish to TestPyPI first (must succeed)
3. Only if TestPyPI succeeds, publish to PyPI
4. Create GitHub release with changelog

## Release Workflow

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Commit changes**: `git commit -m "chore: prepare release v0.1.2"`
4. **Create beta tag**: `git tag v0.1.2-beta1`
5. **Push and test**: `git push origin main v0.1.2-beta1`
6. **Verify on TestPyPI** and test installation
7. **Create production tag**: `git tag v0.1.2`
8. **Push production tag**: `git push origin v0.1.2`
9. **Monitor GitHub Actions** for successful deployment

## Beta Releases
Beta releases go to TestPyPI only for testing:

```bash
git tag v0.2.0-beta1
git tag v0.2.0-beta2  # if you need to test fixes
```

## Troubleshooting

### TestPyPI Failures
- Check if version already exists (TestPyPI doesn't allow overwrites)
- Verify trusted publisher is configured on TestPyPI
- Check GitHub Actions logs for detailed errors

### PyPI Failures
- TestPyPI must succeed first (it's now a dependency)
- Ensure version doesn't already exist on PyPI
- Verify trusted publisher is configured on PyPI