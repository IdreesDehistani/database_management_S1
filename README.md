# Database Management — Movies Database (AUAS, Semester 1)

Data files and cleaning notebooks for the **Database Management** module. This
repo takes a raw movies/sales dataset (originally in Excel), cleans and
normalises it with Python (pandas), and produces a set of CSVs that load into a
relational database. It documents how we cleaned the data, what we kept, and how
the tables relate.

## Data model

The database is normalised into parent tables and junction (many-to-many)
tables.

**Parent tables**

| Table         | Key           | Columns                                                     | Rows   |
|---------------|---------------|-------------------------------------------------------------|--------|
| `movie`       | `movieid`     | title, studio, runtime, rating, reldate, prodbudget         | 11,364 |
| `sales`       | `salesid`     | theater_count, international, domestic                       | 7,739  |
| `awards`      | `awardsid`    | category, year                                              | 66     |
| `genre`       | `genreid`     | genre                                                       | 27     |
| `score`       | `movieid`     | userscore, metascore                                        | 9,259  |
| `cast_member` | `castid`      | castname                                                    | 24,861 |
| `director`    | `directorid`  | directorname                                                | 6,136  |

**Junction tables**

| Table            | Composite key         | Extra columns | Rows   |
|------------------|-----------------------|---------------|--------|
| `movie_sales`    | (movieid, salesid)    | —             | 7,739  |
| `movie_awards`   | (movieid, awardsid)   | rank          | 4,387  |
| `movie_genre`    | (movieid, genreid)    | —             | 27,051 |
| `movie_cast`     | (movieid, castid)     | —             | 48,284 |
| `movie_director` | (movieid, directorid) | —             | 11,350 |

## Repository layout

### Loadable tables (CSV)
- `movie.csv`, `sales_table.csv`, `awards.csv`, `genre.csv`, `score.csv`
- `cast_member_extract.csv`, `director_extract.csv`
- `movie_sales.csv`, `movie_awards.csv`, `movie_genre.csv`, `movie_cast.csv`, `movie_director.csv`

### SQL
- `sqlcommand.txt` — the `CREATE TABLE` statements for every table (parents and
  junctions). Run these first to build the empty schema.

### Analysis scripts (Python)
- `main.py` — connects to the PostgreSQL database, builds the `gap_analysis`
  view (audience score minus critic score per film), runs the H2 sub-questions,
  and exports `gap_analysis.csv` and `ml_dataset.csv`.
- `h2_stats.py` — runs the statistical tests on `gap_analysis.csv`
  (Kruskal-Wallis, Spearman correlation, OLS regression).
- `gap_analysis.csv`, `ml_dataset.csv` — the output tables produced by `main.py`.

### Cleaning notebooks (Python / pandas)
- `Data_processing.ipynb`, `Data_proposed.ipynb` — main cleaning pipeline.
- `Cast.ipynb`, `Director.ipynb` — build cast/director dimension tables (cleaned
  names, A–Z ordered IDs).
- `movie_cast.ipynb`, `movie_director.ipynb` — build the cast/director junctions.
- `Awards.ipynb`, `movie_awards.ipynb`, `Genre.ipynb`, `movie_genre.ipynb`,
  `score.ipynb`, `sales.ipynb` — build the remaining dimensions and junctions.

### Source data
- `metaClean43Brightspace.xlsx`, `sales.xlsx` — original Excel sources.
- `meta.csv`, `sales.csv`, `movies_master.csv`, `movie_lookup.csv`,
  `movie_pk.csv`, `movie_proposed.csv` — intermediate extracts from cleaning.

The large raw review files (`user_r.csv`, `expert_r.csv`, `reviews.csv` and the
`*LIWC.xlsx` sources) are git-ignored and kept locally only.

## Loading the database

1. Create the schema. From this directory, run the statements in
   `sqlcommand.txt` against your database (parents first, junctions last):

   ```bash
   psql -d your_database -f sqlcommand.txt
   ```

2. Load each CSV into its table with PostgreSQL `\copy`, for example:

   ```sql
   \copy movie       FROM 'movie.csv'       CSV HEADER
   \copy score       FROM 'score.csv'       CSV HEADER
   \copy movie_sales FROM 'movie_sales.csv' CSV HEADER
   ```

   Load the parent tables (`movie`, `sales`, `awards`, `genre`, `score`,
   `cast_member`, `director`) before the junction tables.

## Running the H2 analysis

`main.py` and `h2_stats.py` answer research question H2 (is there a gap between
audience and critic scores, and what drives it?).

```bash
pip install psycopg2 pandas python-dotenv statsmodels scipy
```

Database credentials are read from a `.env` file (git-ignored) using these
variables: `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT`.

```bash
python main.py       # builds the view, prints the sub-questions, exports the CSVs
python h2_stats.py   # runs the statistical tests on gap_analysis.csv
```
