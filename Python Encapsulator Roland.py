import psycopg2          # library to connect Python to PostgreSQL
import pandas as pd      # used to return query results as tables (DataFrames)


class GenreRoiAnalyzer:
    # PRIVATE SQL BUILDING BLOCKS
    # The pieces of query that are repeated across multiple queries.

    # One row per movie with its audience-critic gap and its ROI (in %).
    # Movies without a budget, sales figures or scores are left out.
    _FILM = """WITH film AS (
        SELECT
            m.movieid,
            s.userscore - s.metascore AS gap,
            ((sa.international + sa.domestic - m.prodbudget)::numeric
                / m.prodbudget) * 100 AS roi
        FROM movie m
        INNER JOIN movie_sales ms ON ms.movieid = m.movieid
        INNER JOIN sales sa       ON sa.salesid = ms.salesid
        INNER JOIN score s        ON s.movieid  = m.movieid
        WHERE m.prodbudget > 0
          AND sa.international IS NOT NULL
          AND sa.domestic IS NOT NULL
          AND s.userscore IS NOT NULL
          AND s.metascore IS NOT NULL
    )"""

    # Adds the genre name to every movie.
    _GENRE_JOIN = """FROM film f
        INNER JOIN movie_genre mg ON mg.movieid = f.movieid
        INNER JOIN genre g        ON g.genreid  = mg.genreid"""

    # Compares movies with a positive gap (audience scored higher) against
    # movies with a negative gap. Medians are included because ROI has
    # extreme outliers that distort the average.
    _COMPARISON = """COUNT(*) FILTER (WHERE f.gap > 0) AS n_positive,
            COUNT(*) FILTER (WHERE f.gap < 0) AS n_negative,
            ROUND(AVG(f.roi) FILTER (WHERE f.gap > 0), 2) AS avg_roi_positive,
            ROUND(AVG(f.roi) FILTER (WHERE f.gap < 0), 2) AS avg_roi_negative,
            ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.roi)
                   FILTER (WHERE f.gap > 0))::numeric, 2) AS median_roi_positive,
            ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.roi)
                   FILTER (WHERE f.gap < 0))::numeric, 2) AS median_roi_negative,
            ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.roi)
                   FILTER (WHERE f.gap > 0)
                 - PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.roi)
                   FILTER (WHERE f.gap < 0))::numeric, 2) AS median_benefit"""

    # SETUP

    def __init__(self, **conn_kwargs):
        # Open the database connection (host, dbname, user, password).
        self._conn = psycopg2.connect(**conn_kwargs)

    def __enter__(self):
        # Allows "with GenreRoiAnalyzer(...) as analyzer:" syntax.
        return self

    def __exit__(self, *exc):
        # Closes the connection at the end of the "with" block.
        self._conn.close()

    # PRIVATE HELPERS

    def _run(self, sql, params=None):
        """Execute any SQL and return the result as a DataFrame."""
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)

    # PUBLIC INTERFACE

    def roi_per_genre(self, min_films=10):
        """SRQ3: ROI of positive-gap vs negative-gap movies, per genre."""
        # Only genres with at least min_films movies in each group.
        sql = f"""{self._FILM}
        SELECT
            g.genre,
            {self._COMPARISON}
        {self._GENRE_JOIN}
        GROUP BY g.genre
        HAVING COUNT(*) FILTER (WHERE f.gap > 0) >= %(min_films)s
           AND COUNT(*) FILTER (WHERE f.gap < 0) >= %(min_films)s
        ORDER BY median_benefit DESC;"""
        return self._run(sql, {"min_films": min_films})

    def genre_driven_vs_critical(self):
        """H3: Horror and Action (genre-driven) compared with Drama."""
        sql = f"""{self._FILM}
        SELECT
            CASE WHEN g.genre IN ('Horror', 'Action') THEN 'Genre-driven'
                 WHEN g.genre = 'Drama'               THEN 'Critically oriented'
            END AS category,
            {self._COMPARISON}
        {self._GENRE_JOIN}
        WHERE g.genre IN ('Horror', 'Action', 'Drama')
        GROUP BY 1;"""
        return self._run(sql)


# USING THE CLASS
if __name__ == "__main__":
    # Show all columns when printing.
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    with GenreRoiAnalyzer(host="localhost", dbname="Movies", user="postgres",
                          password="1604", port="5432") as analyzer:
        print(analyzer.roi_per_genre())
        print(analyzer.genre_driven_vs_critical())