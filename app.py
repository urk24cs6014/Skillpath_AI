"""SkillPath AI - interactive dashboard.   Run:  streamlit run app.py

Tabs answer the project's four questions:
  1 My Skills        -> What skills do I currently have?
  2 Career Matches   -> What career suits me?
  3 Skill Gap        -> What skills am I missing?
  4 Learning Roadmap -> What should I learn next?
  5 Data Insights    -> the data-science view behind the recommendations
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from personas import PERSONAS
from skillpath import LEVEL_LABELS, W_COSINE, W_INTEREST, W_READINESS, SkillPathEngine

st.set_page_config(page_title="SkillPath AI", page_icon="🎯", layout="wide")


@st.cache_resource
def get_engine() -> SkillPathEngine:
    return SkillPathEngine()


engine = get_engine()
CATEGORIES = list(dict.fromkeys(engine.skills["category"]))
AUTO = "Auto (best match)"
NO_SAMPLE = "- choose -"
CURRENT_COLOR, REQUIRED_COLOR = "#2a9d8f", "#e76f51"


def init(key, default):
    """Create a session-state value once (avoids Streamlit's 'default value + session state' warning)."""
    if key not in st.session_state:
        st.session_state[key] = default


def load_sample():
    persona = next((p for p in PERSONAS if p["name"] == st.session_state.get("sample_choice")), None)
    if persona is None:
        return
    for cat in CATEGORIES:
        st.session_state[f"sel_{cat}"] = [
            s for s in persona["skills"] if engine.skill_info.loc[s, "category"] == cat
        ]
    for skill, level in persona["skills"].items():
        st.session_state[f"lvl_{skill}"] = int(level)
    st.session_state["interests"] = list(persona["interests"])


def clear_skills():
    for cat in CATEGORIES:
        st.session_state[f"sel_{cat}"] = []


# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("SkillPath AI")
    st.caption("From career recommendation to career readiness")

    st.subheader("About you")
    student_name = st.text_input("Name (optional)", key="student_name")
    education = st.selectbox(
        "Education",
        ["B.E./B.Tech - CSE/IT", "B.E./B.Tech - Other branch", "BCA / MCA", "B.Sc / M.Sc", "Other"],
        key="education",
    )
    experience = st.selectbox(
        "Experience", ["Fresher", "Academic projects", "Internship(s)", "1-2 years of work"], key="experience"
    )
    init("interests", [])
    interests = st.multiselect("Interest areas", engine.domains, key="interests")

    st.subheader("Plan")
    init("hours", 10)
    hours = st.slider("Study time per week (hours)", 2, 40, key="hours")
    target_choice = st.selectbox("Target career", [AUTO] + engine.career_names, key="target_choice")

    st.subheader("Quick demo")
    st.selectbox("Sample student", [NO_SAMPLE] + [p["name"] for p in PERSONAS], key="sample_choice")
    st.button("Load sample profile", on_click=load_sample)
    st.button("Clear my skills", on_click=clear_skills)

# ----------------------------------------------------------------------------- header
st.title("SkillPath AI")
st.markdown(
    "**Skill-gap analysis and personalised career path recommendation.**  "
    "Skills &rarr; Career match &rarr; Skill gap &rarr; Priority skills &rarr; Personalised roadmap"
)
q1, q2, q3, q4 = st.columns(4)
q1.markdown("**1. What skills do I have?**  \nTab: My Skills")
q2.markdown("**2. What career suits me?**  \nTab: Career Matches")
q3.markdown("**3. What am I missing?**  \nTab: Skill Gap")
q4.markdown("**4. What should I learn next?**  \nTab: Learning Roadmap")

tabs = st.tabs(["1. My Skills", "2. Career Matches", "3. Skill Gap", "4. Learning Roadmap", "5. Data Insights"])

# ----------------------------------------------------------------------------- tab 1: skills
profile: dict = {}
with tabs[0]:
    st.subheader("What skills do I currently have?")
    st.caption(
        "Pick the skills you know in each category, then rate each one "
        "(1 = awareness ... 5 = expert). Skills you do not pick count as 0. "
        "Tip: load a sample profile from the sidebar to see the dashboard instantly."
    )
    for cat in CATEGORIES:
        cat_skills = engine.skills.loc[engine.skills["category"] == cat, "skill"].tolist()
        init(f"sel_{cat}", [])
        with st.expander(cat, expanded=True):
            chosen = st.multiselect(f"Skills you know - {cat}", cat_skills, key=f"sel_{cat}")
            cols = st.columns(3)
            for i, skill in enumerate(chosen):
                init(f"lvl_{skill}", 3)
                with cols[i % 3]:
                    profile[skill] = st.select_slider(
                        skill,
                        options=[1, 2, 3, 4, 5],
                        key=f"lvl_{skill}",
                        format_func=lambda v: f"{v} - {LEVEL_LABELS[v]}",
                    )

    st.divider()
    if profile:
        label = student_name.strip() or "Student"
        st.markdown(f"**Profile:** {label} &middot; {education} &middot; {experience}")
        s = pd.Series(profile)
        cat_of = engine.skill_info.loc[list(profile), "category"].to_numpy()
        cat_avg = s.groupby(cat_of).mean().sort_values()
        m1, m2, m3 = st.columns(3)
        m1.metric("Skills entered", len(profile))
        m2.metric("Average level", f"{s.mean():.1f} / 5")
        m3.metric("Strongest area", cat_avg.index[-1])
        fig = px.bar(
            cat_avg.reset_index(name="avg_level").rename(columns={"index": "category"}),
            x="avg_level", y="category", orientation="h", range_x=[0, 5],
            labels={"avg_level": "Average level (0-5)", "category": ""},
            title="Your profile by skill category",
        )
        fig.update_traces(marker_color=CURRENT_COLOR)
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig)
    else:
        st.info("No skills yet. Select skills above, or load a sample profile from the sidebar.")

