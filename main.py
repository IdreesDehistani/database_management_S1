#before importing psycopg2, make sure to install it using pip first, using this command: pip install psycopg2
import psycopg2

conn = psycopg2.connect(host="localhost",
    database="your_database_name",
    user="your_username",
    password="your_password"
    port="1111"
)   

# Create a cursor object to excute SQL queries
cur = conn.cursor()

# Database Queries 



# then commit the changes to the database
conn.commit()

#then close the cursor and connection
cur.close()
conn.close()