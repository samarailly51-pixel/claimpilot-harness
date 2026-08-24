# Publishing ClaimPilot Harness

ClaimPilot uses PyPI Trusted Publishing so no long-lived PyPI token is stored in GitHub.

## One-time PyPI setup

Create a pending publisher for the package name `claimpilot-harness` in PyPI with these exact values:

| Field | Value |
| --- | --- |
| PyPI project name | `claimpilot-harness` |
| GitHub owner | `samarailly51-pixel` |
| GitHub repository | `claimpilot-harness` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

The repository contains the matching GitHub environment and `.github/workflows/release.yml`. The publishing job receives only `id-token: write`; it does not receive repository contents write access or a package password.

## Verify locally

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

Install the generated wheel in a clean environment and run the packaged quickstart before tagging a release.

## Release

1. Update `pyproject.toml` and `claimpilot_harness/__init__.py` to the same version.
2. Run the complete unit suite and clean-wheel quickstart.
3. Create and push the matching `vX.Y.Z` tag.
4. GitHub Actions builds the distributions, checks metadata, obtains an ephemeral OIDC credential, and publishes to PyPI.
5. Create the GitHub release from the same tag and attach the verified wheel and source distribution if desired.

The workflow follows the [PyPA Trusted Publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