# ----------------------------------------------------------------------------- shared computations
has_profile = bool(profile)
ranked = engine.match_careers(profile, interests) if has_profile else None
if target_choice != AUTO:
    target = target_choice
elif has_profile:
    target = ranked["career"].iloc[0]
else:
    target = None

gap = rm = None
ready = 0.0
if target:
    gap = engine.skill_gap(profile, target)
    rm = engine.roadmap(profile, target, hours)
    ready = engine.readiness(profile, target)

# ----------------------------------------------------------------------------- tab 2: career matches
with tabs[1]:
    st.subheader("What career suits me?")
    if not has_profile:
        st.info("Add some skills in the first tab to see career recommendations.")
    else:
        top3 = ranked.head(3)
        cols = st.columns(3)
        for col, (rank, row) in zip(cols, enumerate(top3.itertuples(), start=1)):
            with col:
                with st.container(border=True):
                    st.metric(f"Rank {rank}: {row.career}", f"{row.match_score:.0f}% match")
                    st.caption(engine.career_info.loc[row.career, "description"])
                    st.write(row.why)

        fig = px.bar(
            ranked.sort_values("match_score"), x="match_score", y="career", orientation="h",
            text="match_score", range_x=[0, 110],
            labels={"match_score": "Match score (%)", "career": ""}, title="All careers ranked for you",
        )
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", cliponaxis=False,
                          marker_color=CURRENT_COLOR)
        fig.update_layout(height=430, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig)

        with st.expander("How is the match score calculated?"):
            st.markdown(
                f"""
**Match score = {W_READINESS:.0%} x Readiness + {W_COSINE:.0%} x Skill-shape fit + {W_INTEREST:.0%} x Interest match**

- **Readiness**: for every skill the career requires, how much of the required level you already have
  (`min(your level, required) / required`), weighted by how important that skill is for the career.
- **Skill-shape fit**: cosine similarity between your skill vector and the career's requirement vector.
- **Interest match**: 1 if the career belongs to one of the interest areas you chose, otherwise 0.
  If you choose no interests, the other two parts are rescaled to 100%.
                """
            )
            st.dataframe(
                ranked[["career", "match_score", "readiness", "cosine_fit", "interest_match",
                        "skills_met", "skills_required"]],
                hide_index=True,
            )

