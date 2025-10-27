"""
Query Revision History
Queries the database for revision history information.
"""

from datastore import LogcodeDatastore
from pathlib import Path


def query_logcode_revision_history(db_path: str, logcode: str):
    """Query revision history for a specific logcode"""
    db = LogcodeDatastore(db_path)

    print(f"\n{'='*80}")
    print(f"REVISION HISTORY FOR LOGCODE: {logcode.upper()}")
    print(f"{'='*80}\n")

    revisions = db.search_revisions_by_logcode(logcode)

    if not revisions:
        print(f"No revision history found for logcode {logcode.upper()}")
    else:
        for rev in revisions:
            print(f"Revision: {rev['revision']}")
            print(f"Date:     {rev['date']}")
            print(f"Status:   {rev['status']}")
            print("-" * 80)

    db.close()


def query_revisions_by_date(db_path: str, month: str, year: str):
    """Query all revisions for a specific month and year"""
    db = LogcodeDatastore(db_path)

    print(f"\n{'='*80}")
    print(f"LOGCODES UPDATED/NEW IN {month.upper()} {year}")
    print(f"{'='*80}\n")

    revisions = db.get_revisions_by_date(month, year)

    if not revisions:
        print(f"No revisions found for {month} {year}")
    else:
        for rev_data in revisions:
            print(f"Revision: {rev_data['revision']}")
            print(f"Date:     {rev_data['date']}\n")

            if rev_data['updated_logcodes']:
                print("  UPDATED Logcodes:")
                for logcode in rev_data['updated_logcodes']:
                    print(f"    - {logcode}")
                print()

            if rev_data['new_logcodes']:
                print("  NEW Logcodes:")
                for logcode in rev_data['new_logcodes']:
                    print(f"    - {logcode}")
                print()

            print("-" * 80)

    db.close()


def query_revision_by_code(db_path: str, revision_code: str):
    """Query revision details by revision code"""
    db = LogcodeDatastore(db_path)

    print(f"\n{'='*80}")
    print(f"LOGCODES IN REVISION: {revision_code.upper()}")
    print(f"{'='*80}\n")

    rev_data = db.get_revisions_by_code(revision_code)

    if not rev_data:
        print(f"Revision {revision_code.upper()} not found in database")
    else:
        print(f"Revision: {rev_data['revision']}")
        print(f"Date:     {rev_data['date']}\n")

        if rev_data['updated_logcodes']:
            print(f"  UPDATED Logcodes ({len(rev_data['updated_logcodes'])} total):")
            for logcode in rev_data['updated_logcodes']:
                print(f"    - {logcode}")
            print()

        if rev_data['new_logcodes']:
            print(f"  NEW Logcodes ({len(rev_data['new_logcodes'])} total):")
            for logcode in rev_data['new_logcodes']:
                print(f"    - {logcode}")
            print()

    db.close()


if __name__ == "__main__":
    # Database path
    db_path = "../data/parsed_logcodes.db"

    # Check if database exists
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the parser first to create the database.")
        exit(1)

    # Query 1: Revision history for logcode 0x1C1A
    query_logcode_revision_history(db_path, "0x1C1A")

    # Query 2: Logcodes updated/new in February 2025
    query_revisions_by_date(db_path, "February", "2025")

    # Query 3: Logcodes in revision FL
    query_revision_by_code(db_path, "FL")
