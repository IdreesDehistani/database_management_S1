import psycopg2          # library to connect Python to PostgreSQL
import pandas as pd      # used to return query results as tables (DataFrames)


class MovieRoiAnalyzer:
    # PRIVATE SQL BUILDING BLOCKS
    # The pieces of querry that are repeated across multiple queries


    # ROI formula: (total sales - budget) / budget * 100, averaged per group.
    # NULLIF used to prevents a division-by-zero error when budget is 0.
    _ROI = """ROUND(AVG((sa.international + sa.domestic - m.prodbudget)::numeric
                        / NULLIF(m.prodbudget, 0) * 100), 2) AS average_roi"""

    # Use Logical Statements in SQL to labels movie whether its has higher or lower user score
    _SCORE_GROUP = """CASE
            WHEN s.userscore < s.metascore THEN 'User score lower'
            WHEN s.userscore > s.metascore THEN 'User score higher'
        END AS score_group"""

    # This is the JOIN querry that is used a lot in this research
    _FROM = """FROM movie m
        INNER JOIN movie_sales ms ON ms.movieid = m.movieid
        INNER JOIN sales sa       ON sa.salesid = ms.salesid
        INNER JOIN score s        ON s.movieid  = m.movieid"""

    # SETUP

    def __init__(self, **conn_kwargs):
        # Open the database connection
        # conn_kwargs are the login details (host, dbname, user, password).
        self._conn = psycopg2.connect(**conn_kwargs)

    def __enter__(self):
        # Allows "with MovieRoiAnalyzer(...) as analyzer:" syntax.
        return self

    def __exit__(self, *exc):
        # Runs automatically at the end of the "with" block,
        # so the connection is always closed, even after an error.
        self._conn.close()

    # PRIVATE HELPERS

    def _run(self, sql, params=None):
        """Execute any SQL and return the result as a DataFrame."""
        with self._conn.cursor() as cur:
            # params are passed separately so psycopg2 inserts them safely.
            cur.execute(sql, params)
            # cur.description holds the column names of the result.
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)

    def _roi_report(self, dims=(), joins="", where="", params=None):
        """Build and run one ROI query.

        dims   : extra columns to group by (e.g. genre, budget group)
        joins  : extra JOINs needed for those columns
        where  : extra filter conditions
        params : values for the %(name)s placeholders in the SQL
        """
        # Grouping columns = the extra dimensions + the score group.
        select = list(dims) + [self._SCORE_GROUP]

        # Builds "1, 2, 3": PostgreSQL lets us GROUP BY column position,
        # so the long CASE expressions do not have to be repeated.
        positions = ", ".join(str(i) for i in range(1, len(select) + 1))

        sql = f"""
            SELECT {", ".join(select)},
                   COUNT(*) AS movie_count,
                   {self._ROI}
            {self._FROM}
            {joins}
            WHERE s.userscore <> s.metascore {where}
            GROUP BY {positions}
            ORDER BY {positions}"""
        return self._run(sql, params)

    def _quartiles(self, table, column):
        """Return the 25th, 50th and 75th percentile of a column as a dict.

        This replaces the hardcoded limits (9M / 12M / 22M and 3 / 19 / 2511),
        so the groups update automatically when the data changes.
        """
        df = self._run(f"""
            SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column}) AS q1,
                   PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {column}) AS q2,
                   PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column}) AS q3
            FROM {table}
            WHERE {column} IS NOT NULL""")
        # First (only) row as a dict: {"q1": ..., "q2": ..., "q3": ...}
        return df.iloc[0].to_dict()

    @staticmethod
    def _quartile_case(column, alias):
        """Build a CASE that sorts a column into Group 1-4 by quartile.

        %(q1)s, %(q2)s, %(q3)s are placeholders filled in later with the
        values from _quartiles(). It is a staticmethod because it does not
        need the connection or any other data from the object.
        """
        # CASE stops at the first match, so "<= q2" already means
        # "above q1 and up to q2" - no need to write both conditions.
        return f"""CASE
                WHEN {column} <= %(q1)s THEN 'Group 1'
                WHEN {column} <= %(q2)s THEN 'Group 2'
                WHEN {column} <= %(q3)s THEN 'Group 3'
                ELSE 'Group 4'
            END AS {alias}"""


    # PUBLIC INTERFACE
    # One short method per research question. This is all a user of the
    # class needs to know about.


    def roi_by_score(self):
        """Query 1: average ROI for user score lower vs. higher."""
        return self._roi_report()

    def roi_by_genre(self):
        """Query 2: same comparison, split per genre."""
        return self._roi_report(
            dims=["g.genreid", "g.genre"],
            joins="""INNER JOIN movie_genre mg ON mg.movieid = m.movieid
                     INNER JOIN genre g        ON g.genreid  = mg.genreid""")

    def roi_by_budget(self):
        """Query 3: same comparison, split per production budget quartile."""
        return self._roi_report(
            dims=[self._quartile_case("m.prodbudget", "prodbudgetgroup")],
            where="AND m.prodbudget IS NOT NULL",
            params=self._quartiles("movie", "prodbudget"))

    def roi_by_theater_count(self):
        """Query 4: same comparison, split per theater count quartile."""
        return self._roi_report(
            dims=[self._quartile_case("sa.theater_count", "theatercountgroup")],
            where="AND sa.theater_count IS NOT NULL",
            params=self._quartiles("sales", "theater_count"))


# USING THE CLASS
# "with" opens the connection and closes it automatically afterwards.
with MovieRoiAnalyzer(host="localhost", dbname="Movies",
                      user="postgres", password="admin") as analyzer:
    print(analyzer.roi_by_score())
    print(analyzer.roi_by_genre())
    print(analyzer.roi_by_budget())
    print(analyzer.roi_by_theater_count())