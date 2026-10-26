# SkillPath AI
**From Career Recommendation to Career Readiness**
Intelligent skill-gap analysis and personalised career-path recommendation using data science.
Course project: Data Science Ecosystem

```
Student skills -> Career match -> Skill gap -> Priority skills -> Personalised roadmap
```

## What it does (the four questions)
| Question | Dashboard tab | Method |
|---|---|---|
| What skills do I have? | 1. My Skills | Self-rated levels (1-5) across 44 skills in 8 categories |
| What career suits me? | 2. Career Matches | Weighted readiness + cosine similarity + interest match, with a plain-English "why" |
| What skills am I missing? | 3. Skill Gap | `gap = max(required - current, 0)`, `priority = importance x gap`, radar chart |
| What should I learn next? | 4. Learning Roadmap | Prerequisite-aware ordering, study hours -> weeks, readiness-after-each-step curve |
| (data-science view) | 5. Data Insights | Career x skill heatmap, in-demand skills, career similarity, PCA career map |

## Novelty
Existing systems stop at *Student -> Job/Career recommendation*. SkillPath AI continues:
*Career match -> Skill gap -> Priority skills -> Personalised path*, and **explains why** each career is recommended.
It also shows **career readiness before/after** completing roadmap steps.

## How to run (Windows / Mac / Linux)
```bash
python -m venv venv
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py             # opens http://localhost:8501
```
Optional:
```bash
python build_data.py     # regenerate the CSVs in data/ after editing the career/skill definitions
python evaluation.py     # run tests + persona evaluation (writes results/)
```

## Project structure
```
app.py           Streamlit dashboard (UI only)
skillpath.py     Core logic: matching, skill gap, roadmap, analytics (pandas + numpy)
build_data.py    Defines careers, skills, requirements, prerequisites -> writes data/*.csv
personas.py      12 hand-written student profiles (demo + evaluation)
evaluation.py    Invariant tests + persona accuracy + noise-robustness test
data/            skills.csv, careers.csv, career_skills.csv
results/         persona_results.csv, robustness_results.csv, evaluation_output.txt
```

## Method
**Data.** 10 careers x 44 skills. Each career-skill pair has a *required level* (1-5) and an *importance* (1-5).
Each skill has a category, estimated study hours per level, prerequisites and a suggested learning resource.

**Career match score** = 0.60 x Readiness + 0.25 x Skill-shape fit + 0.15 x Interest match
- *Readiness* = sum(importance x min(current, required) / required) / sum(importance)
- *Skill-shape fit* = cosine similarity between the student vector and the career requirement vector
- *Interest match* = 1 if the career's domain is one the student selected (weights rescale if none selected)

**Skill gap.** For the target career: `gap = max(required - current, 0)`, `priority = importance x gap`.

**Roadmap.** (1) every skill with a gap; (2) add missing prerequisites (e.g. Docker needs Linux) up to level 2;
(3) topological order, highest priority first among skills whose prerequisites are done;
(4) hours = gap x hours-per-level, converted to weeks at the student's weekly study time;
(5) split into 3 phases by share of total study time.

**Data insights.** Cosine similarity between careers, skill-demand counts, and a 2-D PCA (via SVD) of the career x skill matrix.

## Evaluation (python evaluation.py)
- **Invariant tests (all pass):** a student who meets every requirement gets 100% readiness and an empty roadmap;
  an empty profile gets 0%; readiness never decreases as roadmap steps are completed and reaches 100% at the end;
  prerequisites always appear before the skills that need them; weeks are consistent with hours and pace.
- **Persona check (12 profiles):** expected career ranked #1 for 12/12 (Top-1 = 100%, Top-3 = 100%).
- **Noise-robustness (200 perturbed copies per persona: levels +-1, ~15% of skills dropped, 2 random extra skills):**
  average Top-1 = 98%, Top-3 = 100%. Confusions are between genuinely adjacent careers
  (Data Scientist / Data Analyst, Cloud / DevOps, ML Engineer / Data Scientist, Data Analyst / Business Analyst).

## Limitations (state these honestly in your report / viva)
1. **Career requirements are team-curated estimates**, in the style of O*NET / ESCO, not downloaded from them.
   Next step: replace or calibrate them with the O*NET database (onetonline.org) and real job-posting data.
2. **Evaluation is a sanity check, not proof.** The personas and their expected careers were written by the team,
   so 100% is partly expected. A stronger test uses real classmates' profiles and their own judgement of a good fit.
3. Skill levels are **self-rated**; the system does not test skills.
4. Education and experience are collected for the profile card but **not yet used in scoring** (future work).
5. Study-hour estimates and learning-resource suggestions are rough; check that links/courses still exist.
6. Covers 10 careers and 44 skills; adding more is a matter of editing `build_data.py`.

## Future work
Use O*NET / job-posting data for requirements; skill extraction from a resume (NLP);
skill assessments instead of self-rating; learning-to-rank trained on real student outcomes;
use education/experience in scoring; cloud deployment.

## Viva cheat-sheet
- **Novelty?** Not just recommending a career: we compute personalised skill gaps, prioritise them, and turn them
  into an ordered, time-estimated roadmap with an explanation for every recommendation.
- **Why cosine similarity?** It compares the *shape* of the student's skills to the career's requirements regardless of scale.
  We combine it with weighted readiness, which rewards actually meeting required levels.
- **Why these weights (0.60/0.25/0.15)?** Readiness is the most meaningful signal, so it gets the most weight;
  they are adjustable constants in `skillpath.py`, and the evaluation shows results are stable under noise.
- **Where does the data come from?** Team-curated, modelled on O*NET/ESCO structure (limitation 1).
- **How do you validate it?** Invariant tests, 12 personas, a 200-trial noise test (limitation 2 explains the caveat).
- **What is data-science about it?** Feature vectors, similarity measures, weighted scoring, PCA, evaluation under noise.
