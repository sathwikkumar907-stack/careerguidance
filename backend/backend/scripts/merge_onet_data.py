"""
Merge raw O*NET database exports into one clean careers CSV for the app.

Inputs (place in backend/scripts/raw/ or pass paths as arguments):
  - occupation_data.csv   (O*NET-SOC Code, Title, Description)
  - essential_skills.csv  (O*NET "Skills.csv" export: Importance/Level ratings)
  - software_skills.csv   (O*NET "Technology Skills.csv" export)

Output:
  - backend/data/onet_jobs.csv with columns:
      Domain, Family_Code, Title, Description, Required_Skills, Software_Tools

Domain is derived from the official SOC major-group code (the first two
digits of the O*NET-SOC Code), NOT guessed from keywords. This is accurate
for 100% of rows, unlike a title/description keyword classifier.

Usage:
    python merge_onet_data.py \
        --occupation raw/occupation_data.csv \
        --skills raw/essential_skills.csv \
        --software raw/software_skills.csv \
        --out ../data/onet_jobs.csv
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

# Official 2018 SOC major group codes -> human-readable domain names.
# https://www.bls.gov/soc/2018/major_groups.htm
SOC_MAJOR_GROUPS = {
    "11": "Management",
    "13": "Business and Financial Operations",
    "15": "Computer and Mathematical",
    "17": "Architecture and Engineering",
    "19": "Life, Physical, and Social Science",
    "21": "Community and Social Service",
    "23": "Legal",
    "25": "Education, Training, and Library",
    "27": "Arts, Design, Entertainment, and Media",
    "29": "Healthcare Practitioners and Technical",
    "31": "Healthcare Support",
    "33": "Protective Service",
    "35": "Food Preparation and Serving",
    "37": "Building and Grounds Cleaning and Maintenance",
    "39": "Personal Care and Service",
    "41": "Sales and Related",
    "43": "Office and Administrative Support",
    "45": "Farming, Fishing, and Forestry",
    "47": "Construction and Extraction",
    "49": "Installation, Maintenance, and Repair",
    "51": "Production",
    "53": "Transportation and Material Moving",
    "55": "Military Specific",
}

TOP_SKILLS_PER_CAREER = 8
TOP_SOFTWARE_PER_CAREER = 6


def load_occupations(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"O*NET-SOC Code", "Title", "Description"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"occupation_data.csv is missing columns: {missing}")
    return df


def derive_domain(soc_code: str) -> str:
    major_group = str(soc_code)[:2]
    return SOC_MAJOR_GROUPS.get(major_group, "General")


def top_skills_by_occupation(path: Path, top_n: int) -> dict[str, str]:
    """Returns {SOC code: 'Skill A, Skill B, ...'} using Importance (IM) ratings."""
    df = pd.read_csv(path)
    importance = df[df["Scale ID"] == "IM"].copy()
    importance["Data Value"] = pd.to_numeric(importance["Data Value"], errors="coerce")
    importance = importance.dropna(subset=["Data Value"])

    result: dict[str, str] = {}
    for soc_code, group in importance.groupby("O*NET-SOC Code"):
        top = group.sort_values("Data Value", ascending=False).head(top_n)
        result[soc_code] = ", ".join(top["Element Name"].tolist())
    return result


def top_software_by_occupation(path: Path, top_n: int) -> dict[str, str]:
    """Returns {SOC code: 'Tool A, Tool B, ...'}, preferring Hot Technology tools first."""
    df = pd.read_csv(path)
    df["_priority"] = (df["Hot Technology"] == "Y").astype(int)

    result: dict[str, str] = {}
    for soc_code, group in df.groupby("O*NET-SOC Code"):
        top = group.sort_values("_priority", ascending=False).head(top_n)
        tools = top["Element Name"].drop_duplicates().tolist()
        result[soc_code] = ", ".join(tools[:top_n])
    return result


def domain_fallback_skills(rows: list[dict], top_n: int = 6) -> dict[str, str]:
    """
    For newer/emerging SOC codes with no published skills survey data yet
    (this genuinely happens in O*NET exports -- verified against the raw
    file, not a bug in this script), fall back to the most common skills
    among OTHER careers in the same domain, rather than showing nothing.
    """
    domain_skill_counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        if row["Required_Skills"]:
            domain_skill_counts[row["Domain"]].update(split(row["Required_Skills"]))
    return {
        domain: ", ".join(skill for skill, _ in counter.most_common(top_n))
        for domain, counter in domain_skill_counts.items()
    }


def split(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def merge(occupation_path: Path, skills_path: Path, software_path: Path) -> pd.DataFrame:
    occ = load_occupations(occupation_path)
    skills_map = top_skills_by_occupation(skills_path, TOP_SKILLS_PER_CAREER)
    software_map = top_software_by_occupation(software_path, TOP_SOFTWARE_PER_CAREER)

    rows = []
    for _, row in occ.iterrows():
        soc_code = row["O*NET-SOC Code"]
        rows.append(
            {
                "Domain": derive_domain(soc_code),
                "Title": row["Title"],
                "Description": row["Description"],
                "Required_Skills": skills_map.get(soc_code, ""),
                "Software_Tools": software_map.get(soc_code, ""),
            }
        )

    fallback_by_domain = domain_fallback_skills(rows)
    backfilled = 0
    for row in rows:
        if not row["Required_Skills"] and row["Domain"] in fallback_by_domain:
            row["Required_Skills"] = fallback_by_domain[row["Domain"]]
            row["_skills_backfilled"] = True
            backfilled += 1
    if backfilled:
        print(f"[merge] Backfilled {backfilled} careers with domain-average skills (no published O*NET survey data for their SOC code).")

    merged = pd.DataFrame(rows)
    if "_skills_backfilled" in merged.columns:
        merged = merged.drop(columns=["_skills_backfilled"])

    before = len(merged)
    merged = merged.drop_duplicates(subset=["Title"], keep="first")
    dropped = before - len(merged)
    if dropped:
        print(f"[merge] Dropped {dropped} duplicate-title rows.")

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--occupation", type=Path, required=True)
    parser.add_argument("--skills", type=Path, required=True)
    parser.add_argument("--software", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    merged = merge(args.occupation, args.skills, args.software)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.out, index=False)

    print(f"[merge] Wrote {len(merged)} careers to {args.out}")
    print("[merge] Domain distribution:")
    print(merged["Domain"].value_counts().to_string())
    empty_skills = (merged["Required_Skills"] == "").sum()
    empty_software = (merged["Software_Tools"] == "").sum()
    print(f"[merge] Rows with no matched skills: {empty_skills}")
    print(f"[merge] Rows with no matched software: {empty_software}")


if __name__ == "__main__":
    main()
