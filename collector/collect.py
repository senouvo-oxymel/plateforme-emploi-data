"""Collecte quotidienne depuis les API publiques configurées.
La clé Supabase de service reste côté serveur (GitHub Actions), jamais dans le site.
"""
import os, re, datetime as dt
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]
HEADERS = {"apikey": SECRET_KEY, "Content-Type": "application/json",
           "Prefer": "resolution=merge-duplicates,return=minimal"}

# Sources API publiques. Remotive est lu une fois par jour (limite conseillée : 4/jour max).
SOURCES = [
    ("remotive", "https://remotive.com/api/remote-jobs?category=data", 1),
    ("arbeitnow", "https://www.arbeitnow.com/api/job-board-api", 3),
]
DATA_WORDS = re.compile(r"data|analyt|business intelligence|bi analyst|scientist|machine learning|intelligence artificielle|data engineer|analytics", re.I)
SKILL_WORDS = ["SQL", "Python", "Power BI", "Tableau", "Excel", "dbt", "AWS", "Azure", "GCP", "Spark", "Statistics", "DAX", "ETL", "Airflow"]

def extract_items(source, payload):
    if source == "remotive":
        return payload.get("jobs", [])
    return payload.get("data", [])

def normalize(source, item):
    title = item.get("title", "").strip()
    description = item.get("description", "") or ""
    if not DATA_WORDS.search(title + " " + description[:5000]):
        return None
    url = item.get("url") or item.get("job_url")
    if not url:
        return None
    text = re.sub(r"<[^>]+>", " ", description)
    skills = [s for s in SKILL_WORDS if re.search(r"\b" + re.escape(s) + r"\b", title + " " + text, re.I)]
    created = item.get("publication_date") or item.get("created_at")
    try:
        if isinstance(created, (int, float)) or (isinstance(created, str) and created.isdigit()):
            published = dt.datetime.fromtimestamp(float(created), tz=dt.timezone.utc).isoformat()
        else:
            parsed = dt.datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
            if parsed and parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            published = parsed.isoformat() if parsed else None
    except (ValueError, AttributeError, OSError, OverflowError):
        published = None
    location = item.get("candidate_required_location") or item.get("location") or "Non précisé"
    remote = source == "remotive" or bool(item.get("remote")) or "remote" in (str(item.get("job_type", "")) + str(location)).lower()
    job_types = item.get("job_types")
    contract_type = item.get("job_type") or (job_types[0] if isinstance(job_types, list) and job_types else None)
    return {"source_id": source, "source_url": url, "title": title,
            "company": item.get("company_name") or item.get("company") or "Employeur non précisé",
            "country": location, "location": location,
            "work_mode": "Remote (éligibilité pays à vérifier)" if remote else "À préciser",
            "contract_type": contract_type, "salary": item.get("salary"),
            "published_at": published, "description": text[:4000], "skills": skills,
            "collected_at": dt.datetime.now(dt.timezone.utc).isoformat()}

def main():
    session = requests.Session(); session.headers.update({"User-Agent": "DataJobWatch/1.0 contact: configure-in-deployment"})
    rows = []
    successful_sources = []
    for source, url, max_pages in SOURCES:
        try:
            for page in range(1, max_pages + 1):
                page_url = f"{url}&page={page}" if "?" in url else f"{url}?page={page}"
                response = session.get(page_url, timeout=30); response.raise_for_status()
                payload = response.json()
                items = extract_items(source, payload)
                if page == 1:
                    successful_sources.append(source)
                for item in items:
                    row = normalize(source, item)
                    if row: rows.append(row)
                if not items or source == "remotive":
                    break
            print(f"{source}: source lue")
        except Exception as exc:
            print(f"{source}: erreur de collecte: {exc}")
    if not successful_sources:
        raise RuntimeError("Aucune source n'a répondu. La base n'a pas été modifiée.")
    if rows:
        resp = session.post(f"{SUPABASE_URL}/rest/v1/job_offers?on_conflict=source_id,source_url", headers=HEADERS, json=rows, timeout=60)
        resp.raise_for_status()
    print(f"{len(rows)} annonce(s) insérée(s)/actualisée(s)")

if __name__ == "__main__": main()
