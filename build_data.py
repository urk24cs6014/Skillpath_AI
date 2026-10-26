"""Builds the CSV files used by SkillPath AI.

Run:  python build_data.py

Outputs (in ./data):
    skills.csv        skill, category, hours_per_level, resource, prerequisites
    careers.csv       career, domains, description
    career_skills.csv career, skill, required_level (1-5), importance (1-5)

IMPORTANT (be honest in your report): the required levels and importance
weights below are hand-curated estimates written by the project team, inspired
by the structure of O*NET / ESCO occupation-skill data. They are NOT copied
from O*NET. To strengthen the project, cross-check a few careers against
https://www.onetonline.org and edit the numbers here, then re-run this file.

Scales:
    required_level : 1 = awareness, 2 = basic, 3 = working, 4 = advanced, 5 = expert
    importance     : 1 = nice to have ... 5 = critical for the role
"""
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"

# (skill, category, hours_per_level, learning resource, prerequisites)
# hours_per_level = rough study hours to raise the skill by ONE level (estimate).
SKILLS = [
    # Programming
    ("Python", "Programming", 20, "Python official tutorial + Kaggle Learn (Python)", []),
    ("Java", "Programming", 25, "MOOC.fi Java Programming / Oracle Java Tutorials", []),
    ("SQL", "Programming", 12, "SQLBolt + Mode SQL Tutorial", []),
    ("JavaScript", "Programming", 20, "javascript.info", []),
    # CS fundamentals
    ("Data Structures & Algorithms", "CS Fundamentals", 30, "NeetCode roadmap / GeeksforGeeks DSA", []),
    ("OOP", "CS Fundamentals", 12, "OOP chapters of your Java/Python course", []),
    ("DBMS", "CS Fundamentals", 15, "NPTEL / Stanford DB course", ["SQL"]),
    ("Operating Systems", "CS Fundamentals", 12, "OSTEP (free online book)", []),
    ("Computer Networks", "CS Fundamentals", 12, "NPTEL Computer Networks / Top-Down Approach book", []),
    ("System Design", "CS Fundamentals", 15, "System Design Primer (GitHub)", ["DBMS"]),
    # Data & AI
    ("Statistics", "Data & AI", 15, "Khan Academy Statistics & Probability", []),
    ("Excel", "Data & AI", 8, "Microsoft Excel training / ExcelIsFun", []),
    ("Data Cleaning", "Data & AI", 10, "Kaggle Learn (Data Cleaning)", ["Python"]),
    ("Data Visualization", "Data & AI", 10, "Kaggle Learn (Data Visualization)", ["Python"]),
    ("Power BI / Tableau", "Data & AI", 10, "Microsoft Learn Power BI / Tableau Public training", ["Excel"]),
    ("Machine Learning", "Data & AI", 25, "Andrew Ng ML Specialization / scikit-learn docs", ["Python", "Statistics"]),
    ("Deep Learning", "Data & AI", 25, "fast.ai / DeepLearning.AI", ["Machine Learning"]),
    ("Big Data (Spark)", "Data & AI", 15, "Apache Spark docs + Databricks Academy", ["Python", "SQL"]),
    ("ETL & Data Pipelines", "Data & AI", 12, "Data Engineering Zoomcamp (DataTalks.Club)", ["SQL", "Python"]),
    ("MLOps", "Data & AI", 15, "MLOps Zoomcamp (DataTalks.Club) / Made With ML", ["Machine Learning", "Docker"]),
    # Web
    ("HTML/CSS", "Web", 8, "freeCodeCamp Responsive Web Design", []),
    ("REST APIs", "Web", 8, "Postman Learning Center", []),
    ("React", "Web", 15, "react.dev Learn", ["JavaScript", "HTML/CSS"]),
    ("Spring Boot", "Web", 20, "spring.io guides / Baeldung", ["Java", "REST APIs"]),
    # Cloud & DevOps
    ("Linux", "Cloud & DevOps", 10, "Linux Journey / OverTheWire Bandit", []),
    ("Git", "Cloud & DevOps", 6, "Pro Git book / GitHub Skills", []),
    ("Docker", "Cloud & DevOps", 10, "Docker official Get Started guide", ["Linux"]),
    ("Kubernetes", "Cloud & DevOps", 18, "Kubernetes official tutorials", ["Docker"]),
    ("AWS", "Cloud & DevOps", 20, "AWS Skill Builder (Cloud Practitioner -> Solutions Architect)", ["Linux"]),
    ("CI/CD", "Cloud & DevOps", 10, "GitHub Actions documentation", ["Git"]),
    ("Infrastructure as Code (Terraform)", "Cloud & DevOps", 12, "HashiCorp Terraform tutorials", ["AWS"]),
    ("Monitoring & Logging", "Cloud & DevOps", 8, "Prometheus + Grafana docs", ["Linux"]),
    # Security
    ("Cybersecurity Fundamentals", "Security", 15, "Cisco Intro to Cybersecurity / TryHackMe Pre-Security", ["Computer Networks"]),
    ("Cryptography", "Security", 12, "Cryptography I (Stanford, Coursera)", []),
    ("Network Security", "Security", 15, "TryHackMe network security rooms", ["Computer Networks", "Cybersecurity Fundamentals"]),
    ("Vulnerability Assessment", "Security", 15, "OWASP Top 10 + TryHackMe", ["Cybersecurity Fundamentals", "Linux"]),
    # Design
    ("UI/UX Design", "Design", 20, "Google UX Design Certificate / Interaction Design Foundation", []),
    ("Figma", "Design", 8, "Figma official tutorials", []),
    ("User Research", "Design", 10, "Nielsen Norman Group articles", []),
    # Business & soft skills
    ("Requirements Analysis", "Business & Soft Skills", 10, "BABOK overview (IIBA) / requirement-writing practice", []),
    ("Communication", "Business & Soft Skills", 10, "Practice: presentations, report writing, mock interviews", []),
    ("Problem Solving", "Business & Soft Skills", 15, "LeetCode / Project Euler practice", []),
    ("Teamwork", "Business & Soft Skills", 6, "Group projects / open-source contributions", []),
    ("Project Management", "Business & Soft Skills", 10, "Scrum Guide (scrum.org) / Google Project Management", []),
]

