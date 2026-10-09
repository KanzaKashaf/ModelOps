
### `docs/windows-setup.md`
```markdown
# Windows Setup Guide

## 1. Install Git
- Download from https://git-scm.com/download/win
- Verify: `git --version`

## 2. Install Python 3.11+
- Download from https://www.python.org/downloads/windows/
- Check "Add Python to PATH"
- Verify: `python --version`

## 3. Install VS Code
- Download from https://code.visualstudio.com/

## 4. Install Docker Desktop
- Download from https://www.docker.com/products/docker-desktop/
- Enable WSL 2 backend during installation.
- Verify: `docker version` and `docker run hello-world`

## 5. Clone Repository
```powershell
git clone https://github.com/your-username/modelops.git
cd modelops