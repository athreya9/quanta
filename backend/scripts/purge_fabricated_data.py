"""
One-time cleanup: removes fabricated/synthetic records that were created by
the pre-fix version of QUANTA (hardcoded fake executive database, random-
number "intent signals", guessed emails for real CEOs, etc).

Safe to run multiple times (idempotent). Run this once, right after deploying
the fixed code and BEFORE restarting the service (or immediately after - the
new code never recreates these fabricated rows).

Identification logic (see AUDIT notes / commit message for full context):
  - ALL rows in linkedin_profiles were from the hardcoded fake seed list.
    There is no legitimate historical data here - the table only ever
    contained the fabricated seed.
  - Leads with outreach_playbook set were only ever created by the old
    crawler.py / outsourcing_crawler.py fabrication pipeline - the real
    contact-form path never set this field.
  - extension_signals rows with source in ('qeic_crawler', 'outsourcing_crawler')
    were, before this fix, always fabricated (random numbers / hardcoded
    fake companies). The fixed crawlers reuse the same source tags for
    genuinely real data going forward, so this script must be run BEFORE
    the fixed crawlers get a chance to write fresh rows - run it
    immediately after deploy, before/at the same time as restarting uvicorn.

Usage:
    cd backend
    ./venv/bin/python scripts/purge_fabricated_data.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.crm import engine

def main():
    with engine.connect() as conn:
        linkedin_deleted = conn.execute(text("DELETE FROM linkedin_profiles")).rowcount
        leads_deleted = conn.execute(text("DELETE FROM leads WHERE outreach_playbook IS NOT NULL")).rowcount
        signals_deleted = conn.execute(
            text("DELETE FROM extension_signals WHERE source IN ('qeic_crawler', 'outsourcing_crawler')")
        ).rowcount
        conn.commit()

    print(f"Purged {linkedin_deleted} fabricated LinkedIn profiles")
    print(f"Purged {leads_deleted} fabricated CRM leads (had an auto-generated outreach_playbook)")
    print(f"Purged {signals_deleted} fabricated crawler signals")
    print("Done. Any real contact-form leads and real chrome_extension signals were left untouched.")

if __name__ == "__main__":
    main()
