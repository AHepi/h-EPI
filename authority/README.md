# Authority evidence

The CR-1.0 PDF is the sole semantic and formal authority. It is intentionally absent from this repository. `source_manifest.json` pins its identity, size, page count, geometry, and active span; `source_anchors.json` pins the DF-10 and TH-3 clause locations, literal word-snapshot digests, reviewed readings, source marks, and source-declared dependencies.

Anchor identity is content-addressed:

```text
sha256("CR-EIB/source-anchor/v1\0" + canonical_payload_json)
```

The canonical profile permits only objects, arrays, strings, integers, Booleans, and null. Object keys are sorted, UTF-8 is retained, and insignificant whitespace is removed. Floats, duplicate keys, and non-finite values are rejected.

Changing an anchor creates a new identity. Existing declarations keep pointing at the old identity and therefore fail closed. Interpretation choices and proof verdicts live under `bridge/`, outside these records.

The cold-start ambiguity `SEM-19` gives TH-3 the wrong location. Visual review against the authority fixes it at physical PDF page 230, printed footer 229; the verifier rejects the stale 229/228 locator.
