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
- `load_all.sql` — re-runnable script that drops, recreates, and loads the core
  tables using PostgreSQL `\copy`. Run with `psql` from this directory.
- `sqlcommand.txt` — working `CREATE TABLE` statements (schema scratchpad).

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

## Loading the database

`load_all.sql` covers the core tables. From this directory:

```bash
psql -d your_database -f load_all.sql
```

It drops existing tables, recreates the schema, loads each CSV (parents first,
junctions last), and prints a row count per table to verify the load. The cast
and director tables (`cast_member`, `director`, `movie_cast`, `movie_director`)
are defined in `sqlcommand.txt` and loaded from their CSVs.