# ----------------------------------------------------------------------------- tab 3: skill gap
with tabs[2]:
    st.subheader("What skills am I missing?")
    if gap is None:
        st.info("Add skills (or pick a target career in the sidebar) to analyse your gap.")
    else:
        st.markdown(f"Target career: **{target}**" + ("  (best match)" if target_choice == AUTO else ""))
        met = int((gap["gap"] == 0).sum())
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Career readiness", f"{ready:.0f}%")
        g2.metric("Skills met", f"{met} / {len(gap)}")
        g3.metric("Skills to learn", int((gap["gap"] > 0).sum()))
        g4.metric("Study hours needed", f"{rm['hours'].sum():.0f} h" if len(rm) else "0 h")

        left, right = st.columns(2)
        with left:
            gr = gap.sort_values(["category", "skill"])
            theta = gr["skill"].tolist() + [gr["skill"].iloc[0]]
            radar = go.Figure()
            radar.add_trace(go.Scatterpolar(
                r=gr["required"].tolist() + [gr["required"].iloc[0]], theta=theta, fill="toself",
                name=f"Required for {target}", line_color=REQUIRED_COLOR, opacity=0.5))
            radar.add_trace(go.Scatterpolar(
                r=gr["current"].tolist() + [gr["current"].iloc[0]], theta=theta, fill="toself",
                name="You", line_color=CURRENT_COLOR, opacity=0.6))
            radar.update_layout(
                title="Your skills vs the career requirement",
                polar=dict(radialaxis=dict(range=[0, 5], tickvals=[1, 2, 3, 4, 5])),
                legend=dict(orientation="h", y=-0.1), height=520, margin=dict(l=40, r=40, t=60, b=40))
            st.plotly_chart(radar)
        with right:
            todo = gap[gap["gap"] > 0].head(10)
            if len(todo):
                fig = px.bar(
                    todo, x="priority", y="skill", orientation="h", color="status",
                    color_discrete_map={"Missing": REQUIRED_COLOR, "Partial": "#e9c46a"},
                    category_orders={"skill": todo["skill"].tolist()},
                    labels={"priority": "Priority = importance x gap", "skill": ""},
                    title="Top skills to prioritise",
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10), legend_title_text="")
                st.plotly_chart(fig)
            else:
                st.success("You already meet every requirement for this career.")

        st.markdown("**Full gap table** (sorted by priority)")
        st.dataframe(
            gap.rename(columns={"skill": "Skill", "category": "Category", "current": "Your level",
                                "required": "Required", "gap": "Gap", "importance": "Importance",
                                "priority": "Priority", "status": "Status"}),
            hide_index=True,
        )

