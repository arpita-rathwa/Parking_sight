"""Demo visualizations — three figures that explain the model to a judge:

  1. regimes_timeline.png  : a zone's congestion over time, colored by inferred regime
  2. transition_matrix.png : the learned regime transition probabilities
  3. risk_ranking.png      : current per-zone hotspot risk (the forecast)

Saved to ./hmm_reports/ for easy screenshots.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common.config import get_settings  # noqa: E402
from hmm_prediction import features, infer  # noqa: E402
from hmm_prediction.states import state_names  # noqa: E402

OUT = Path("./hmm_reports")
_COLORS = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]  # calm->critical


def _state_colors(n):
    return _COLORS if n == 4 else plt.cm.RdYlGn_r(np.linspace(0, 1, n))


def regimes_timeline(zone_id: str) -> Path:
    model, scaler, meta = infer._load()
    perm = meta["perm"]
    X, ts = features.zone_matrix(zone_id, limit=96)
    Xs = scaler.transform(X)
    states_model = model.predict(Xs)
    rank = {old: r for r, old in enumerate(perm)}
    sev = np.array([rank[s] for s in states_model])

    fig, ax = plt.subplots(figsize=(11, 4))
    impact = X[:, 0]
    ax.plot(range(len(impact)), impact, color="#333", lw=1, alpha=0.6, zorder=1)
    colors = _state_colors(meta["n_states"])
    ax.scatter(range(len(impact)), impact, c=[colors[r] for r in sev], s=36, zorder=2)
    ax.set_title(f"Zone {zone_id}: congestion impact over time, colored by inferred regime")
    ax.set_xlabel("30-min bin")
    ax.set_ylabel("impact score")
    handles = [
        plt.Line2D([0], [0], marker="o", ls="", color=colors[i], label=n)
        for i, n in enumerate(state_names(meta["n_states"]))
    ]
    ax.legend(handles=handles, loc="upper left", ncol=4, fontsize=8)
    OUT.mkdir(exist_ok=True)
    path = OUT / "regimes_timeline.png"
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def transition_matrix() -> Path:
    _, _, meta = infer._load()
    A = np.array(meta["transmat_severity"])
    names = meta["state_names"]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    im = ax.imshow(A, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_yticklabels(names)
    ax.set_xlabel("next regime")
    ax.set_ylabel("current regime")
    ax.set_title("Learned regime transition probabilities")
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(
                j,
                i,
                f"{A[i, j]:.2f}",
                ha="center",
                va="center",
                color="white" if A[i, j] > 0.5 else "black",
                fontsize=9,
            )
    fig.colorbar(im, fraction=0.046)
    OUT.mkdir(exist_ok=True)
    path = OUT / "transition_matrix.png"
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def risk_ranking() -> Path:
    preds = infer.forecast_all(persist=False)
    zones = [p["zone_id"] for p in preds]
    risks = [p["risk_score"] for p in preds]
    colors = ["#e74c3c" if r >= 0.66 else "#e67e22" if r >= 0.33 else "#2ecc71" for r in risks]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(zones[::-1], risks[::-1], color=colors[::-1])
    ax.set_xlim(0, 1)
    ax.set_xlabel("hotspot risk (next 30 min)")
    ax.set_title("Predicted enforcement priority — pre-staging forecast")
    for i, r in enumerate(risks[::-1]):
        ax.text(r + 0.01, i, f"{r:.2f}", va="center", fontsize=8)
    OUT.mkdir(exist_ok=True)
    path = OUT / "risk_ranking.png"
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def generate_all(sample_zone: str | None = None) -> list[Path]:
    s = get_settings()  # noqa: F841
    zone = sample_zone or (features.list_zones() or ["zone_00"])[0]
    return [regimes_timeline(zone), transition_matrix(), risk_ranking()]
