import sqlite3
from datetime import datetime

# the path to the database
DATABASE_PATH = "evidence_store.db"


def save_decision(record, decision, run_id):
    # we save every decision (approve, flag or reject), that way the db always matches what the reviewer decided (team report section 2.2)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("""CREATE TABLE IF NOT EXISTS decisions (
        run_id TEXT, pubmed_id TEXT, doi TEXT, title TEXT, authors TEXT, publication_date TEXT, abstract TEXT, decision TEXT, decision_date TEXT)""")

    # we prepare the values, in the same order as the columns of the table
    authors = ", ".join(record.authors)
    decision_date = str(datetime.now())

    # we use ? so titles with an apostrophe don't break the query
    connection.execute("INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (run_id, record.pubmed_id, record.doi, record.title, authors, record.publication_date, record.abstract, decision, decision_date))
    connection.commit()
    connection.close()
 

def get_approved():
    # the evidence store is the approved papers
    connection = sqlite3.connect(DATABASE_PATH)
    rows = connection.execute("SELECT pubmed_id, title FROM decisions WHERE decision = 'approve'").fetchall()
    connection.close()
    return rows