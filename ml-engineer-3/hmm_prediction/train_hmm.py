"""Train the Gaussian HMM and persist it.

Pipeline:
  1. build observation matrix from congestion_scores (all zones)
  2. standardize features
  3. fit GaussianHMM (diagonal covariance) via EM
  4. RELABEL hidden states by severity (mean impact_score) so index order is
     calm -> critical. This is the key step for interpretability.
  5. persist model + scaler (joblib) and a meta.json (transition matrix, state
     means, log-likelihood) for the explain/visualize layers.
"""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

import numpy as np

from common.config import get_settings
from common.logging import get_logger
from common.storage import Storage
from hmm_prediction import features
from hmm_prediction.states import state_names

log = get_logger("hmm.train")

MODEL_KEY = "hmm/model.joblib"
META_KEY = "hmm/meta.json"


def train(n_iter: int = 200, random_state: int = 42) -> dict:
    import joblib
    from hmmlearn.hmm import GaussianHMM
    from sklearn.preprocessing import StandardScaler

    s = get_settings()
    n = s.hmm_n_states

    X_all, lengths, zones = features.training_matrix(min_len=s.hmm_min_history)
    scaler = StandardScaler().fit(X_all)
    Xs = scaler.transform(X_all)

    model = GaussianHMM(n_components=n, covariance_type="diag", n_iter=n_iter, random_state=random_state)
    model.fit(Xs, lengths)
    loglik = float(model.score(Xs, lengths))

    # severity ordering: rank states by mean impact_score in ORIGINAL units
    means_orig = scaler.inverse_transform(model.means_)
    impact_idx = features.FEATURE_NAMES.index("impact_score")
    severity = means_orig[:, impact_idx]
    perm = [int(i) for i in np.argsort(severity)]  # model-state indices, ascending severity

    # severity-ordered transition matrix (for explain + viz)
    transmat_sev = model.transmat_[np.ix_(perm, perm)]

    storage = Storage()
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "model.joblib"
        joblib.dump({"model": model, "scaler": scaler}, p)
        storage.put_file(s.s3_bucket_models, MODEL_KEY, p)

    meta = {
        "trained_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "n_states": n,
        "state_names": state_names(n),
        "perm": perm,
        "feature_names": features.FEATURE_NAMES,
        "severity_impact_means": [float(severity[i]) for i in perm],
        "transmat_severity": transmat_sev.tolist(),
        "state_means_severity": means_orig[perm].tolist(),
        "log_likelihood": loglik,
        "n_observations": int(len(X_all)),
        "n_zones": len(zones),
    }
    storage.put_json(s.s3_bucket_models, META_KEY, meta)

    log.info("hmm_trained", n_states=n, n_zones=len(zones), n_obs=len(X_all), log_likelihood=round(loglik, 1))
    return meta


if __name__ == "__main__":
    print(train())
