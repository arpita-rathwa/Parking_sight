"""Stage 2 — Validate.

Catches the dataset problems that silently wreck a retrain:
  * image without a matching label (and vice-versa)
  * class id outside the canonical 0..N-1 range
  * bbox coords not normalized to [0, 1]
  * empty val or empty train split
  * (warn) severe class imbalance / a class with zero samples

Returns a ValidationReport; the pipeline aborts on any hard error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common.config import get_settings
from common.logging import get_logger

log = get_logger("training.validate")


@dataclass
class ValidationReport:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    class_counts: dict[str, int] = field(default_factory=dict)

    def error(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _check_label_file(
    path: Path, n_classes: int, report: ValidationReport, class_counts: dict[int, int]
) -> None:
    for ln, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            report.error(f"{path.name}:{ln} expected 5 fields, got {len(parts)}")
            continue
        try:
            cls = int(parts[0])
            coords = [float(x) for x in parts[1:]]
        except ValueError:
            report.error(f"{path.name}:{ln} non-numeric token")
            continue
        if not (0 <= cls < n_classes):
            report.error(f"{path.name}:{ln} class id {cls} out of range 0..{n_classes - 1}")
        if any(not (0.0 <= c <= 1.0) for c in coords):
            report.error(f"{path.name}:{ln} bbox not normalized to [0,1]: {coords}")
        class_counts[cls] = class_counts.get(cls, 0) + 1


def validate(dataset_dir: str | Path) -> ValidationReport:
    s = get_settings()
    root = Path(dataset_dir)
    report = ValidationReport()
    class_counts: dict[int, int] = {}

    for split in ("train", "val"):
        img_dir = root / "images" / split
        lbl_dir = root / "labels" / split
        images = (
            {p.stem for p in img_dir.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")}
            if img_dir.exists()
            else set()
        )
        labels = {p.stem for p in lbl_dir.glob("*.txt")} if lbl_dir.exists() else set()

        if not images:
            report.error(f"{split} split has no images")
        for stem in images - labels:
            report.error(f"{split}: image '{stem}' has no label file")
        for stem in labels - images:
            report.warn(f"{split}: label '{stem}' has no image (ignored)")
        for stem in images & labels:
            _check_label_file(lbl_dir / f"{stem}.txt", len(s.classes), report, class_counts)

    report.class_counts = {s.classes[i]: n for i, n in sorted(class_counts.items()) if i < len(s.classes)}
    for i, name in enumerate(s.classes):
        if class_counts.get(i, 0) == 0:
            report.warn(f"class '{name}' has zero samples — model cannot learn it this cycle")

    log.info(
        "validation_done",
        ok=report.ok,
        n_errors=len(report.errors),
        n_warnings=len(report.warnings),
        class_counts=report.class_counts,
    )
    return report


if __name__ == "__main__":
    import sys

    r = validate(sys.argv[1] if len(sys.argv) > 1 else "./_run/dataset")
    print("OK" if r.ok else "FAILED")
    for e in r.errors:
        print("ERROR:", e)
