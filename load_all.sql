-- ============================================================
-- Rebuilds the whole Movies database: all 8 tables 
-- ============================================================

-- Drop everything first (junctions before parents) so this is re-runnable
DROP TABLE IF EXISTS movie_sales, movie_awards, movie_genre, sales, awards, genre, score, movie CASCADE;

-- ---------- PARENT TABLES ----------
CREATE TABLE movie (
    movieid    INTEGER PRIMARY KEY,
    title      VARCHAR(255),
    studio     VARCHAR(255),
    runtime    INTEGER,
    rating     VARCHAR(100),
    reldate    DATE,
    prodbudget BIGINT
);

CREATE TABLE sales (
    salesid       INTEGER PRIMARY KEY,
    theater_count INTEGER,
    international  BIGINT,
    domestic      BIGINT
);

CREATE TABLE awards (
    awardsid INTEGER PRIMARY KEY,
    category VARCHAR(255),
    year     INTEGER
);

CREATE TABLE genre (
    genreid INTEGER PRIMARY KEY,
    genre   VARCHAR(100)
);

CREATE TABLE score (
    movieid   INTEGER PRIMARY KEY,
    userscore INTEGER,
    metascore INTEGER,
    FOREIGN KEY (movieid) REFERENCES movie(movieid)
);

-- ---------- JUNCTION TABLES ----------
CREATE TABLE movie_sales (
    movieid INTEGER,
    salesid INTEGER,
    PRIMARY KEY (movieid, salesid),
    FOREIGN KEY (movieid) REFERENCES movie(movieid),
    FOREIGN KEY (salesid) REFERENCES sales(salesid)
);

CREATE TABLE movie_awards (
    movieid  INTEGER,
    awardsid INTEGER,
    rank     INTEGER,
    PRIMARY KEY (movieid, awardsid),
    FOREIGN KEY (movieid)  REFERENCES movie(movieid),
    FOREIGN KEY (awardsid) REFERENCES awards(awardsid)
);

CREATE TABLE movie_genre (
    movieid INTEGER,
    genreid INTEGER,
    PRIMARY KEY (movieid, genreid),
    FOREIGN KEY (movieid) REFERENCES movie(movieid),
    FOREIGN KEY (genreid) REFERENCES genre(genreid)
);

-- ---------- LOAD DATA (parents first, junctions last) ----------
\copy movie        FROM 'movie.csv'         WITH (FORMAT csv, HEADER true);
\copy sales        FROM 'sales_table.csv'   WITH (FORMAT csv, HEADER true);
\copy awards       FROM 'awards.csv'        WITH (FORMAT csv, HEADER true);
\copy genre        FROM 'genre.csv'         WITH (FORMAT csv, HEADER true);
\copy score        FROM 'score.csv'         WITH (FORMAT csv, HEADER true);
\copy movie_sales  FROM 'movie_sales.csv'   WITH (FORMAT csv, HEADER true);
\copy movie_awards FROM 'movie_awards.csv'  WITH (FORMAT csv, HEADER true);
\copy movie_genre  FROM 'movie_genre.csv'   WITH (FORMAT csv, HEADER true);

-- ---------- VERIFY ----------
SELECT 'movie' AS tbl, count(*) FROM movie
UNION ALL SELECT 'sales', count(*) FROM sales
UNION ALL SELECT 'awards', count(*) FROM awards
UNION ALL SELECT 'genre', count(*) FROM genre
UNION ALL SELECT 'score', count(*) FROM score
UNION ALL SELECT 'movie_sales', count(*) FROM movie_sales
UNION ALL SELECT 'movie_awards', count(*) FROM movie_awards
UNION ALL SELECT 'movie_genre', count(*) FROM movie_genre;
