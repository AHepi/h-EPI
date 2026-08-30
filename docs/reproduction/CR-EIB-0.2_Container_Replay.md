# CR-EIB-0.2 container replay

## Claim boundary

The Dockerfile is the normative cold-start image definition. Each replay
evidence instance is bound to the built image's immutable Docker content ID and,
when the image is published, should also record its OCI manifest digest. The
DevContainer uses the same Dockerfile only as an editor convenience. This
environment reproduces the reviewed executable checks; it is not the CR-1.0
semantic authority, does not accept a source mapping, and does not unblock full
bridge conformance.

The image is scoped to `linux/amd64`. It still shares the host kernel, and this
repository does not claim that independent image builds are bit-for-bit
identical. Release evidence should retain the immutable Docker content ID; if
the image is published, it should additionally retain the OCI manifest digest.

## Frozen inputs

| Input | Pin |
|---|---|
| Ubuntu base | `ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517` |
| Ubuntu archive | snapshot `20260828T000000Z` |
| TLS bootstrap | `ca-certificates=20260601~24.04.1`, authenticated by signed snapshot metadata; peer verification is disabled only while installing this package into the minimal base, then immediately required |
| `pdftotext` | Ubuntu `poppler-utils=24.02.0-1ubuntu9.9` |
| `pdfinfo` | Poppler `26.05.0`, source SHA-256 `6fef27ff04f37db43054c86bcdff6128c9fb1f6af4ef3c8b369a7e9abd68d0bb` |
| Lean | `4.33.1`, release archive SHA-256 `890afd185370f85666025b883914ab4f4b339136f8c96167b69cfb62aecaf235`, compiler commit `819816b2e0a3bf405af45ae5c7af2491d8f5bee6` |
| Python | Ubuntu snapshot Python 3.12 plus the SHA-256 wheel lock in `requirements-container.txt` |

The mixed Poppler pair is deliberate: it preserves the provenance already
bound into the source anchors. Poppler 26.05.0 is installed under an isolated
prefix, and only its `pdfinfo` is placed ahead of Ubuntu's tools. The image does
not contain Elan, an `LD_PRELOAD` shim, or `LEAN_FIXED_APP_PATH`.

## Build and smoke replay

From a clean repository root, build the image without substituting any build
arguments:

```sh
docker build \
  --platform linux/amd64 \
  --pull=false \
  --file .devcontainer/Dockerfile \
  --tag cr-eib-replay:0.2 \
  .

replay_image_id="$(docker image inspect --format '{{.Id}}' cr-eib-replay:0.2)"
docker image inspect \
  --format 'container_image_id={{.Id}} repo_digests={{json .RepoDigests}}' \
  "${replay_image_id}"
```

The build may use the network only to obtain the content-pinned inputs. The
smoke replay runs afterward without a network and without a writable root
filesystem:

```sh
repository_root="$(pwd -P)"
replay_image_id="$(docker image inspect --format '{{.Id}}' cr-eib-replay:0.2)"
docker run --rm \
  --platform linux/amd64 \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --mount "type=bind,src=${repository_root},dst=/repo,readonly" \
  --workdir /repo \
  "${replay_image_id}" \
  bash /repo/tools/container_smoke.sh
```

Without the authority PDF, the smoke replay must report operational `PARTIAL`,
mapping fidelity `UNREVIEWED`, bridge conformance `BLOCKED`,
`authority_pdf_checked=false`, and `formal_replay_checked=true`. CI exercises
this path. It also rebuilds a clean copy of the formal package and byte-compares
the exact 14-line release axiom output with
`docs/audits/CR-EIB-0.2_Release_Axiom_Transcript.txt`. The Lean Action remains
the independent namespace-wide zero-axiom audit; the published audit packet
records the earlier 254-declaration result at its pinned commit.

## Full operational replay

Set `authority_pdf` to an absolute path for a lawfully held copy of the pinned
authority. The file is mounted read-only under its expected checksum filename;
it is never copied into the image or Docker build context.

```sh
repository_root="$(pwd -P)"
authority_pdf="$(realpath '/path/to/Creativity_Semantic_Model_CR-1.0(1).pdf')"
replay_image_id="$(docker image inspect --format '{{.Id}}' cr-eib-replay:0.2)"

docker run --rm \
  --platform linux/amd64 \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --mount "type=bind,src=${repository_root},dst=/repo,readonly" \
  --mount "type=bind,src=${authority_pdf},dst=/authority/Creativity_Semantic_Model_CR-1.0(1).pdf,readonly" \
  --workdir /repo \
  "${replay_image_id}" \
  bash /repo/tools/container_smoke.sh \
    "/authority/Creativity_Semantic_Model_CR-1.0(1).pdf"
```

The full invocation is accepted only if it reports operational `PASS`, mapping
fidelity `UNREVIEWED`, bridge conformance `BLOCKED`, and both replay flags
`true`. The smoke driver asserts that exact tuple mechanically after running
the bootstrap validator, both Python test modes, the formal checksum/build and
axiom transcript checks, and the verifier. The verifier hashes the PDF before
parsing a private copy and then replays the pinned formal package in the same
process invocation.

Any extractor mismatch, anchor mismatch, or formal replay failure is a closed
failure. Do not change source anchors to make the container pass. A consistent
Poppler re-extraction would be a separate, explicitly reviewed evidence
migration with new anchor identities and dependent declaration pins; it is not
part of this environment.

## DevContainer convenience

`.devcontainer/devcontainer.json` builds this same image for `linux/amd64` and
sets `PYTHONPATH` for editor terminals. It does not mount the authority PDF or
run networked setup hooks. Release evidence must use the OCI commands above,
not an editor session.
