import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


GROUP_COUNTS = {
    "strong": 10,
    "medium": 15,
    "weak": 15,
    "straggler": 10,
}

STALENESS = {
    "strong": 0,
    "medium": 0,
    "weak": 1,
    "straggler": 2,
}


class SystemHeterogeneityEmulator:
    """Deterministic logical staleness emulator for controlled pilot runs."""

    def __init__(self, args, clients):
        self.enabled = getattr(args, "system_profile", "homogeneous") != "homogeneous"
        requested_seed = getattr(args, "system_seed", None)
        self.seed = int(getattr(args, "seed", 0) if requested_seed is None else requested_seed)
        self.profile = getattr(args, "system_profile", "homogeneous")
        self.history = defaultdict(list)
        self.groups = self._assign_groups(len(clients))
        for client, group in zip(clients, self.groups):
            client.resource_group = group
        output = Path(str(args.output))
        requested = getattr(args, "system_log", "")
        self.csv_path = Path(requested) if requested else output.with_suffix(".system.csv")
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.csv_path.open("w", encoding="utf-8", newline="")
        self.writer = csv.DictWriter(self.handle, fieldnames=[
            "round", "client_id", "resource_group", "requested_staleness",
            "effective_staleness", "current_norm", "effective_norm", "norm_ratio",
            "current_cosine_to_mean", "effective_cosine_to_mean",
            "stale_delta_norm", "aggregator_score",
            "selected", "selection_rank"
        ])
        self.writer.writeheader()
        meta = self.csv_path.with_name(self.csv_path.stem + ".meta.json")
        meta.write_text(json.dumps({
            "profile": self.profile,
            "system_seed": self.seed,
            "groups": self.groups,
            "staleness_by_group": STALENESS,
        }, indent=2), encoding="utf-8")

    def _assign_groups(self, num_clients):
        if self.profile == "homogeneous":
            return ["medium"] * num_clients
        if num_clients != sum(GROUP_COUNTS.values()):
            raise ValueError("four_tier pilot currently requires exactly 50 clients")
        groups = [g for g, n in GROUP_COUNTS.items() for _ in range(n)]
        rng = np.random.default_rng(self.seed)
        rng.shuffle(groups)
        return groups

    def apply(self, updates):
        effective = []
        effective_staleness = []
        for client_id, current in enumerate(updates):
            history = self.history[client_id]
            history.append(np.asarray(current, dtype=np.float32).copy())
            requested = STALENESS[self.groups[client_id]] if self.enabled else 0
            actual = min(requested, len(history) - 1)
            effective.append(history[-1 - actual])
            effective_staleness.append(actual)
        return np.asarray(effective, dtype=np.float32), effective_staleness

    @staticmethod
    def _cosine_rows(matrix, reference):
        ref_norm = float(np.linalg.norm(reference))
        row_norms = np.linalg.norm(matrix, axis=1)
        denom = row_norms * ref_norm
        dots = matrix @ reference
        return np.divide(dots, denom, out=np.zeros_like(dots), where=denom > 0)

    def record(self, round_id, current_updates, effective_updates,
               effective_staleness, aggregator):
        selected = list(getattr(
            aggregator, "last_selected_indices", range(len(effective_updates))))
        selected_set = set(int(i) for i in selected)
        ranks = {int(client_id): rank for rank, client_id in enumerate(selected)}
        scores = getattr(aggregator, "last_scores", None)
        score_map = {}
        if scores is not None:
            score_map = {int(i): float(score) for i, score in scores}
        current_mean = np.mean(current_updates, axis=0)
        current_cosines = self._cosine_rows(current_updates, current_mean)
        effective_cosines = self._cosine_rows(effective_updates, current_mean)
        for client_id, (current, effective) in enumerate(
                zip(current_updates, effective_updates)):
            group = self.groups[client_id]
            current_norm = float(np.linalg.norm(current))
            effective_norm = float(np.linalg.norm(effective))
            self.writer.writerow({
                "round": round_id,
                "client_id": client_id,
                "resource_group": group,
                "requested_staleness": STALENESS[group] if self.enabled else 0,
                "effective_staleness": effective_staleness[client_id],
                "current_norm": current_norm,
                "effective_norm": effective_norm,
                "norm_ratio": effective_norm / current_norm if current_norm else "",
                "current_cosine_to_mean": float(current_cosines[client_id]),
                "effective_cosine_to_mean": float(effective_cosines[client_id]),
                "stale_delta_norm": float(np.linalg.norm(effective - current)),
                "aggregator_score": score_map.get(client_id, ""),
                "selected": int(client_id in selected_set),
                "selection_rank": ranks.get(client_id, ""),
            })
        self.handle.flush()

    def close(self):
        self.handle.close()
