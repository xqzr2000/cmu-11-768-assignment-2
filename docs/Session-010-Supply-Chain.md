# Session 010 — OCI image and chart wheel-lock provenance

**Status, 2026-11-07 (America/Vancouver):** The user inspected live public registry *metadata* from the Codespace; no image layer was pulled, built, or started. The chart-only hash file and its offline checker are committed, but **the checker has not yet been executed in Codespaces**. Do not confuse a digest-shaped reference or a lockfile hash with a successful pull, wheel download, or reproducible image build.

## OCI manifest evidence — user Codespace transcript

The user executed:

```bash
uname -m
docker buildx imagetools inspect docker.io/library/python:3.12-slim
git status --short --branch
```

Observed host architecture: `x86_64` (target Docker platform `linux/amd64`).

| Evidence | Observed value |
| --- | --- |
| Image source | `docker.io/library/python:3.12-slim` |
| Index media type | `application/vnd.oci.image.index.v1+json` |
| Full multi-platform index digest | `sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54` |
| Matching `linux/amd64` image manifest | `sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177` |
| AMD64 source tag/version | `3.12.16-slim-trixie` |
| Underlying Debian base name | `debian:trixie-slim` |
| Underlying Debian base digest annotation | `sha256:7378260c0a098d27ac206225db5e7d92b8c7c84ea7afccc86eeb513756bbd392` |
| AMD64 image creation annotation | `2026-11-05T07:52:11Z` |
| Git status | Clean and tracking `feature/session-010-chart-agent-controller` |

The **index** digest identifies the multi-platform list; the **AMD64 manifest** identifies the platform-specific Python image. The Debian annotation is **not** the correct `python` image pin. For this single-platform development environment, the candidate immutable base reference is:

```text
python:3.12-slim@sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177
```

This is a **candidate pinned reference confirmed by registry metadata at inspection time**, *not* a successful image pull, a signature/attestation trust verification, or a functioning chart image. The mutable tag may later point to different digests; the observed digest is still a stable content identifier.

## Existing repository dependency evidence

The main project `pyproject.toml` pins the four plotting roots:

- `matplotlib==3.10.5`
- `numpy==2.3.2`
- `pandas==2.3.1`
- `pillow==12.3.0`

The committed `uv.lock` (Git blob `546d4d0839cc287c1b29b7c8b74ea4582737964a` at inspection) contains package versions and SHA-256 metadata for many platforms. The chart-only dependency closure for the four roots under the recorded lock has **14 packages**: those four roots plus contourpy, cycler, fonttools, kiwisolver, packaging, pyparsing, python-dateutil, pytz, six, and tzdata.

**New** `requirements/chart-cp312-linux-amd64.txt` records the 14 exact package versions with one SHA-256 wheel hash per package. Native wheels were selected with `cp312-cp312` and `manylinux`/`x86_64` tags when present, otherwise a universal `py3-none-any` or `py2.py3-none-any` wheel. The accompanying comments identify the exact expected wheel filenames.

`scripts/check_chart_wheel_lock_offline.py` reads the **actual committed** `uv.lock` and requirements file; it recursively checks the four roots' **unconditional** dependency closure, exact versions, registry provenance, selected wheel labels, and hashes. It fails closed if new marker/extra dependency behavior appears or a pinned hash or package changes. It neither downloads nor installs wheels. The checker has **not yet passed in Codespaces** and is the next required verification.

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_chart_wheel_lock_offline.py
git status --short --branch
```

Expected *only after verification*: audit of **14** packages (4 direct, 10 transitive). If a future dependency graph changes, the offline auditor should block rather than silently omit a package.

## Remaining gaps before a real chart-capable image

1. **Wheel retrieval/install:** We have only lockfile-published wheel hashes. No wheel bytes have been downloaded and rehashed or installed against this OCI image. A future approved build must enforce `pip install --require-hashes --only-binary=:all:` using the complete reviewed file and confirm dependency compatibility and plotting imports.
2. **Dockerfile/build-context integration:** The sixth-slice `chart_image_recipe.py` still emits a direct-pins `pip install` command, not this 14-package hash-lock, and the minimal context currently includes only Dockerfile, verified CSVs, and the extractor. A future reviewed code update must add **exactly** this lock to the allowlist, stage it securely, and consume it from the Dockerfile. Do not claim that our current Dockerfile is hash-locked.
3. **Platform and image integrity:** The observed manifest corresponds to `linux/amd64` as reported by the public registry. No actual layer pull or signed-origin verification was performed; building a chart image requires separately approved Docker operations and a fixed target platform.
4. **Sandbox architecture:** Current gateway's default image is still the historical floating `python:3.12-slim` transport test; it is not the chart-capable image and must not be silently repointed. The large PNG output path, explicit independent launch/command consent and end-to-end plotting must be reviewed separately.
5. **Model consent and academic scope:** No potentially billed model request is authorized. Session 009's provider transport checks are not an official model-equivalent chart benchmark or Terra-accuracy evaluation.

**Decision:** Pinning the observed platform-specific manifest *as a documented candidate* is justified by user-supplied registry metadata. Treating the resulting Docker environment as built, reproducible, secure or assignment-equivalent is not justified yet.