# ----------------------------------------------------------------------------- tab 4: roadmap
with tabs[3]:
    st.subheader("What should I learn next?")
    if rm is None:
        st.info("Add skills (or pick a target career in the sidebar) to generate a roadmap.")
    elif len(rm) == 0:
        st.success(f"You already meet all requirements for {target}. Time to build projects and apply!")
    else:
        total_h, total_w = rm["hours"].sum(), rm["week_end"].max()
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Skills on roadmap", len(rm))
        r2.metric("Total study time", f"{total_h:.0f} h")
        r3.metric("At your pace", f"{total_w:.0f} weeks")
        r4.metric("Approx. months", f"{total_w / 4.3:.1f}")
        st.caption(
            f"Roadmap for **{target}** at {hours} h/week. Prerequisites are placed before the skills that "
            "need them; otherwise the highest-priority skills come first. Hours are rough estimates."
        )

        tl = rm.assign(duration=(rm["week_end"] - rm["week_start"]).clip(lower=0.2))
        fig = px.bar(
            tl, x="duration", y="skill", base="week_start", orientation="h", color="phase",
            category_orders={"skill": tl["skill"].tolist()},
            hover_data={"hours": True, "reason": True, "duration": False},
            labels={"duration": "Weeks from today", "skill": ""}, title="Learning timeline",
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(380, 28 * len(tl) + 120), margin=dict(l=10, r=10, t=60, b=10),
                          legend_title_text="")
        st.plotly_chart(fig)

        st.markdown("#### Career readiness after each step")
        n_done = st.slider("If I complete the first N skills of the roadmap...", 0, len(rm), min(3, len(rm)))
        curve = [engine.projected_readiness(profile, target, rm, k) for k in range(len(rm) + 1)]
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Readiness now", f"{curve[0]:.0f}%")
            st.metric(f"Readiness after {n_done} skill(s)", f"{curve[n_done]:.0f}%",
                      delta=f"{curve[n_done] - curve[0]:+.0f} pts")
        with c2:
            fig = px.line(x=list(range(len(curve))), y=curve, markers=True,
                          labels={"x": "Roadmap skills completed", "y": "Career readiness (%)"})
            fig.add_scatter(x=[n_done], y=[curve[n_done]], mode="markers", name="Selected",
                            marker=dict(size=16, color=REQUIRED_COLOR))
            fig.update_yaxes(range=[0, 105])
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
            st.plotly_chart(fig)

        st.markdown("#### Your step-by-step path")
        show_cols = {"order": "#", "skill": "Skill", "current": "From", "target": "To", "hours": "Hours",
                     "week_start": "Start (week)", "week_end": "End (week)", "reason": "Why",
                     "resource": "Suggested resource"}
        for phase in rm["phase"].unique():
            st.markdown(f"**{phase}**")
            st.dataframe(rm.loc[rm["phase"] == phase, list(show_cols)].rename(columns=show_cols),
                         hide_index=True)

        st.download_button(
            "Download roadmap (CSV)", rm.to_csv(index=False).encode("utf-8"),
            file_name=f"skillpath_roadmap_{target.replace(' ', '_')}.csv", mime="text/csv",
        )

# ----------------------------------------------------------------------------- tab 5: data insights
with tabs[4]:
    st.subheader("Data insights behind the recommendations")
    st.caption(
        "Career requirements in this prototype are team-curated estimates in the style of O*NET / ESCO "
        "occupation-skill data (see README), covering "
        f"{len(engine.career_names)} careers and {len(engine.skill_names)} skills."
    )

    st.markdown("#### Career x skill requirement matrix")
    fig = px.imshow(engine.req, aspect="auto", color_continuous_scale="Blues",
                    labels=dict(x="Skill", y="Career", color="Required level"))
    fig.update_xaxes(tickangle=-60)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig)

    a, b = st.columns(2)
    with a:
        st.markdown("#### Most in-demand skills across careers")
        demand = engine.skill_demand().head(15)
        fig = px.bar(demand, x="careers_needing", y="skill", orientation="h", color="avg_importance",
                     color_continuous_scale="Blues", category_orders={"skill": demand["skill"].tolist()},
                     labels={"careers_needing": "Number of careers that need it", "skill": "",
                             "avg_importance": "Avg importance"})
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=470, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig)
    with b:
        st.markdown("#### Which careers overlap? (cosine similarity)")
        fig = px.imshow(engine.career_similarity(), text_auto=".2f", color_continuous_scale="Blues",
                        zmin=0, zmax=1, aspect="auto")
        fig.update_xaxes(tickangle=-45)
        fig.update_layout(height=470, margin=dict(l=10, r=10, t=20, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig)

    st.markdown("#### Career map (PCA of the requirement matrix)")
    cmap = engine.career_map(profile if has_profile else None)
    cmap["size"] = cmap["kind"].map({"Career": 12, "You": 20})
    fig = px.scatter(cmap, x="x", y="y", text="name", color="kind", size="size", size_max=20,
                     color_discrete_map={"Career": REQUIRED_COLOR, "You": CURRENT_COLOR},
                     labels={"x": "Principal component 1", "y": "Principal component 2"})
    fig.update_traces(textposition="top center")
    fig.update_layout(height=480, margin=dict(l=10, r=10, t=20, b=10), legend_title_text="")
    st.plotly_chart(fig)
    st.caption("Careers close together need similar skills. Your marker shows where your current skills "
               "sit relative to them.")
