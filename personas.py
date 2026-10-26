"""Hand-written student personas.

Used in two places:
  * app.py        - "Load a sample profile" so the dashboard can be demoed in seconds
  * evaluation.py - sanity-check the recommender

The `expected` career is the TEAM'S OWN JUDGEMENT of the best-fit career for that
persona (it is not derived from the career data). To make the evaluation stronger,
add 10+ real profiles from your classmates (a Google Form is enough) and decide
the expected career together with each student.
"""

PERSONAS = [
    dict(name="Java-focused CSE student", expected="Java Full Stack Developer", interests=["Web"],
         skills={"Java": 4, "SQL": 3, "OOP": 4, "DBMS": 3, "HTML/CSS": 3, "JavaScript": 2, "Git": 3,
                 "Data Structures & Algorithms": 3, "REST APIs": 2, "Problem Solving": 3}),
    dict(name="Front-end / React learner", expected="Java Full Stack Developer", interests=["Web"],
         skills={"JavaScript": 4, "React": 4, "HTML/CSS": 4, "REST APIs": 3, "Git": 3, "Java": 2, "Teamwork": 3}),
    dict(name="Stats-minded Python student", expected="Data Scientist", interests=["Data"],
         skills={"Python": 4, "Statistics": 4, "Machine Learning": 3, "Data Cleaning": 3,
                 "Data Visualization": 3, "SQL": 3, "Problem Solving": 3}),
    dict(name="Kaggle regular", expected="Data Scientist", interests=["Data"],
         skills={"Python": 4, "Statistics": 3, "Machine Learning": 3, "SQL": 2, "Data Visualization": 3,
                 "Data Cleaning": 3, "Git": 2}),
    dict(name="Excel and dashboards intern", expected="Data Analyst", interests=["Data", "Business"],
         skills={"Excel": 4, "SQL": 3, "Power BI / Tableau": 3, "Data Visualization": 3, "Communication": 4,
                 "Statistics": 2, "Python": 2}),
    dict(name="Deep-learning enthusiast", expected="ML Engineer", interests=["Data"],
         skills={"Python": 5, "Machine Learning": 4, "Deep Learning": 4, "Statistics": 3, "Git": 3,
                 "Docker": 2, "MLOps": 1, "Data Structures & Algorithms": 3}),
    dict(name="Pipeline builder", expected="Data Engineer", interests=["Data", "Cloud"],
         skills={"SQL": 4, "Python": 4, "ETL & Data Pipelines": 3, "Big Data (Spark)": 2, "DBMS": 4, "Linux": 3}),
    dict(name="AWS-certified beginner", expected="Cloud Engineer", interests=["Cloud"],
         skills={"AWS": 3, "Linux": 3, "Computer Networks": 3, "Docker": 2, "Operating Systems": 3,
                 "Python": 2, "Git": 2}),
    dict(name="Linux and Docker hobbyist", expected="DevOps Engineer", interests=["Cloud"],
         skills={"Linux": 4, "Docker": 3, "Git": 4, "CI/CD": 2, "Python": 2, "Monitoring & Logging": 2,
                 "Teamwork": 3}),
    dict(name="CTF player", expected="Cybersecurity Analyst", interests=["Security"],
         skills={"Cybersecurity Fundamentals": 3, "Computer Networks": 4, "Linux": 4, "Network Security": 3,
                 "Cryptography": 3, "Python": 2}),
    dict(name="Design student", expected="UI/UX Designer", interests=["Design"],
         skills={"UI/UX Design": 4, "Figma": 4, "User Research": 3, "HTML/CSS": 3, "Communication": 4,
                 "Teamwork": 4}),
    dict(name="Management-minded student", expected="Business Analyst", interests=["Business"],
         skills={"Requirements Analysis": 3, "Communication": 5, "Project Management": 4, "Excel": 3,
                 "SQL": 2, "Teamwork": 4, "Problem Solving": 3}),
]
