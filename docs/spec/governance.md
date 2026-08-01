# emerge.yaml Spec Governance

The `emerge.yaml` manifest is the contract every Orcha agent implements. Once
external agents exist, a breaking change to the spec breaks everyone. We treat
the spec like a wire protocol: **frozen by default, versioned, and changed only
through an RFC.**

## Versioning

- Every manifest may declare `schema_version` (defaults to `"1.0"`).
- The canonical schema lives at
  [`docs/spec/emerge-yaml.schema.json`](emerge-yaml.schema.json).
- **Backward-compatible** additions (new optional field) bump the **minor**
  version (`1.0` → `1.1`).
- **Breaking** changes (removing/renaming a field, tightening a constraint) bump
  the **major** version (`1.x` → `2.0`) and require a migration note.

## RFC process

1. **Open an issue** using the spec-change label describing the problem, the
   proposed change, and who it affects. Do not send a spec PR first.
2. **Discussion** stays on the issue until there is rough consensus. Maintainers
   look for: does this break existing agents? can it be additive? is it within
   the runtime's scope (vs. an agent-local concern)?
3. **Draft RFC** — a short doc under `docs/spec/rfcs/NNNN-title.md` covering:
   motivation, proposed schema delta, compatibility/migration, alternatives.
4. **Acceptance** requires maintainer sign-off. On accept: update the JSON
   Schema, bump `schema_version`, update `docs/emerge-yaml.md`, and add the
   migration note.
5. **Rejection** is recorded on the RFC for the historical record.

## What does NOT need an RFC

- Documentation fixes, examples, clarifications.
- New agents/bridges that use the spec as-is.
- Validation bug fixes that bring behavior in line with the published schema.

## Stability commitment

From launch, `schema_version: "1.0"` is stable. Tooling MUST accept manifests
that omit `schema_version` and treat them as `1.0`. Deprecations are announced
at least one minor version before removal.