# career -> domains, description, {skill: (required_level, importance)}
CAREERS = {
    "Data Analyst": dict(
        domains="Data|Business",
        description="Turns raw data into reports, dashboards and insights for decision makers.",
        reqs={
            "SQL": (4, 5), "Excel": (4, 4), "Power BI / Tableau": (4, 5), "Data Visualization": (4, 4),
            "Statistics": (3, 4), "Python": (3, 4), "Data Cleaning": (4, 4), "Communication": (4, 4),
            "Problem Solving": (3, 3), "Requirements Analysis": (2, 2), "DBMS": (3, 3), "Teamwork": (3, 2),
        },
    ),
    "Data Scientist": dict(
        domains="Data",
        description="Builds statistical and machine-learning models to answer business questions.",
        reqs={
            "Python": (5, 5), "Statistics": (5, 5), "Machine Learning": (4, 5), "SQL": (4, 4),
            "Data Cleaning": (4, 4), "Data Visualization": (4, 3), "Deep Learning": (3, 3),
            "Big Data (Spark)": (2, 2), "Problem Solving": (4, 3), "Communication": (4, 3),
            "Data Structures & Algorithms": (3, 2), "Git": (3, 2),
        },
    ),
    "ML Engineer": dict(
        domains="Data|Cloud",
        description="Puts machine-learning models into production as reliable, scalable services.",
        reqs={
            "Python": (5, 5), "Machine Learning": (5, 5), "Deep Learning": (4, 4), "MLOps": (4, 4),
            "Docker": (3, 3), "Data Structures & Algorithms": (4, 3), "Statistics": (4, 3), "SQL": (3, 2),
            "Git": (4, 3), "AWS": (3, 3), "Linux": (3, 2), "Problem Solving": (4, 3), "CI/CD": (3, 2),
        },
    ),
    "Data Engineer": dict(
        domains="Data|Cloud",
        description="Designs the pipelines and storage that deliver clean data to analysts and models.",
        reqs={
            "SQL": (5, 5), "Python": (4, 5), "ETL & Data Pipelines": (5, 5), "Big Data (Spark)": (4, 4),
            "DBMS": (4, 4), "AWS": (3, 3), "Linux": (3, 3), "Git": (3, 2), "Docker": (3, 2),
            "Data Structures & Algorithms": (3, 2), "Problem Solving": (3, 3), "CI/CD": (2, 2),
        },
    ),
    "Java Full Stack Developer": dict(
        domains="Web",
        description="Builds complete web applications: Java/Spring back end, database and web front end.",
        reqs={
            "Java": (5, 5), "Spring Boot": (4, 5), "SQL": (4, 4), "REST APIs": (4, 4), "JavaScript": (4, 4),
            "HTML/CSS": (4, 3), "React": (3, 4), "OOP": (5, 4), "DBMS": (3, 3), "Git": (4, 3),
            "Data Structures & Algorithms": (3, 3), "Docker": (2, 2), "System Design": (2, 2),
            "Problem Solving": (4, 3), "Teamwork": (3, 2),
        },
    ),
    "Cloud Engineer": dict(
        domains="Cloud",
        description="Designs, deploys and operates infrastructure and applications on cloud platforms.",
        reqs={
            "AWS": (4, 5), "Linux": (4, 5), "Computer Networks": (4, 4), "Docker": (3, 3),
            "Infrastructure as Code (Terraform)": (3, 4), "CI/CD": (3, 3), "Python": (3, 3),
            "Kubernetes": (2, 2), "Monitoring & Logging": (3, 3), "Cybersecurity Fundamentals": (2, 2),
            "Git": (3, 2), "Operating Systems": (3, 3), "Problem Solving": (3, 3),
        },
    ),
    "DevOps Engineer": dict(
        domains="Cloud",
        description="Automates build, test, deployment and monitoring so software ships quickly and safely.",
        reqs={
            "Linux": (4, 5), "Docker": (4, 5), "CI/CD": (4, 5), "Kubernetes": (3, 4), "Git": (4, 4),
            "Infrastructure as Code (Terraform)": (3, 4), "AWS": (3, 4), "Monitoring & Logging": (4, 4),
            "Python": (3, 3), "Computer Networks": (3, 2), "Teamwork": (4, 3), "Problem Solving": (3, 3),
        },
    ),
    "Cybersecurity Analyst": dict(
        domains="Security",
        description="Monitors systems, finds vulnerabilities and responds to security incidents.",
        reqs={
            "Cybersecurity Fundamentals": (4, 5), "Computer Networks": (4, 5), "Network Security": (4, 4),
            "Linux": (4, 4), "Vulnerability Assessment": (3, 4), "Cryptography": (3, 3),
            "Operating Systems": (3, 3), "Python": (2, 2), "Problem Solving": (4, 3),
            "Communication": (3, 3), "Monitoring & Logging": (3, 2),
        },
    ),
    "UI/UX Designer": dict(
        domains="Design|Web",
        description="Researches users and designs intuitive, good-looking interfaces and prototypes.",
        reqs={
            "UI/UX Design": (5, 5), "Figma": (4, 5), "User Research": (4, 4), "HTML/CSS": (3, 3),
            "Communication": (4, 4), "Teamwork": (4, 3), "Problem Solving": (3, 2), "JavaScript": (2, 2),
            "Requirements Analysis": (3, 2), "Project Management": (2, 1),
        },
    ),
    "Business Analyst": dict(
        domains="Business|Data",
        description="Bridges business and technology teams by gathering requirements and analysing processes.",
        reqs={
            "Requirements Analysis": (5, 5), "Communication": (5, 5), "SQL": (3, 4), "Excel": (4, 4),
            "Power BI / Tableau": (3, 3), "Project Management": (4, 4), "Problem Solving": (4, 3),
            "Teamwork": (4, 3), "Data Visualization": (3, 3), "Statistics": (2, 2), "DBMS": (2, 2),
        },
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    skills = pd.DataFrame(
        [
            dict(skill=s, category=c, hours_per_level=h, resource=r, prerequisites="|".join(p))
            for s, c, h, r, p in SKILLS
        ]
    )
    careers = pd.DataFrame(
        [dict(career=c, domains=v["domains"], description=v["description"]) for c, v in CAREERS.items()]
    )
    rows = []
    for career, v in CAREERS.items():
        for skill, (level, importance) in v["reqs"].items():
            rows.append(dict(career=career, skill=skill, required_level=level, importance=importance))
    career_skills = pd.DataFrame(rows)

    # ---- validation: catch typos before they become silent bugs ----
    names = set(skills["skill"])
    assert len(names) == len(skills), "duplicate skill names"
    unknown = set(career_skills["skill"]) - names
    assert not unknown, f"career_skills refers to unknown skills: {unknown}"
    for s, _, _, _, prereqs in SKILLS:
        for p in prereqs:
            assert p in names, f"prerequisite '{p}' of '{s}' is not a skill"
    assert career_skills["required_level"].between(1, 5).all()
    assert career_skills["importance"].between(1, 5).all()
    assert not career_skills.duplicated(["career", "skill"]).any()

    skills.to_csv(OUT / "skills.csv", index=False)
    careers.to_csv(OUT / "careers.csv", index=False)
    career_skills.to_csv(OUT / "career_skills.csv", index=False)
    print(f"Wrote {len(skills)} skills, {len(careers)} careers, {len(career_skills)} career-skill rows to {OUT}")


if __name__ == "__main__":
    main()
