"""Evaluation + tests for SkillPath AI.   Run:  python evaluation.py

Part 1 - invariant tests: properties that must always hold if the logic is correct.
Part 2 - persona evaluation: does the recommender rank the expected career highly?
         Saves results/persona_results.csv for your report.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from personas import PERSONAS
from skillpath import SkillPathEngine

engine = SkillPathEngine()
results_dir = Path(__file__).parent / "results"
results_dir.mkdir(exist_ok=True)


def run_tests() -> None:
    # 1. A student who exactly meets a career's requirements has 100% readiness and no gaps/roadmap.
    for career in engine.career_names:
        perfect = engine.req.loc[career][engine.req.loc[career] > 0].to_dict()
        assert abs(engine.readiness(perfect, career) - 100) < 1e-9, career
        assert (engine.skill_gap(perfect, career)["gap"] == 0).all(), career
        assert len(engine.roadmap(perfect, career)) == 0, career

    # 2. An empty profile has 0% readiness everywhere.
    for career in engine.career_names:
        assert engine.readiness({}, career) == 0

    # 3. Readiness never decreases as roadmap items are completed, and reaches 100% at the end.
    for career in engine.career_names:
        rm = engine.roadmap({}, career)
        prev = -1.0
        for k in range(len(rm) + 1):
            r = engine.projected_readiness({}, career, rm, k)
            assert r >= prev - 1e-9, (career, k)
            prev = r
        assert abs(prev - 100) < 1e-6, (career, prev)

    # 4. Prerequisites always come before the skills that need them in the roadmap.
    for career in engine.career_names:
        rm = engine.roadmap({}, career)
        position = dict(zip(rm["skill"], rm["order"]))
        for skill, pos in position.items():
            for p in engine.prereqs.get(skill, []):
                if p in position:
                    assert position[p] < pos, f"{career}: {p} must come before {skill}"

    # 5. Weeks are consistent with hours and hours/week.
    rm = engine.roadmap({}, "Data Scientist", hours_per_week=10)
    assert abs(rm["week_end"].iloc[-1] - rm["hours"].sum() / 10) < 0.2

    # 6. Match scores are within 0-100 and sorted.
    m = engine.match_careers(PERSONAS[0]["skills"], PERSONAS[0]["interests"])
    assert m["match_score"].between(0, 100).all()
    assert m["match_score"].is_monotonic_decreasing

    print("All invariant tests passed.")


def run_persona_eval() -> pd.DataFrame:
    rows = []
    for p in PERSONAS:
        ranked = engine.match_careers(p["skills"], p["interests"])
        ranked_no_interest = engine.match_careers(p["skills"], None)
        names = ranked["career"].tolist()
        names_ni = ranked_no_interest["career"].tolist()
        rows.append(
            dict(
                persona=p["name"],
                expected=p["expected"],
                top1=names[0],
                rank_of_expected=names.index(p["expected"]) + 1,
                top1_hit=names[0] == p["expected"],
                top3_hit=p["expected"] in names[:3],
                top1_without_interests=names_ni[0],
                top3_hit_without_interests=p["expected"] in names_ni[:3],
                top1_score=ranked["match_score"].iloc[0],
            )
        )
    df = pd.DataFrame(rows)
    df.to_csv(results_dir / "persona_results.csv", index=False)
    return df


def run_robustness(trials: int = 200, seed: int = 42) -> pd.DataFrame:
    """Stress test: every trial perturbs a persona (levels +-1, ~15% of skills dropped,
    two random unrelated skills added at level 1-2) and checks the expected career still ranks well."""
    rng = np.random.default_rng(seed)
    rows = []
    for p in PERSONAS:
        top1 = top3 = 0
        confused = {}
        for _ in range(trials):
            noisy = {}
            for skill, level in p["skills"].items():
                if rng.random() < 0.15:
                    continue
                noisy[skill] = int(np.clip(level + rng.integers(-1, 2), 1, 5))
            for skill in rng.choice(engine.skill_names, size=2, replace=False):
                noisy.setdefault(skill, int(rng.integers(1, 3)))
            names = engine.match_careers(noisy, p["interests"])["career"].tolist()
            top1 += names[0] == p["expected"]
            top3 += p["expected"] in names[:3]
            if names[0] != p["expected"]:
                confused[names[0]] = confused.get(names[0], 0) + 1
        rows.append(
            dict(persona=p["name"], expected=p["expected"], top1_rate=top1 / trials, top3_rate=top3 / trials,
                 most_confused_with=max(confused, key=confused.get) if confused else "-")
        )
    df = pd.DataFrame(rows)
    df.to_csv(results_dir / "robustness_results.csv", index=False)
    return df


if __name__ == "__main__":
    run_tests()
    rob = run_robustness()
    print("\nRobustness under noise (200 perturbed copies per persona):")
    print(rob.assign(top1_rate=rob.top1_rate.map("{:.0%}".format), top3_rate=rob.top3_rate.map("{:.0%}".format))
          .to_string(index=False))
    print(f"Average top-1: {rob['top1_rate'].mean():.0%}   Average top-3: {rob['top3_rate'].mean():.0%}")
    df = run_persona_eval()
    pd.set_option("display.width", 200, "display.max_columns", 20)
    print("\n", df[["persona", "expected", "top1", "rank_of_expected", "top3_hit"]].to_string(index=False))
    n = len(df)
    print(f"\nPersonas: {n}")
    print(f"Top-1 accuracy: {df['top1_hit'].mean():.0%}   Top-3 accuracy: {df['top3_hit'].mean():.0%}")
    print(f"(without using interests)  Top-3 accuracy: {df['top3_hit_without_interests'].mean():.0%}")
    print(f"Mean rank of expected career: {df['rank_of_expected'].mean():.2f}")
