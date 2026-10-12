## Known CVEs in the Base Image

The container scan (Trivy) reports 54 HIGH CVEs at the Debian 13.7 base
layer, and 0 in any Python package. These findings are documented and
suppressed in `.trivyignore` with per-CVE triage notes.

**Why suppress instead of fix:** every finding has an empty "Fixed
Version" column. Debian has not yet published patches for them in
Debian 13's repositories. Upgrading the base image would not resolve
them; only a future Debian point release will.

**Why this is safe:** the runtime image runs as UID 1001 (`appuser`)
with no home directory and a `nologin` shell. The application never
invokes any of the affected OS binaries (`mount`, `bsdutils`, `login`,
`curl --sftp`, `gnutls`, `ncurses`, `perl`). The affected code paths
are unreachable from the running process.

**Re-evaluation cadence:** every entry in `.trivyignore` must be
re-triaged whenever the base image digest changes. The workflow pins
the digest, so updating it is a deliberate action that requires
revisiting this file.

**Python supply chain:** the Docker scan covers all wheels in the
image's `.venv`. As of the last scan, 0 CVEs were found across
scikit-learn, numpy, pandas, scipy, mlflow, fastapi, pydantic,
pandera, and their transitive dependencies. This is the surface that
matters most for an ML application and it remains strict at zero
tolerance.