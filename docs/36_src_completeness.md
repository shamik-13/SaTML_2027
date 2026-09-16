# src/ completeness audit — is anything the paper needs still in proto/?

## Answer

**One real dependency was found and fixed.** Everything else the paper needs was already in `src/`.

## What was verified

- **All 51 artefacts** the paper's build/validation chain reads (`make_appendix_tables.py`,
  `make_figures*.py`, `paper.ipynb`, `runner.py`, and the `t45`/`t61`/`t65` gates) have a producer in
  `src/lib`. Zero orphans. The other 22 artefacts in `src/lib/out` are legacy and unused.
- **Every intra-package import in `src/lib` resolves inside `src/lib`** (`h_stream`, `h_meta`,
  `h6_procs`, `t49`, `t51`, `t53`, `t54`).
- LSPR23 inputs come from a `/tmp` cache the user derives with the documented `awk` recipes, not from
  `proto/`.

## The defect

`src/lib/t51_R7_ait.py:50` hard-coded

```python
data = Path(__file__).resolve().parents[2] / "proto" / "data"
```

so the paper's **second-dataset transfer result (78 of 79)** read its inputs from `proto/data/`.
`t54_ait_suppression` and `t67_ait_order` import `t51`, so the whole AIT chain inherited it. And
`src/data/README.md` did not mention AIT-LDSv2.0 at all — the reproduction package could neither find
the inputs nor tell a reader where to get them.

I nearly dismissed this as a comment: three of the four hits are a comment, a docstring and an error
string. The fourth was executable.

**Fixed by:** moving the eight `NF__*_netflows.zip` files (261 MB) plus `NF__label_info.txt` and the
dataset's own README from `proto/data/` to `src/data/ait/`; repointing `t51` at
`parents[1]/"data"/"ait"` with an `AIT_ZIP_DIR` override; documenting AIT-LDSv2.0 in
`src/data/README.md` (record, the eight organisations, what the pipeline reads, the TCP-only scope).
Verified by resolving the path and finding all 8 zips. The stale `proto/` copy of `t51` was repointed
too, so no file in the repo names a location that no longer exists.

## What proto/ still holds, and why that is fine

| contents | keep in proto? |
|---|---|
| the six gates (`t45`, `t61`, `t65`, `t68`, `t69`, `t70`) | yes — QA tooling, not paper implementation |
| 15 `*_selftest.py` | yes — they test, they do not produce |
| ~19 early exploratory scripts (`t1`–`t14`, `t19`) | yes — superseded history |
| **stale duplicates of 48 modules** | **yes, but see the hazard** |

## The hazard, now gated

`src/tools/` holds a `proto -> src/lib` pipeline (`strip_comments.py`, then `make_importable.py`),
which makes `proto` *look* canonical. It is not:

- 46 of the 48 same-named modules differ, and several differ in real code. `src/lib/t48_W3_dilution.py`
  carries the `episodes_keyhash` (canonical-order) arm that `proto/t48_W3_dilution.py` **does not
  contain at all** — and the paper's headline order convention depends on it.
- Five paper-critical modules exist only in `src/lib` with no proto ancestor: `t52_B1_synthetic`,
  `t53_ordering`, `t54_ait_suppression`, `t66_nonoracle_padding`, `t67_ait_order` — between them the
  AIT transfer, the ordering arms, the non-oracle padding analysis and the synthetic ADDIS run.
- `strip_comments.py` currently **fails its own AST self-check**, so the pipeline cannot be run anyway.

Regenerating `src/lib` from `proto` would therefore silently revert the paper's implementation.
`proto/t70_src_completeness.py` pins the three invariants that make that impossible to do by accident,
and reports the divergence as INFO so it stays visible.

**Injection-tested:** reverting `t51` to the proto path, hiding a proto path in an env-var default
(`AIT_ZIP_DIR = os.environ.get(..., "../../proto/data")`), and adding an import that does not resolve
inside `src/lib` each fail the gate. Two earlier false positives were fixed first — imports are now
parsed with `ast` rather than a regex (prose in a docstring, "…from a host already talking to it…",
matched a regex), and the proto-path check runs on de-commented source, since a comment cannot create
a dependency and "proto" is also the network-protocol column name.

**Gate set is now six:** `t45` 268, `t61` 200, `t65` 90, `t68` 2, `t69` 26 objects / 0 drift,
`t70` 3. Paper compiles clean.
