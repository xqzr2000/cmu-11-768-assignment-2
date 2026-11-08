# Session 010 — OCI image and chart wheel-lock provenance

**Status, 2026-11-07 (America/Vancouver) / 2026-11-08 UTC:** The post-integration Codespace run verified the 14-package chart-wheel **metadata** audit and **29/29 focused offline tests** (12 Dockerfile recipe, 17 private context). The prior six-suite **77/77** total predates the changes; a new all-six run is pending. No image was pulled, built or started and no wheel archive was downloaded or installed. A lockfile hash is not proof of a trusted image or functioning chart environment. Session 010 remains active on its unmerged feature branch.

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

`scripts/check_chart_wheel_lock_offline.py` reads the **actual committed** `uv.lock` and requirements file; it recursively checks the four roots' **unconditional** dependency closure, exact versions, registry provenance, selected wheel labels, and hashes. It fails closed if new marker/extra dependency behavior appears or a pinned hash or package changes. It neither downloads nor installs wheels. The checker **passed in the user Codespace** after pulling branch commit `b3983cc`; it reported 14 checked hashes (4 direct, 10 transitive) and finished with a metadata-consistency PASS. It has **not** downloaded, rehashed or installed the actual wheel bytes.

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_chart_wheel_lock_offline.py
git status --short --branch
```

**Observed result (user terminal log):** `Chart wheel lock audit: 14 fully hashed package(s), CPython 3.12 / linux/amd64 (manylinux)`; `Direct roots: 4; transitive: 10`; all 14 wheel filenames listed; final `PASS: requirements match the committed uv.lock metadata; no network/download/install.` The script also explicitly printed `NOT VERIFIED: actual package download, wheel integrity, pip resolution or Docker build.` If the graph changes, the offline auditor must block rather than silently omit a package.

## Remaining gaps before a real chart-capable image

1. **Wheel retrieval/install:** We have only lockfile-published wheel hashes. No wheel bytes have been downloaded and rehashed or installed against this OCI image. A future approved build must enforce `pip install --require-hashes --only-binary=:all:` using the complete reviewed file and confirm dependency compatibility and plotting imports.
2. **Dockerfile/build-context integration:** Implemented and **focused-test verified**: `chart_image_recipe.py` now requests a hashed pip install; the minimal context includes the reviewed 14-package lock, and both source and staged requirements are audited against `uv.lock`. The full suite and actual installer execution remain unverified. Do not equate validated Dockerfile text with a completed image build.
3. **Platform and image integrity:** The observed manifest corresponds to `linux/amd64` as reported by the public registry. No actual layer pull or signed-origin verification was performed; building a chart image requires separately approved Docker operations and a fixed target platform.
4. **Sandbox architecture:** Current gateway's default image is still the historical floating `python:3.12-slim` transport test; it is not the chart-capable image and must not be silently repointed. The large PNG output path, explicit independent launch/command consent and end-to-end plotting must be reviewed separately.
5. **Model consent and academic scope:** No potentially billed model request is authorized. Session 009's provider transport checks are not an official model-equivalent chart benchmark or Terra-accuracy evaluation.

**Decision:** Pinning the observed platform-specific manifest *as a documented candidate* is justified by user-supplied registry metadata. Treating the resulting Docker environment as built, reproducible, secure or assignment-equivalent is not justified yet.

## Offline hashed-wheel staging implementation — focused tests passed

The inert image recipe now adds `COPY requirements/chart-cp312-linux-amd64.txt /opt/assignment/chart-requirements.txt` before its pip step. It **requests** `pip install --no-cache-dir --require-hashes --only-binary=:all: -r /opt/assignment/chart-requirements.txt`, rather than installing the four plotting roots as un-hashed command arguments. No such install has actually been executed.

The context allowlist now includes exactly one new file, `requirements/chart-cp312-linux-amd64.txt`, in a private `requirements/` subdirectory; Dockerfile, vetted CSVs and the fixed extractor are unchanged permitted categories. A reusable no-network audit validates the source and staged bytes against `uv.lock` (not just against a forgeable manifest checksum). The existing wheel-audit CLI still uses this logic.

Updated offline tests cover the Dockerfile copy/install ordering, exact context paths, permission and cleanup policy, extra/unhashed requirements, changed wheel hashes with forged manifests, and missing/symlinked/unhashed source locks. CI continues to run the guarded image/context suites and the separate wheel audit.

**Focused Codespace verification passed at `aee45e6`:** 14 package hashes audited, image recipe **12/12** passed (0.002 s), private context **17/17** passed (4.275 s), clean synchronized working tree. Broader suites were not rerun at this checkpoint. We have not downloaded/rehash-verified wheel bytes, tested pip resolution, built an image or launched Docker. The minimal image still omits SciPy and seaborn supported by the course environment; full environment equivalence cannot be claimed.

## Pause / restart handoff

**Last verified local Git state:** clean feature branch `feature/session-010-chart-agent-controller` tracking origin at `aee45e6` (before this verification-journal commit). Keep the branch; do **not** merge, delete it or rerun billable model probes. Pull the journal commit before full regression tests.

**Next verification step (offline-only):** Pull the verification documentation, run all six guarded Session 010 test scripts (expected 82 if unchanged), provider and validator regressions, structural tests/preflight, and inspect CI via PR. Do not attempt a real image build or plotting smoke test until separately reviewed and approved.

**Resume:**

```bash
cd /workspaces/cmu-11-768-assignment-2
git switch feature/session-010-chart-agent-controller
git pull --ff-only
git status --short --branch
uv run python scripts/check_chart_wheel_lock_offline.py
```

For a concise map of all sessions and the full restart plan, see [Learning Progress — Pause / resume checkpoint](Learning-Progress.md#pause--resume-checkpoint--2026-11-07-americavancouver).
