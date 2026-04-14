#!/usr/bin/env python3
"""
Fetch latest bipolar disorder research papers from PubMed E-utilities API.
Targets core bipolar journals and adjacent high-yield journals across
psychiatry, psychology, neuroscience, PT, OT, and TCM.
"""

import json
import sys
import argparse
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote_plus

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

JOURNALS_CORE = [
    "Bipolar Disorders",
    "International Journal of Bipolar Disorders",
    "Journal of Affective Disorders",
    "American Journal of Psychiatry",
    "JAMA Psychiatry",
    "The Lancet Psychiatry",
    "Acta Psychiatrica Scandinavica",
    "Journal of Psychiatric Research",
    "Psychiatry Research",
    "BMC Psychiatry",
]

JOURNALS_PSYCHOLOGY = [
    "Clinical Psychology Review",
    "Journal of Clinical Psychology",
    "Behaviour Research and Therapy",
    "Psychotherapy and Psychosomatics",
    "Cognitive Therapy and Research",
    "Journal of Consulting and Clinical Psychology",
]

JOURNALS_NEUROSCIENCE = [
    "Biological Psychiatry",
    "Molecular Psychiatry",
    "Neuropsychopharmacology",
    "Translational Psychiatry",
    "European Neuropsychopharmacology",
    "Psychiatry Research Neuroimaging",
    "Neuroscience Biobehavioral Reviews",
]

JOURNALS_PT_REHAB = [
    "Mental Health and Physical Activity",
    "Physiotherapy Theory and Practice",
    "Disability and Rehabilitation",
    "Journal of Bodywork and Movement Therapies",
]

JOURNALS_OT = [
    "Occupational Therapy in Mental Health",
    "OTJR Occupation Participation and Health",
    "American Journal of Occupational Therapy",
    "Hong Kong Journal of Occupational Therapy",
    "Journal of Psychiatric and Mental Health Nursing",
]

JOURNALS_TCM = [
    "Chinese Medicine",
    "Chinese Journal of Integrative Medicine",
    "Journal of Integrative Medicine",
    "Complementary Therapies in Medicine",
    "BMC Complementary Medicine and Therapies",
]

ALL_JOURNALS = (
    JOURNALS_CORE
    + JOURNALS_PSYCHOLOGY
    + JOURNALS_NEUROSCIENCE
    + JOURNALS_PT_REHAB
    + JOURNALS_OT
    + JOURNALS_TCM
)

SEARCH_QUERIES = [
    '(("Bipolar Disorder"[Mesh] OR "bipolar disorder"[Title/Abstract] OR "bipolar I"[Title/Abstract] OR "bipolar II"[Title/Abstract] OR mania[Title/Abstract] OR hypomania[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR "bipolar depression"[Title/Abstract] OR ((bipolar[Title/Abstract]) AND (depression[Title/Abstract] OR depressive[Title/Abstract]))))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (diagnos*[Title/Abstract] OR "differential diagnosis"[Title/Abstract] OR misdiagnos*[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (relapse[Title/Abstract] OR recurrence[Title/Abstract] OR maintenance[Title/Abstract] OR prophylaxis[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (suicid*[Title/Abstract] OR "self-harm"[Title/Abstract] OR self-injur*[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (sleep[Title/Abstract] OR insomnia[Title/Abstract] OR circadian[Title/Abstract] OR "social rhythm"[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (cognit*[Title/Abstract] OR neurocognit*[Title/Abstract] OR "executive function"[Title/Abstract] OR "functional recovery"[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (psychotherapy[Title/Abstract] OR psychoeducation[Title/Abstract] OR "cognitive behavioral therapy"[Title/Abstract] OR CBT[Title/Abstract] OR "family-focused therapy"[Title/Abstract] OR IPSRT[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (lithium[Title/Abstract] OR valproate[Title/Abstract] OR lamotrigine[Title/Abstract] OR quetiapine[Title/Abstract] OR lurasidone[Title/Abstract] OR aripiprazole[Title/Abstract] OR "mood stabilizer"[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (neuroimaging[Title/Abstract] OR MRI[Title/Abstract] OR fMRI[Title/Abstract] OR biomarker*[Title/Abstract] OR inflammation[Title/Abstract] OR BDNF[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (exercise[Title/Abstract] OR "physical activity"[Title/Abstract] OR physiotherapy[Title/Abstract] OR rehabilitation[Title/Abstract] OR yoga[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND ("occupational therapy"[Title/Abstract] OR "occupational functioning"[Title/Abstract] OR "functional recovery"[Title/Abstract] OR participation[Title/Abstract] OR "vocational rehabilitation"[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND ("traditional Chinese medicine"[Title/Abstract] OR TCM[Title/Abstract] OR acupuncture[Title/Abstract] OR electroacupuncture[Title/Abstract] OR "Chinese herbal medicine"[Title/Abstract] OR "integrative medicine"[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND (child*[Title/Abstract] OR adolescent*[Title/Abstract] OR youth[Title/Abstract] OR pediatric[Title/Abstract]))',
    '(("Bipolar Disorder"[Mesh] OR bipolar[Title/Abstract]) AND ("systematic review"[Title/Abstract] OR "meta-analysis"[Publication Type] OR meta-analysis[Title/Abstract]))',
]

