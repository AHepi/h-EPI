"""A prototype of "mini": one artifact template, declared wiring, an
append-only record.

Nothing here mints a status. Artifacts are produced, formats are checked,
citations are byte-checked, and every outcome is a typed entry on the record;
no outcome makes any other artifact stand or fall. See ``docs/mini/SPEC.md``.
"""

# Importing the blind-spot module registers its kernels, its transforms and its
# two machine seats. A registration is an import: nothing here is wired by a
# consumer knowing about it.
from creib.forge.mini import blindspot as _blindspot  # noqa: E402,F401
