#idrees Dehistani (500992020)

#install beforehand: pip install psycopg2 pandas python-dotenv


#We use dotenv to read the .env file and set the environment variables.
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


#connect to the database once; every function below reuses this same connection
conn = psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    dbname=os.getenv("PGDATABASE", "movies_db"),
    user=os.getenv("PGUSER", "ed2"),
    password=os.environ["PGPASSWORD"],  #my password is in .env file.
    port=5432,
)


#returns query results as a DataFrame instead of printing them.
#every function below uses this one, so we write the execute/fetch code only once.
def query_df(sql, params=None):
    return pd.read_sql(sql, conn, params=params)




# gap     = userscore - metascore   (signed; > 0 means audience liked it MORE)
# abs_gap = |userscore - metascore| (the "size" of the gap that H2 is about)

#we need runtime, rating and both scores in one row, plus the gap itself so we create a view.
def create_view():
    cur = conn.cursor()
    cur.execute("""
    CREATE OR REPLACE VIEW gap_analysis AS
    SELECT m.movieid,
           m.title,
           NULLIF(m.runtime, 0)    AS runtime,     -- turn 0 into NULL (0 = missing)
           NULLIF(m.prodbudget, 0) AS budget,      -- turn 0 into NULL (0 = missing)
           CASE                                         -- group the rating text
               WHEN m.rating LIKE 'TV-%'               THEN 'TV'         -- all TV-* into one group
               WHEN btrim(coalesce(m.rating, '')) = '' THEN 'Not Rated'  -- NULL or blank
               ELSE m.rating::text                                       -- otherwise keep as-is
           END                                         AS rating_group,
           s.userscore,                            -- audience score (0-100)
           s.metascore,                            -- critic score   (0-100)
           s.userscore - s.metascore               AS gap,
           abs(s.userscore - s.metascore)          AS abs_gap
    FROM movie m
    JOIN score s ON s.movieid = m.movieid;
    """)

    #we have to commit the changes to our database, just like github
    conn.commit()
    cur.close()


#1 - all film-level gap data. Optional rating filter
def get_gap_data(rating=None):
    if rating:
        return query_df("SELECT * FROM gap_analysis WHERE rating_group = %(r)s;", {"r": rating})
    return query_df("SELECT * FROM gap_analysis;")


#2 - how big is the gap overall?
#average gap, keeping + and − 
def gap_baseline():
    return query_df("""
        SELECT count(*)                              AS n_films,
               round(avg(gap), 2)                    AS avg_signed_gap, 
               round(avg(abs_gap), 2)                AS avg_abs_gap,
               round(100.0 * avg((gap > 0)::int), 1) AS pct_audience_higher
        FROM gap_analysis;
    """)
# the ::int: turns true into 1 and false into 0



#3 - Gap by RATING
def gap_by_rating():
    return query_df("""
        SELECT rating_group,
               count(*)               AS n_films,
               round(avg(gap), 2)     AS avg_signed_gap,
               round(avg(abs_gap), 2) AS avg_abs_gap
        FROM gap_analysis
        GROUP BY rating_group
        ORDER BY n_films DESC;
    """)
#do audiences and critics disagree more for some ratings than others?


# 4 -gap by runtime band case turns minutes into 4 readable bands.
def gap_by_runtime():
    return query_df("""
        SELECT CASE
                   WHEN runtime < 90  THEN '1. under 90 min'
                   WHEN runtime < 120 THEN '2. 90-119 min'
                   WHEN runtime < 150 THEN '3. 120-149 min'
                   ELSE                    '4. 150+ min'
               END                    AS runtime_band,
               count(*)               AS n_films,
               round(avg(gap), 2)     AS avg_signed_gap,
               round(avg(abs_gap), 2) AS avg_abs_gap
        FROM gap_analysis
        WHERE runtime IS NOT NULL
        GROUP BY runtime_band
        ORDER BY runtime_band;
    """)


#5 - gap by budget band
def gap_by_budget():
    return query_df("""
        SELECT CASE
                   WHEN budget < 10000000  THEN '1. under $10M'
                   WHEN budget < 50000000  THEN '2. $10-50M'
                   WHEN budget < 100000000 THEN '3. $50-100M'
                   ELSE                         '4. $100M+'
               END                    AS budget_band,
               count(*)               AS n_films,
               round(avg(gap), 2)     AS avg_signed_gap,
               round(avg(abs_gap), 2) AS avg_abs_gap
        FROM gap_analysis
        WHERE budget IS NOT NULL
        GROUP BY budget_band
        ORDER BY budget_band;
    """)
#we choose band not numeric budget beacause budgets range from a few thousand to hundreds of millions


#6- direct test of H2: (-1 to +1) of the gap with runtime and budget.
def gap_correlations():
    return query_df("""
        SELECT round(corr(gap, runtime)::numeric, 3)     AS corr_signedgap_runtime,
               round(corr(abs_gap, runtime)::numeric, 3) AS corr_absgap_runtime,
               round(corr(gap, budget)::numeric, 3)      AS corr_signedgap_budget,
               round(corr(abs_gap, budget)::numeric, 3)  AS corr_absgap_budget
        FROM gap_analysis;
    """)
#corr() is postgre’s built in pearson correlation between two columns
#::numeric is to round to 3 decimal places

#7 - dataset for future statistics: one row per film with the gap, film characteristics, box office and ROI (revenue / budget) in one table
def get_ml_dataset():
    return query_df("""
        SELECT g.*,
               sa.theater_count,
               COALESCE(sa.domestic, 0) + COALESCE(sa.international, 0) AS worldwide,
               (COALESCE(sa.domestic, 0) + COALESCE(sa.international, 0))::numeric
                   / NULLIF(g.budget, 0) AS roi
        FROM gap_analysis g
        JOIN movie_sales ms ON ms.movieid = g.movieid
        JOIN sales sa       ON sa.salesid = ms.salesid;
    """)


#runs only when we start this file directly in terminal (python main.py)
if __name__ == "__main__":
    create_view()  #build the view before we query it

    print("\n=== SQ2.0 Baseline ===\n",       gap_baseline())
    print("\n=== SQ2.1 Gap by rating ===\n",  gap_by_rating())
    print("\n=== SQ2.2 Gap by runtime ===\n", gap_by_runtime())
    print("\n=== SQ2.3 Gap by budget ===\n",  gap_by_budget())
    print("\n=== SQ2.4 Correlations ===\n",   gap_correlations())

    #export to CSV for the statistics module (h2_stats.py) and future ML
    get_gap_data().to_csv("gap_analysis.csv", index=False)
    get_ml_dataset().to_csv("ml_dataset.csv", index=False)
    print("\nExported gap_analysis.csv and ml_dataset.csv")

    conn.close()  #after we are done, we need to close the connection