HEADERS = {"User-Agent": "BipolarBrainBot/1.0 (research aggregator)"}


def build_query(days: int = 7) -> str:
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_part = f'"{lookback}"[Date - Publication] : "3000"[Date - Publication]'
    journal_part = " OR ".join([f'"{j}"[Journal]' for j in ALL_JOURNALS])
    return f"({journal_part}) AND {date_part}"


def build_topic_queries(days: int = 7) -> list[str]:
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_part = f'"{lookback}"[Date - Publication] : "3000"[Date - Publication]'
    queries = []
    for sq in SEARCH_QUERIES:
        queries.append(f"({sq}) AND {date_part}")
    return queries


def search_papers(query: str, retmax: int = 20) -> list[str]:
    params = (
        f"?db=pubmed&term={quote_plus(query)}&retmax={retmax}&sort=date&retmode=json"
    )
    url = PUBMED_SEARCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[ERROR] PubMed search failed: {e}", file=sys.stderr)
        return []


def fetch_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    papers = []
    batch_size = 50
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        ids = ",".join(batch)
        params = f"?db=pubmed&id={ids}&retmode=xml"
        url = PUBMED_FETCH + params
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=60) as resp:
                xml_data = resp.read().decode()
        except Exception as e:
            print(
                f"[ERROR] PubMed fetch failed (batch {i // batch_size + 1}): {e}",
                file=sys.stderr,
            )
            continue

        try:
            root = ET.fromstring(xml_data)
            for article in root.findall(".//PubmedArticle"):
                medline = article.find(".//MedlineCitation")
                art = medline.find(".//Article") if medline else None
                if art is None:
                    continue

                title_el = art.find(".//ArticleTitle")
                title = (
                    (title_el.text or "").strip()
                    if title_el is not None and title_el.text
                    else ""
                )
                if not title:
                    continue

                abstract_parts = []
                for abs_el in art.findall(".//Abstract/AbstractText"):
                    label = abs_el.get("Label", "")
                    text = "".join(abs_el.itertext()).strip()
                    if label and text:
                        abstract_parts.append(f"{label}: {text}")
                    elif text:
                        abstract_parts.append(text)
                abstract = " ".join(abstract_parts)[:2000]

                journal_el = art.find(".//Journal/Title")
                journal = (
                    (journal_el.text or "").strip()
                    if journal_el is not None and journal_el.text
                    else ""
                )

                pub_date = art.find(".//PubDate")
                date_str = ""
                if pub_date is not None:
                    year = pub_date.findtext("Year", "")
                    month = pub_date.findtext("Month", "")
                    day = pub_date.findtext("Day", "")
                    parts = [p for p in [year, month, day] if p]
                    date_str = " ".join(parts)

                pmid_el = medline.find(".//PMID")
                pmid = pmid_el.text if pmid_el is not None else ""
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

                keywords = []
                for kw in medline.findall(".//KeywordList/Keyword"):
                    if kw.text:
                        keywords.append(kw.text.strip())

                papers.append(
                    {
                        "pmid": pmid,
                        "title": title,
                        "journal": journal,
                        "date": date_str,
                        "abstract": abstract,
                        "url": link,
                        "keywords": keywords,
                    }
                )
        except ET.ParseError as e:
            print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)

        if i + batch_size < len(pmids):
            time.sleep(0.5)

    return papers


def main():
    parser = argparse.ArgumentParser(
        description="Fetch bipolar disorder papers from PubMed"
    )
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument(
        "--max-papers", type=int, default=50, help="Max papers to fetch"
    )
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_pmids = set()

    journal_query = build_query(days=args.days)
    print(
        f"[INFO] Searching by journal list (last {args.days} days)...", file=sys.stderr
    )
    pmids = search_papers(journal_query, retmax=args.max_papers)
    all_pmids.update(pmids)
    print(f"[INFO] Journal search found {len(pmids)} papers", file=sys.stderr)

    topic_queries = build_topic_queries(days=args.days)
    print(
        f"[INFO] Running {len(topic_queries)} topic-specific searches...",
        file=sys.stderr,
    )
    for i, tq in enumerate(topic_queries):
        pmids = search_papers(tq, retmax=15)
        new = set(pmids) - all_pmids
        all_pmids.update(new)
        if new:
            print(f"  Query {i + 1}: +{len(new)} new papers", file=sys.stderr)
        time.sleep(0.4)

    print(f"[INFO] Total unique PMIDs: {len(all_pmids)}", file=sys.stderr)

    pmid_list = list(all_pmids)[: args.max_papers]

    if not pmid_list:
        print("NO_CONTENT", file=sys.stderr)
        if args.json:
            output = json.dumps(
                {
                    "date": datetime.now(timezone(timedelta(hours=8))).strftime(
                        "%Y-%m-%d"
                    ),
                    "count": 0,
                    "papers": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            if args.output == "-":
                print(output)
            else:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
        return

    papers = fetch_details(pmid_list)
    print(f"[INFO] Fetched details for {len(papers)} papers", file=sys.stderr)

    seen_titles = set()
    unique_papers = []
    for p in papers:
        key = p["title"].lower().strip()[:80]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_papers.append(p)

    output_data = {
        "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
        "count": len(unique_papers),
        "papers": unique_papers,
    }

    out_str = json.dumps(output_data, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(out_str)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"[INFO] Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
