"""Evaluation metrics for comparing AutoScoring vs human teacher scores."""

from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
from scipy.stats import pearsonr, spearmanr


@dataclass
class EvaluationMetrics:
    sample_count: int
    pearson_correlation: float
    pearson_p_value: float
    spearman_correlation: float
    spearman_p_value: float
    quadratic_weighted_kappa: float
    mean_absolute_error: float
    root_mean_squared_error: float
    mean_human_score: float
    mean_system_score: float
    exact_match_rate: float
    within_1_point_rate: float
    within_2_point_rate: float

    def to_dict(self) -> dict:
        return asdict(self)

    def summary_lines(self) -> list[str]:
        return [
            f"Samples evaluated     : {self.sample_count}",
            f"Pearson correlation   : {self.pearson_correlation:.4f} (p={self.pearson_p_value:.4f})",
            f"Spearman correlation  : {self.spearman_correlation:.4f} (p={self.spearman_p_value:.4f})",
            f"Quadratic Weighted κ  : {self.quadratic_weighted_kappa:.4f}",
            f"Mean Absolute Error   : {self.mean_absolute_error:.4f}",
            f"RMSE                  : {self.root_mean_squared_error:.4f}",
            f"Mean human score      : {self.mean_human_score:.2f}",
            f"Mean system score     : {self.mean_system_score:.2f}",
            f"Exact match rate      : {self.exact_match_rate:.1%}",
            f"Within ±1 point       : {self.within_1_point_rate:.1%}",
            f"Within ±2 points      : {self.within_2_point_rate:.1%}",
        ]


def quadratic_weighted_kappa(
    human_scores: np.ndarray,
    system_scores: np.ndarray,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
) -> float:
    """QWK — standard agreement metric for automated essay/short-answer grading."""
    human = np.round(np.asarray(human_scores, dtype=float)).astype(int)
    system = np.round(np.asarray(system_scores, dtype=float)).astype(int)

    if min_rating is None:
        min_rating = int(min(human.min(), system.min()))
    if max_rating is None:
        max_rating = int(max(human.max(), system.max()))

    num_ratings = max_rating - min_rating + 1
    conf_mat = np.zeros((num_ratings, num_ratings), dtype=float)

    for h, s in zip(human, system):
        conf_mat[h - min_rating, s - min_rating] += 1

    conf_mat /= conf_mat.sum()

    hist_true = conf_mat.sum(axis=1)
    hist_pred = conf_mat.sum(axis=0)

    weights = np.zeros((num_ratings, num_ratings), dtype=float)
    for i in range(num_ratings):
        for j in range(num_ratings):
            weights[i, j] = ((i - j) ** 2) / ((num_ratings - 1) ** 2) if num_ratings > 1 else 0.0

    expected = np.outer(hist_true, hist_pred)
    observed = (weights * conf_mat).sum()
    expected_score = (weights * expected).sum()

    if np.isclose(expected_score, 1.0):
        return 1.0 if np.isclose(observed, 1.0) else 0.0

    return float(1.0 - observed / expected_score)


def compute_metrics(human_scores: list[float], system_scores: list[float]) -> EvaluationMetrics:
    if len(human_scores) != len(system_scores):
        raise ValueError("human_scores and system_scores must have the same length")
    if len(human_scores) < 2:
        raise ValueError("At least 2 samples are required for correlation metrics")

    human = np.asarray(human_scores, dtype=float)
    system = np.asarray(system_scores, dtype=float)
    diffs = np.abs(human - system)

    pearson_r, pearson_p = pearsonr(human, system)
    spearman_r, spearman_p = spearmanr(human, system)
    qwk = quadratic_weighted_kappa(human, system)
    mae = float(np.mean(diffs))
    rmse = float(np.sqrt(np.mean((human - system) ** 2)))

    return EvaluationMetrics(
        sample_count=len(human),
        pearson_correlation=round(float(pearson_r), 4),
        pearson_p_value=round(float(pearson_p), 4),
        spearman_correlation=round(float(spearman_r), 4),
        spearman_p_value=round(float(spearman_p), 4),
        quadratic_weighted_kappa=round(qwk, 4),
        mean_absolute_error=round(mae, 4),
        root_mean_squared_error=round(rmse, 4),
        mean_human_score=round(float(human.mean()), 2),
        mean_system_score=round(float(system.mean()), 2),
        exact_match_rate=round(float(np.mean(diffs == 0)), 4),
        within_1_point_rate=round(float(np.mean(diffs <= 1.0)), 4),
        within_2_point_rate=round(float(np.mean(diffs <= 2.0)), 4),
    )
