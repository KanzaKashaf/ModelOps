
### `docs/safety-checklist.md`
```markdown
# Public Repository Safety Checklist

Before every commit and push, verify:

- [ ] No `.env` file is committed.
- [ ] No credentials, API keys, or tokens in any file.
- [ ] No real user data or personally identifiable information.
- [ ] No large datasets or model binaries in Git.
- [ ] `.gitignore` covers `.venv/`, `__pycache__/`, `data/`, `models/`, `mlruns/`.
- [ ] CI logs do not print secrets.
- [ ] Docker images do not contain secrets.
- [ ] Kubernetes Secrets are not committed to Git.