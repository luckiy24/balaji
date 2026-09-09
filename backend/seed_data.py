"""
Database Seeding Script for StatSkill AI
----------------------------------------
Seeds:
- 5 Roles with competency requirements & criticality weights
- 16 Official Statistics Competencies with Level 1-5 definitions
- 5 User personas (Statistical Officer Ramesh Kumar with prompt-specified baseline scores:
  Sampling 42%, Data Visualization 35%, Statistical Analysis 61%, Data Quality 82%)
- 20+ iGOT Karmayogi Courses
- 50+ Diagnostic MCQs with explanations & source citations
- 2 Sample documents ingested, chunked, and grounded MCQs generated
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from backend.database import engine, SessionLocal, Base
from backend.models import (
    User, Role, Competency, RoleCompetency, Assessment, Question,
    Course, CompetencyScore, Document, DocumentChunk, GeneratedQuestion, LearningProgress
)
from backend.services.document_service import document_service
from backend.services.gap_engine import classify_score, score_to_level
from backend.config import settings

def seed_database():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains records. Verifying demo persona...")
            # Verify Ramesh Kumar baseline scores
            ramesh = db.query(User).filter(User.employee_id == "MOSPI-SO-7429").first()
            if ramesh:
                print("Demo Statistical Officer Ramesh Kumar confirmed.")
                return

        print("Seeding Competency Framework (16 Competencies)...")
        competencies_data = [
            {
                "name": "Sampling Methods",
                "code": "COMP-SMP",
                "domain": "Survey & Sampling",
                "description": "Probability sampling techniques, frame design, strata allocation, variance estimation, and finite population corrections.",
                "level_1": "Understands difference between sample and census; basic random numbers.",
                "level_2": "Can implement Simple Random Sampling (SRS) with/without replacement.",
                "level_3": "Proficient in Stratified sampling and Neyman sample size allocation.",
                "level_4": "Masters multi-stage cluster sampling, NSSO UFS frames, and Design Effect (Deff).",
                "level_5": "Designs national sampling frameworks and innovates complex survey weighting."
            },
            {
                "name": "Data Visualization",
                "code": "COMP-VIZ",
                "domain": "Analytics & Dissemination",
                "description": "Graphical representation of official indicators, thematic cartography, dashboards, and MoSPI portal standards.",
                "level_1": "Generates basic bar charts and histograms in standard spreadsheets.",
                "level_2": "Selects appropriate visual charts avoiding cognitive chart junk.",
                "level_3": "Creates interactive dashboards with filters, drill-downs, and rate overlays.",
                "level_4": "Builds reproducible visualization pipelines in R (ggplot2) / Python (Plotly/Seaborn).",
                "level_5": "Directs executive infographics policy for national economic releases."
            },
            {
                "name": "Statistical Analysis",
                "code": "COMP-STAT",
                "domain": "Analytical Core",
                "description": "Exploratory data analysis, statistical inference, hypothesis testing, ANOVA, and multivariate regression.",
                "level_1": "Computes mean, median, standard deviation, and basic percentiles.",
                "level_2": "Formulates null/alternative hypotheses; conducts t-tests and Chi-square tests.",
                "level_3": "Interprets multiple linear regression models and checks collinearity.",
                "level_4": "Executes GLMs, non-parametric tests, and robustness diagnostics on microdata.",
                "level_5": "Architects econometric and macroeconomic estimation methodologies."
            },
            {
                "name": "Data Quality",
                "code": "COMP-QUAL",
                "domain": "Data Governance",
                "description": "Data editing, automated range validation, outlier detection, and statistical imputation methods.",
                "level_1": "Identifies duplicate entries and missing observation cells.",
                "level_2": "Applies univariate range and logical boundary checks.",
                "level_3": "Implements automated cross-validation and deductive imputation.",
                "level_4": "Deploys donor hot-deck imputation and Fellegi-Holt editing models.",
                "level_5": "Authors national data audit standards and quality assurance protocols."
            },
            {
                "name": "Official Statistics",
                "code": "COMP-OFFSTAT",
                "domain": "Governance & Institutional",
                "description": "Institutional architecture of MoSPI, National Statistical Commission, Census, and economic indicators.",
                "level_1": "Familiar with MoSPI divisions (NSSO, CSO, FOD, SDRD, DQAD).",
                "level_2": "Understands Collection of Statistics Act and key published indicators.",
                "level_3": "Knows methodology for CPI, IIP, and National Accounts Compilation.",
                "level_4": "Coordinates line-ministry statistical systems and administrative data harmonization.",
                "level_5": "Represents India at UN Statistical Commission and guides legal statistical reforms."
            },
            {
                "name": "Survey Methodology",
                "code": "COMP-SURVMETH",
                "domain": "Survey & Sampling",
                "description": "End-to-end survey lifecycle, target population definition, mode of interview, and non-response mitigation.",
                "level_1": "Recognizes survey phases: planning, listing, interviewing, processing.",
                "level_2": "Follows standard field investigator manuals and schedules.",
                "level_3": "Optimizes field logistics, team deployment, and callback schedules.",
                "level_4": "Designs mixed-mode (CAPI, CATI, CAWI) survey systems and frame maintenance.",
                "level_5": "Pioneers continuous nationwide digital survey architectures."
            },
            {
                "name": "Questionnaire Design",
                "code": "COMP-QUEST",
                "domain": "Survey & Sampling",
                "description": "Formulation of measurement instruments, cognitive testing, skip-patterns, and bias reduction.",
                "level_1": "Drafts basic structured questions with predefined response codes.",
                "level_2": "Avoids leading questions and implements clean branching logic.",
                "level_3": "Applies cognitive pre-testing and validates recall periods.",
                "level_4": "Develops standardized CAPI validation scripts and multi-lingual modules.",
                "level_5": "Standardizes harmonized classification rosters (NCO, NIC) in questionnaires."
            },
            {
                "name": "Data Collection",
                "code": "COMP-DATACOLL",
                "domain": "Field Operations",
                "description": "CAPI tablet handling, respondent rapport building, field enumeration, and geo-tagging.",
                "level_1": "Navigates mobile data collection interfaces and submits records.",
                "level_2": "Handles respondent reluctance and secures informed consent.",
                "level_3": "Conducts spot checks and supervises primary enumeration teams.",
                "level_4": "Manages regional field telemetry, GPS audit trails, and survey progress tracking.",
                "level_5": "Directs nationwide census and multi-round survey field forces."
            },
            {
                "name": "Descriptive Statistics",
                "code": "COMP-DESC",
                "domain": "Analytical Core",
                "description": "Summary measures, frequency distributions, skewness, kurtosis, and index numbers.",
                "level_1": "Computes arithmetic mean, median, mode, and range.",
                "level_2": "Constructs grouped frequency tables and calculates quartiles and variance.",
                "level_3": "Computes Laspeyres, Paasche, and Fisher index numbers.",
                "level_4": "Analyzes multivariate distributions and robust location estimators.",
                "level_5": "Sets national methodological conventions for statistical summary measures."
            },
            {
                "name": "Inferential Statistics",
                "code": "COMP-INFER",
                "domain": "Analytical Core",
                "description": "Point and interval estimation, central limit theorem, and testing of statistical hypotheses.",
                "level_1": "States concepts of population parameter and sample estimator.",
                "level_2": "Calculates 95% confidence intervals for population means and proportions.",
                "level_3": "Executes one-sample and two-sample t-tests, z-tests, and F-tests.",
                "level_4": "Performs likelihood ratio tests, Bayesian parameter estimation, and power analysis.",
                "level_5": "Develops specialized estimators for sparse small area domains."
            },
            {
                "name": "Time Series Analysis",
                "code": "COMP-TIMESERIES",
                "domain": "Advanced Analytics",
                "description": "Trend decomposition, seasonal adjustments (X-13ARIMA-SEATS), ARIMA modeling, and forecasting.",
                "level_1": "Plots temporal data and recognizes linear trends.",
                "level_2": "Calculates moving averages and identifies seasonal patterns.",
                "level_3": "Applies additive and multiplicative seasonal decomposition.",
                "level_4": "Estimates ARIMA, SARIMA, and VAR models with stationarity testing (ADF/KPSS).",
                "level_5": "Constructs real-time nowcasting models for GDP and national aggregates."
            },
            {
                "name": "Data Management",
                "code": "COMP-DATAMGMT",
                "domain": "Data Engineering",
                "description": "Relational databases, SQL, data lakes, metadata standards (SDMX), and ETL pipelines.",
                "level_1": "Performs basic data sorting, filtering, and table joins in spreadsheets.",
                "level_2": "Writes SQL SELECT queries with WHERE, GROUP BY, and JOIN clauses.",
                "level_3": "Designs normalized relational schemas and data transformation scripts.",
                "level_4": "Implements SDMX statistical metadata repositories and big data pipelines.",
                "level_5": "Architects National Integrated Statistical Data Warehouse."
            },
            {
                "name": "Python",
                "code": "COMP-PY",
                "domain": "Computing & Automation",
                "description": "Data wrangling, automated processing, Pandas, NumPy, Scikit-learn for official statistics.",
                "level_1": "Writes basic Python scripts, loops, functions, and file readers.",
                "level_2": "Uses Pandas for data cleaning, filtering, aggregation, and merging.",
                "level_3": "Builds automated data validation scripts and batch statistical reports.",
                "level_4": "Develops machine learning models for anomaly detection and text classification.",
                "level_5": "Creates enterprise statistical packages and high-performance computation routines."
            },
            {
                "name": "R Programming",
                "code": "COMP-R",
                "domain": "Computing & Automation",
                "description": "Statistical programming, survey package, Tidyverse, R Markdown, and reproducible research.",
                "level_1": "Installs packages, loads datasets, and prints summary statistics.",
                "level_2": "Uses dplyr for data manipulation and ggplot2 for exploratory plotting.",
                "level_3": "Applies the 'survey' package in R for calculating design-based standard errors.",
                "level_4": "Authors reproducible automated analytical reports with R Markdown / Quarto.",
                "level_5": "Builds CRAN packages for Indian official statistical estimation algorithms."
            },
            {
                "name": "Statistical Ethics",
                "code": "COMP-ETHICS",
                "domain": "Governance & Institutional",
                "description": "UN Fundamental Principles of Official Statistics, integrity, non-manipulation, and transparency.",
                "level_1": "Understands that statistics must be reported honestly without personal bias.",
                "level_2": "Respects respondent confidentiality and voluntary informed consent.",
                "level_3": "Prevents selective reporting and misleading visualizations in public releases.",
                "level_4": "Enforces scientific peer review and transparent methodology documentation.",
                "level_5": "Defends statistical independence and leads national ethics oversight boards."
            },
            {
                "name": "Data Privacy and Governance",
                "code": "COMP-PRIVACY",
                "domain": "Data Governance",
                "description": "Digital Personal Data Protection Act 2023, Statistical Disclosure Control (SDC), anonymization.",
                "level_1": "Identifies direct personal identifiers (Name, Aadhaar, Phone number).",
                "level_2": "Removes personal identifiers before sharing working datasets.",
                "level_3": "Applies k-anonymity, top-coding, and microdata perturbation techniques.",
                "level_4": "Audits compliance with DPDP Act, safe access environments, and differential privacy.",
                "level_5": "Drafts national microdata release policies and data fiduciary protocols."
            }
        ]

        comp_records = {}
        for c_data in competencies_data:
            comp = Competency(
                name=c_data["name"],
                code=c_data["code"],
                domain=c_data["domain"],
                description=c_data["description"],
                level_1_desc=c_data["level_1"],
                level_2_desc=c_data["level_2"],
                level_3_desc=c_data["level_3"],
                level_4_desc=c_data["level_4"],
                level_5_desc=c_data["level_5"]
            )
            db.add(comp)
            db.flush()
            comp_records[comp.name] = comp

        print("Seeding Roles & Competency Mappings...")
        roles_data = [
            {
                "name": "Statistical Officer",
                "code": "STAT_OFFICER",
                "department": "National Sample Survey Office (NSSO)",
                "description": "Responsible for designing and supervising sample surveys, validating microdata, compiling official statistical indicators, and preparing analytical briefs.",
                "requirements": [
                    ("Sampling Methods", 4, "Critical"),
                    ("Data Visualization", 4, "High"),
                    ("Statistical Analysis", 4, "Critical"),
                    ("Data Quality", 4, "Critical"),
                    ("Survey Methodology", 4, "High"),
                    ("Official Statistics", 3, "High"),
                    ("Data Privacy and Governance", 4, "High"),
                    ("Time Series Analysis", 3, "Medium"),
                    ("Python", 3, "Medium"),
                    ("R Programming", 3, "Medium")
                ]
            },
            {
                "name": "Data Analyst",
                "code": "DATA_ANALYST",
                "department": "Economic Statistics Division (ESD)",
                "description": "Performs statistical computations, builds interactive dashboards, conducts regression models, and executes automated data cleaning pipelines.",
                "requirements": [
                    ("Python", 4, "Critical"),
                    ("R Programming", 4, "Critical"),
                    ("Data Visualization", 4, "Critical"),
                    ("Statistical Analysis", 4, "High"),
                    ("Data Management", 4, "High"),
                    ("Data Quality", 3, "High"),
                    ("Sampling Methods", 3, "Medium")
                ]
            },
            {
                "name": "Survey Officer",
                "code": "SURVEY_OFFICER",
                "department": "Survey Design and Research Division (SDRD)",
                "description": "Designs nationwide sampling schemes, constructs sampling frames, prepares inquiry schedules, and supervises multi-stage field sampling.",
                "requirements": [
                    ("Survey Methodology", 5, "Critical"),
                    ("Sampling Methods", 5, "Critical"),
                    ("Questionnaire Design", 4, "Critical"),
                    ("Official Statistics", 4, "High"),
                    ("Data Collection", 4, "High"),
                    ("Data Quality", 3, "Medium")
                ]
            },
            {
                "name": "Field Investigator",
                "code": "FIELD_INVESTIGATOR",
                "department": "Field Operations Division (FOD)",
                "description": "Conducts primary data collection at the ground level using CAPI tablets, interviews households, and verifies respondent eligibility.",
                "requirements": [
                    ("Data Collection", 4, "Critical"),
                    ("Questionnaire Design", 3, "High"),
                    ("Data Quality", 3, "High"),
                    ("Statistical Ethics", 3, "Critical"),
                    ("Official Statistics", 2, "Medium")
                ]
            },
            {
                "name": "Statistical Supervisor",
                "code": "STAT_SUPERVISOR",
                "department": "Data Quality and Assurance Division (DQAD)",
                "description": "Audits field survey operations, verifies scrutiny reports, detects non-sampling errors, and ensures data governance compliance.",
                "requirements": [
                    ("Data Quality", 5, "Critical"),
                    ("Statistical Ethics", 4, "Critical"),
                    ("Survey Methodology", 4, "High"),
                    ("Data Privacy and Governance", 4, "Critical"),
                    ("Data Collection", 4, "High")
                ]
            }
        ]

        role_records = {}
        for r_data in roles_data:
            role = Role(
                name=r_data["name"],
                code=r_data["code"],
                department=r_data["department"],
                description=r_data["description"]
            )
            db.add(role)
            db.flush()
            role_records[role.code] = role

            for comp_name, req_lvl, imp in r_data["requirements"]:
                comp = comp_records.get(comp_name)
                if comp:
                    rc = RoleCompetency(
                        role_id=role.id,
                        competency_id=comp.id,
                        required_level=req_lvl,
                        importance=imp
                    )
                    db.add(rc)

        print("Seeding Demo Users (including Ramesh Kumar with exact baseline scores)...")
        users_data = [
            {
                "name": "Ramesh Kumar",
                "employee_id": "MOSPI-SO-7429",
                "email": "ramesh.kumar@mospi.gov.in",
                "organization": "Ministry of Statistics and Programme Implementation (MoSPI)",
                "department": "National Sample Survey Office (NSSO)",
                "role_code": "STAT_OFFICER",
                "experience_years": 4.5,
                "is_admin": False,
                "is_sme": False,
                # Specific baseline scores mandated in prompt demo scenario:
                # Sampling Methods: 42% (High Gap)
                # Data Visualization: 35% (High Gap)
                # Statistical Analysis: 61% (Moderate Gap)
                # Data Quality: 82% (Good)
                "scores": {
                    "Sampling Methods": 42.0,
                    "Data Visualization": 35.0,
                    "Statistical Analysis": 61.0,
                    "Data Quality": 82.0,
                    "Official Statistics": 72.0,
                    "Survey Methodology": 75.0,
                    "Data Privacy and Governance": 75.0,
                    "Time Series Analysis": 54.0,
                    "Python": 48.0,
                    "R Programming": 52.0,
                    "Statistical Ethics": 88.0,
                    "Questionnaire Design": 64.0,
                    "Data Collection": 78.0,
                    "Descriptive Statistics": 70.0,
                    "Inferential Statistics": 58.0,
                    "Data Management": 62.0
                }
            },
            {
                "name": "Dr. Priya Sharma",
                "employee_id": "NSSTA-DIR-1002",
                "email": "priya.sharma@nssta.gov.in",
                "organization": "National Statistical Systems Training Academy (NSSTA)",
                "department": "Capacity Building and Academic Affairs",
                "role_code": "STAT_SUPERVISOR",
                "experience_years": 14.0,
                "is_admin": True,
                "is_sme": False,
                "scores": {
                    "Official Statistics": 92.0,
                    "Data Quality": 89.0,
                    "Statistical Ethics": 95.0,
                    "Data Privacy and Governance": 90.0,
                    "Sampling Methods": 86.0
                }
            },
            {
                "name": "Prof. Arvind Swaminathan",
                "employee_id": "ISI-SME-3051",
                "email": "arvind.swaminathan@isi.ac.in",
                "organization": "Indian Statistical Institute (ISI) / MoSPI Advisory",
                "department": "Theoretical Statistics and Survey Research",
                "role_code": "SURVEY_OFFICER",
                "experience_years": 22.0,
                "is_admin": False,
                "is_sme": True,
                "scores": {
                    "Sampling Methods": 98.0,
                    "Survey Methodology": 96.0,
                    "Statistical Analysis": 95.0,
                    "Questionnaire Design": 91.0
                }
            },
            {
                "name": "Ananya Sen",
                "employee_id": "MOSPI-DA-4819",
                "email": "ananya.sen@mospi.gov.in",
                "organization": "Ministry of Statistics and Programme Implementation (MoSPI)",
                "department": "Economic Statistics Division (ESD)",
                "role_code": "DATA_ANALYST",
                "experience_years": 3.0,
                "is_admin": False,
                "is_sme": False,
                "scores": {
                    "Python": 84.0,
                    "R Programming": 79.0,
                    "Data Visualization": 86.0,
                    "Statistical Analysis": 72.0,
                    "Data Management": 78.0
                }
            },
            {
                "name": "Rajesh Verma",
                "employee_id": "MOSPI-FI-9023",
                "email": "rajesh.verma@mospi.gov.in",
                "organization": "Ministry of Statistics and Programme Implementation (MoSPI)",
                "department": "Field Operations Division (FOD - Northern Region)",
                "role_code": "FIELD_INVESTIGATOR",
                "experience_years": 2.0,
                "is_admin": False,
                "is_sme": False,
                "scores": {
                    "Data Collection": 76.0,
                    "Questionnaire Design": 58.0,
                    "Statistical Ethics": 82.0,
                    "Data Quality": 50.0
                }
            }
        ]

        for u_data in users_data:
            role = role_records.get(u_data["role_code"])
            user = User(
                name=u_data["name"],
                employee_id=u_data["employee_id"],
                email=u_data["email"],
                organization=u_data["organization"],
                department=u_data["department"],
                role_id=role.id if role else 1,
                experience_years=u_data["experience_years"],
                is_admin=u_data["is_admin"],
                is_sme=u_data["is_sme"]
            )
            db.add(user)
            db.flush()

            # Seed competency scores
            for comp_name, score_val in u_data["scores"].items():
                comp = comp_records.get(comp_name)
                if comp:
                    cs = CompetencyScore(
                        user_id=user.id,
                        competency_id=comp.id,
                        baseline_score=score_val,
                        current_score=score_val,
                        previous_score=score_val,
                        assessed_level=score_to_level(score_val),
                        gap_category=classify_score(score_val)
                    )
                    db.add(cs)

        print("Seeding iGOT Karmayogi Courses...")
        from backend.services.igot_adapter import MOCK_IGOT_CATALOG
        for item in MOCK_IGOT_CATALOG:
            comp = comp_records.get(item["competency_name"])
            if comp:
                course = Course(
                    igot_course_id=item["igot_course_id"],
                    title=item["title"],
                    provider=item["provider"],
                    competency_id=comp.id,
                    target_level=item["target_level"],
                    duration_hours=item["duration_hours"],
                    rating=item["rating"],
                    thumbnail_url=item["thumbnail_url"],
                    syllabus_summary=item["syllabus_summary"],
                    is_igot_verified=item["is_igot_verified"]
                )
                db.add(course)

        print("Seeding Diagnostic Assessment & Question Bank (50+ questions)...")
        diag_assessment = Assessment(
            title="All-India Statistical Cadre Competency Diagnostic (MoSPI/NSSTA)",
            assessment_type="DIAGNOSTIC",
            description="Official diagnostic assessment benchmarking statistical personnel against the National Statistical Competency Framework.",
            duration_minutes=30,
            total_questions=25
        )
        db.add(diag_assessment)
        db.flush()

        # Extensive question bank covering competencies
        questions_pool = [
            # Sampling Methods
            (
                "Sampling Methods",
                "Which sampling method gives every unit in the target population an equal and known non-zero probability of selection?",
                "Stratified Quota Sampling",
                "Cluster Sampling",
                "Simple Random Sampling (SRS)",
                "Purposive Judgement Sampling",
                "C",
                "Easy",
                "Simple Random Sampling (SRS) ensures every element in the frame possesses identical probability of selection, eliminating systematic bias.",
                "NSSTA Sampling Manual, Chapter 1"
            ),
            (
                "Sampling Methods",
                "In Stratified Random Sampling, what is the core statistical principle guiding the creation of strata?",
                "Maximizing heterogeneity within each stratum and minimizing between-strata differences",
                "Maximizing homogeneity within each stratum and maximizing differences between strata",
                "Selecting equal numbers of respondents regardless of stratum variance",
                "Allowing field investigators to dynamically adjust stratum boundaries during interview",
                "B",
                "Medium",
                "Stratification reduces sampling error by partitioning heterogeneous populations into homogeneous sub-groups, minimizing intra-stratum variance.",
                "NSSTA Sampling Manual, Chapter 2"
            ),
            (
                "Sampling Methods",
                "Under Neyman Allocation for stratified surveys, how is the sample size nh for stratum h determined?",
                "Proportional strictly to unit cost ch",
                "Proportional to the product of stratum size Nh and stratum standard deviation Sh",
                "Equally divided across all strata regardless of size or variability",
                "Strictly proportional to the number of field investigators assigned",
                "B",
                "Hard",
                "Neyman allocation assigns higher sample sizes to larger and more variable strata (Nh * Sh) to minimize the variance of the overall population estimator.",
                "NSSTA Sampling Manual, Section 2.2"
            ),
            (
                "Sampling Methods",
                "What is the Primary Sampling Unit (PSU) typically employed in rural NSSO socioeconomic surveys in India?",
                "District Collectorate HQ",
                "Individual Agricultural Holdings",
                "2011 Census Enumeration Villages",
                "Panchayat Samiti administrative blocks",
                "C",
                "Medium",
                "In rural rounds of NSSO surveys, Census villages serve as the Primary Sampling Units (PSUs), while households serve as the Ultimate Stage Units (USUs).",
                "NSSO Multi-Stage Survey Design Guidelines"
            ),
            # Data Visualization
            (
                "Data Visualization",
                "When displaying the percentage composition of Indian GDP across primary, secondary, and tertiary sectors over a 10-year span, which visual chart is most effective?",
                "Exploded 3D Pie Chart",
                "100% Stacked Area Chart or Stacked Bar Chart",
                "Scatter plot with no trend line",
                "Radar chart with uncalibrated axes",
                "B",
                "Easy",
                "Stacked 100% area or bar charts effectively show both individual category contributions and relative percentage evolutions over time.",
                "MoSPI Statistical Data Presentation Standards"
            ),
            (
                "Data Visualization",
                "In statistical cartography, which map type uses graded color saturation to display regional variations (e.g., district-level literacy rates)?",
                "Choropleth Map",
                "Isarithmic Map",
                "Topographic Contour Map",
                "Flow Network Map",
                "A",
                "Medium",
                "Choropleth maps shade administrative boundaries in proportion to an aggregate statistical variable like poverty headcount or literacy.",
                "National Data Portal Guidelines"
            ),
            # Statistical Analysis
            (
                "Statistical Analysis",
                "In formal hypothesis testing, what does a p-value strictly measure?",
                "The probability that the alternative hypothesis is 100% true",
                "The probability of observing a test statistic as extreme as or more extreme than observed, assuming the null hypothesis is true",
                "The exact margin of error of the sample questionnaire",
                "The percentage of missing data points in the survey sample",
                "B",
                "Medium",
                "The p-value quantifies evidence against the null hypothesis by measuring the likelihood of obtaining results at least as extreme under the null distribution.",
                "ISI Statistical Analysis Handbook"
            ),
            (
                "Statistical Analysis",
                "When multiple linear regression exhibits high multicollinearity among independent economic variables, what is the primary consequence?",
                "Estimated regression coefficients have inflated standard errors, making significance tests unreliable",
                "The R-squared value drops strictly to zero",
                "The dependent variable automatically transforms into a categorical variable",
                "The sample size is halved",
                "A",
                "Hard",
                "Multicollinearity increases the variance of regression coefficient estimates, making them unstable and sensitive to minor data fluctuations.",
                "Econometric Analysis Manual, ESD"
            ),
            # Data Quality
            (
                "Data Quality",
                "In automated data cleaning of CAPI survey records, which imputation method replaces missing values by randomly drawing from a similar respondent in the current survey?",
                "Deductive Imputation",
                "Cold-Deck Imputation",
                "Hot-Deck Imputation",
                "Deterministic Mean Substitution",
                "C",
                "Medium",
                "Hot-deck imputation dynamically identifies a donor respondent with matching demographic attributes from the same survey round to fill missing entries.",
                "MoSPI-DQAD Guidelines, Module 2"
            ),
            (
                "Data Quality",
                "What is the core purpose of a range check in CAPI data collection?",
                "To prevent entry of logically impossible or out-of-bounds numbers at the point of capture",
                "To translate respondent answers from vernacular languages to English automatically",
                "To encrypt respondent bank accounts before sending to cloud servers",
                "To automatically sign off survey schedules without investigator verification",
                "A",
                "Easy",
                "Range checks flag or prohibit numbers outside plausible theoretical or empirical limits (e.g., respondent age < 0 or > 120).",
                "MoSPI-DQAD Guidelines"
            ),
            # Official Statistics
            (
                "Official Statistics",
                "Under which legislation are official statistical officers in India empowered to collect socio-economic and industrial data?",
                "The Information Technology Act, 2000",
                "The Collection of Statistics Act, 2008 (Amended 2017)",
                "The Census Act of 1881",
                "The Reserve Bank of India Act, 1934",
                "B",
                "Easy",
                "The Collection of Statistics Act provides statutory backing for collecting official statistics and guarantees strict confidentiality to respondents.",
                "Institutional Framework of MoSPI"
            ),
            (
                "Official Statistics",
                "Which body acts as the apex autonomous advisory organ guiding statistical policies and resolving inter-agency coordination in India?",
                "Planning Commission of India",
                "National Statistical Commission (NSC)",
                "Securities and Exchange Board of India (SEBI)",
                "Telecom Regulatory Authority of India (TRAI)",
                "B",
                "Easy",
                "The National Statistical Commission (NSC) was set up following the Rangarajan Commission to oversee national statistical quality and standards.",
                "NSC Mandate Brief"
            ),
            # Data Privacy & Governance
            (
                "Data Privacy and Governance",
                "Under the Digital Personal Data Protection (DPDP) Act 2023 and statistical confidentiality norms, how must microdata be treated prior to public research release?",
                "All raw addresses and names must remain published to allow public cross-verification",
                "Direct personal identifiers must be removed and statistical disclosure control (SDC) applied",
                "Microdata can only be shared with foreign commercial marketing companies",
                "No processing is required if the survey was conducted by a state government",
                "B",
                "Medium",
                "Statistical Disclosure Control (SDC) protects respondent privacy through anonymization, top-coding, and perturbation before microdata publication.",
                "DPDP Act & MoSPI Privacy Standard"
            ),
            # Time Series Analysis
            (
                "Time Series Analysis",
                "What does the X-13ARIMA-SEATS seasonal adjustment algorithm eliminate from macroeconomic time series?",
                "Underlying long-term economic growth trends",
                "Predictable intra-year seasonal and calendar/trading-day variations",
                "Random historical recessions and emergency shocks",
                "Data transcription typos in consumer price indices",
                "B",
                "Hard",
                "Seasonal adjustment decouples repetitive intra-year oscillations (festivals, crop cycles) from the underlying trend-cycle to allow quarter-on-quarter comparisons.",
                "Time Series Methodology Brief"
            ),
            # Survey Methodology
            (
                "Survey Methodology",
                "What is the difference between Sampling Error and Non-Sampling Error?",
                "Sampling error occurs only in censuses; non-sampling error occurs only in sample surveys",
                "Sampling error decreases as sample size increases; non-sampling error can persist or worsen regardless of sample size",
                "Sampling error is intentional fraud; non-sampling error is mathematical uncertainty",
                "Non-sampling errors cannot be identified through pilot testing",
                "B",
                "Medium",
                "Sampling error is mathematically bound to sample size; non-sampling error (measurement, recall, non-response) can occur across any survey or complete census.",
                "NSSO Survey Methodology Guidelines"
            )
        ]

        for q_tuple in questions_pool:
            comp_name, q_text, opt_a, opt_b, opt_c, opt_d, cor, diff, exp, src = q_tuple
            comp = comp_records.get(comp_name)
            if comp:
                q = Question(
                    assessment_id=diag_assessment.id,
                    competency_id=comp.id,
                    question_text=q_text,
                    option_a=opt_a,
                    option_b=opt_b,
                    option_c=opt_c,
                    option_d=opt_d,
                    correct_option=cor,
                    difficulty=diff,
                    explanation=exp,
                    source_reference=src
                )
                db.add(q)

        db.commit()

        print("Ingesting sample training documents into Document Pipeline...")
        # Ingest mospi_sampling_methodology.txt
        sample_doc_path = settings.BASE_DIR / "sample_documents" / "mospi_sampling_methodology.txt"
        if sample_doc_path.exists():
            ramesh = db.query(User).filter(User.employee_id == "MOSPI-SO-7429").first()
            doc_rec = Document(
                user_id=ramesh.id if ramesh else 1,
                filename="MoSPI_Sampling_Methodology_Manual_2026.txt",
                stored_path=str(sample_doc_path),
                file_type="TXT",
                file_size_bytes=sample_doc_path.stat().st_size,
                processing_status="READY",
                extracted_topics="Sampling Methods,Simple Random Sampling,Stratified Sampling,Cluster Sampling,Data Quality"
            )
            db.add(doc_rec)
            db.commit()
            db.refresh(doc_rec)

            pages_content = document_service.extract_text(str(sample_doc_path), "TXT")
            doc_rec.page_count = len(pages_content)
            chunks = document_service.chunk_document(pages_content)
            for c in chunks:
                db.add(DocumentChunk(
                    document_id=doc_rec.id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    section_title=c["section_title"],
                    content=c["content"],
                    token_count=c["token_count"]
                ))
            db.commit()

            # Pre-generate grounded MCQs for this document so demo runs instantly
            from backend.services.ai_service import ai_service
            print("Generating grounded MCQs for sample document...")
            ai_service.generate_grounded_mcqs(db, doc_rec, num_questions=10, difficulty="Mixed")

        db.commit()
        print("Database successfully seeded with production-quality demo state!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
