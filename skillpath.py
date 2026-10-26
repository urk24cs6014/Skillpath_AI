"""SkillPath AI - core logic (pandas + numpy only, no UI code).

Pipeline:  Student skills -> Career match -> Skill gap -> Priority skills -> Roadmap

Everything the dashboard shows is computed here, so it can be tested without
Streamlit (see evaluation.py).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

LEVEL_LABELS = {0: "None", 1: "Awareness", 2: "Basic", 3: "Working", 4: "Advanced", 5: "Expert"}

# Career match score = weighted mix of three signals (weights sum to 1).
W_READINESS = 0.60   # how much of the career's weighted requirement the student already meets
W_COSINE = 0.25      # overall shape similarity between student and career skill vectors
W_INTEREST = 0.15    # does the career belong to a domain the student is interested in

PREREQ_MIN_LEVEL = 2  # a missing prerequisite is added to the roadmap up to this level


class SkillPathEngine:
    def __init__(self, data_dir: Path = DATA_DIR):
        data_dir = Path(data_dir)
        self.skills = pd.read_csv(data_dir / "skills.csv").fillna({"prerequisites": ""})
        self.careers = pd.read_csv(data_dir / "careers.csv")
        self.career_skills = pd.read_csv(data_dir / "career_skills.csv")

        self.skill_names = self.skills["skill"].tolist()
        self.career_names = self.careers["career"].tolist()
        self.skill_info = self.skills.set_index("skill")
        self.career_info = self.careers.set_index("career")

        # Career x skill matrices (0 where a skill is not required)
        def matrix(col: str) -> pd.DataFrame:
            m = self.career_skills.pivot(index="career", columns="skill", values=col)
            return m.reindex(index=self.career_names, columns=self.skill_names).fillna(0.0)

        self.req = matrix("required_level")
        self.imp = matrix("importance")

        self.prereqs = {
            row.skill: [p for p in str(row.prerequisites).split("|") if p]
            for row in self.skills.itertuples()
        }
        self.domains = sorted({d for s in self.careers["domains"] for d in s.split("|")})

    # ------------------------------------------------------------------ helpers
    def profile_vector(self, profile: dict) -> np.ndarray:
        """Student profile {skill: level 0-5} -> vector aligned with skill_names."""
        return np.array([float(np.clip(profile.get(s, 0), 0, 5)) for s in self.skill_names])

    def readiness(self, profile: dict, career: str) -> float:
        """Weighted share (0-100) of the career's requirements the student already meets.

        For each required skill: min(current, required) / required, weighted by importance.
        """
        cur = self.profile_vector(profile)
        req = self.req.loc[career].to_numpy()
        imp = self.imp.loc[career].to_numpy()
        mask = req > 0
        met = np.minimum(cur[mask], req[mask]) / req[mask]
        return float(100 * (imp[mask] * met).sum() / imp[mask].sum())

    # ------------------------------------------------------------ 1. career match
    def match_careers(self, profile: dict, interests: list[str] | None = None) -> pd.DataFrame:
        """Rank all careers for a profile. Returns one row per career with a 'why' explanation."""
        interests = set(interests or [])
        cur = self.profile_vector(profile)
        cur_norm = np.linalg.norm(cur)
        rows = []
        for career in self.career_names:
            req = self.req.loc[career].to_numpy()
            ready = self.readiness(profile, career)
            cos = float(cur @ req / (cur_norm * np.linalg.norm(req))) if cur_norm > 0 else 0.0
            career_domains = set(self.career_info.loc[career, "domains"].split("|"))
            interest = 1.0 if interests & career_domains else 0.0

            if interests:
                score = W_READINESS * ready / 100 + W_COSINE * cos + W_INTEREST * interest
            else:  # no interests given -> redistribute the interest weight
                score = (W_READINESS * ready / 100 + W_COSINE * cos) / (W_READINESS + W_COSINE)

            gap = self.skill_gap(profile, career)
            strengths = gap[gap["gap"] == 0].sort_values("importance", ascending=False)["skill"].tolist()
            top_gaps = gap[gap["gap"] > 0]["skill"].head(3).tolist()
            n_req = len(gap)
            n_met = len(strengths)
            why = f"You already meet {n_met} of {n_req} required skills ({ready:.0f}% weighted readiness)."
            if strengths:
                why += " Strongest matches: " + ", ".join(strengths[:3]) + "."
            if top_gaps:
                why += " Biggest gaps: " + ", ".join(top_gaps) + "."
            if interest:
                why += " Aligns with your stated interests."

            rows.append(
                dict(
                    career=career,
                    match_score=round(100 * score, 1),
                    readiness=round(ready, 1),
                    cosine_fit=round(100 * cos, 1),
                    interest_match=bool(interest),
                    skills_met=n_met,
                    skills_required=n_req,
                    why=why,
                )
            )
        return pd.DataFrame(rows).sort_values("match_score", ascending=False).reset_index(drop=True)

    # -------------------------------------------------------------- 2. skill gap
    def skill_gap(self, profile: dict, career: str) -> pd.DataFrame:
        """Per-skill gap for a career, sorted by priority = importance x gap."""
        req = self.req.loc[career]
        imp = self.imp.loc[career]
        rows = []
        for skill in req.index[req > 0]:
            current = float(np.clip(profile.get(skill, 0), 0, 5))
            required = float(req[skill])
            gap = max(required - current, 0.0)
            rows.append(
                dict(
                    skill=skill,
                    category=self.skill_info.loc[skill, "category"],
                    current=current,
                    required=required,
                    gap=gap,
                    importance=float(imp[skill]),
                    priority=float(imp[skill]) * gap,
                    status="Met" if gap == 0 else ("Missing" if current == 0 else "Partial"),
                )
            )
        df = pd.DataFrame(rows)
        # Sort: highest priority first; ties -> more important skills first
        return df.sort_values(["priority", "importance"], ascending=False, kind="stable").reset_index(drop=True)

    # ------------------------------------------------------------- 3. roadmap
    def roadmap(self, profile: dict, career: str, hours_per_week: float = 10.0) -> pd.DataFrame:
        """Prioritised, prerequisite-ordered learning path for a career.

        1. Take every skill with a gap.
        2. Add missing prerequisites (up to PREREQ_MIN_LEVEL) - e.g. Docker needs Linux.
        3. Order topologically (prerequisites first); among skills that are ready to
           learn, pick the highest priority first.
        4. Convert gap -> study hours -> weeks using hours_per_week.
        """
        gap = self.skill_gap(profile, career)
        todo = {
            r.skill: dict(
                target=r.required, current=r.current, importance=r.importance,
                priority=r.priority, reason="Required for " + career,
            )
            for r in gap.itertuples() if r.gap > 0
        }
        if not todo:
            return pd.DataFrame(
                columns=["order", "skill", "category", "current", "target", "gap", "priority", "hours",
                         "week_start", "week_end", "phase", "reason", "resource"]
            )

        # add missing prerequisites (transitively)
        queue = list(todo)
        while queue:
            skill = queue.pop()
            for p in self.prereqs.get(skill, []):
                cur_p = float(np.clip(profile.get(p, 0), 0, 5))
                if p in todo or cur_p >= PREREQ_MIN_LEVEL:
                    continue
                todo[p] = dict(
                    target=float(PREREQ_MIN_LEVEL), current=cur_p,
                    importance=todo[skill]["importance"],
                    priority=todo[skill]["priority"] + 0.5,  # slightly above the skill that needs it
                    reason=f"Prerequisite for {skill}",
                )
                queue.append(p)

        # topological order, highest priority first among available skills
        deps = {s: [p for p in self.prereqs.get(s, []) if p in todo] for s in todo}
        order, placed = [], set()
        while len(order) < len(todo):
            available = [s for s in todo if s not in placed and all(d in placed for d in deps[s])]
            if not available:  # cannot happen with an acyclic prerequisite graph; guard anyway
                available = [s for s in todo if s not in placed]
            nxt = max(available, key=lambda s: (todo[s]["priority"], todo[s]["importance"]))
            order.append(nxt)
            placed.add(nxt)

        rows, cum_hours = [], 0.0
        for i, skill in enumerate(order, start=1):
            t = todo[skill]
            gap_levels = t["target"] - t["current"]
            hours = gap_levels * float(self.skill_info.loc[skill, "hours_per_level"])
            start_week = cum_hours / hours_per_week      # elapsed weeks since you begin
            cum_hours += hours
            end_week = cum_hours / hours_per_week
            rows.append(
                dict(
                    order=i, skill=skill, category=self.skill_info.loc[skill, "category"],
                    current=t["current"], target=t["target"], gap=gap_levels,
                    priority=round(t["priority"], 1), hours=round(hours, 1),
                    week_start=round(start_week, 1), week_end=round(end_week, 1),
                    reason=t["reason"], resource=self.skill_info.loc[skill, "resource"],
                )
            )
        df = pd.DataFrame(rows)

        # phases by share of total study time
        share = (df["hours"].cumsum() - df["hours"] / 2) / df["hours"].sum()
        df["phase"] = np.where(share < 1 / 3, "Phase 1: Build the base",
                               np.where(share < 2 / 3, "Phase 2: Core skills", "Phase 3: Advanced & polish"))
        return df[["order", "skill", "category", "current", "target", "gap", "priority", "hours",
                   "week_start", "week_end", "phase", "reason", "resource"]]

    def projected_readiness(self, profile: dict, career: str, roadmap: pd.DataFrame, n_done: int) -> float:
        """Career readiness (0-100) if the student completes the first n_done roadmap items."""
        updated = dict(profile)
        for r in roadmap.head(n_done).itertuples():
            updated[r.skill] = max(updated.get(r.skill, 0), r.target)
        return self.readiness(updated, career)

    # ------------------------------------------- data-science views (dashboard)
    def skill_demand(self) -> pd.DataFrame:
        """How many careers need each skill, and how important it is on average."""
        needed = (self.req > 0)
        df = pd.DataFrame(
            dict(
                skill=self.skill_names,
                category=self.skills["category"].values,
                careers_needing=needed.sum(axis=0).values,
                avg_importance=(self.imp.where(needed).mean(axis=0)).fillna(0).round(2).values,
                avg_required_level=(self.req.where(needed).mean(axis=0)).fillna(0).round(2).values,
            )
        )
        return df.sort_values(["careers_needing", "avg_importance"], ascending=False).reset_index(drop=True)

    def career_similarity(self) -> pd.DataFrame:
        """Cosine similarity between careers' requirement vectors (shows which careers overlap)."""
        m = self.req.to_numpy()
        norm = np.linalg.norm(m, axis=1, keepdims=True)
        sim = (m / norm) @ (m / norm).T
        return pd.DataFrame(sim.round(2), index=self.career_names, columns=self.career_names)

    def career_map(self, profile: dict | None = None) -> pd.DataFrame:
        """2-D PCA projection (via SVD) of careers, and of the student if a profile is given."""
        m = self.req.to_numpy()
        mean = m.mean(axis=0)
        _, _, vt = np.linalg.svd(m - mean, full_matrices=False)
        comps = vt[:2]
        pts = (m - mean) @ comps.T
        df = pd.DataFrame(dict(name=self.career_names, x=pts[:, 0], y=pts[:, 1], kind="Career"))
        if profile is not None:
            s = (self.profile_vector(profile) - mean) @ comps.T
            df = pd.concat([df, pd.DataFrame([dict(name="You", x=s[0], y=s[1], kind="You")])], ignore_index=True)
        return df
