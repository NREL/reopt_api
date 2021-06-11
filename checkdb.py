import psycopg2
import os
from keys import *
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

env = os.getenv('APP_ENV')
dbname = os.getenv("DB_NAME")

if env == 'development':
    dbhost = dev_database_host
    dbuser = dev_user
    dbpass = dev_user_password
elif env == 'staging':
    dbhost = staging_database_host
    dbuser = staging_user
    dbpass = staging_user_password
elif env == 'production':
    dbhost = prod_database_host
    dbuser = production_user
    dbpass = production_user_password
else:
    dbname = dev_database_name
    dbhost = dev_database_host
    dbuser = dev_user
    dbpass = dev_user_password

if env != 'production':
    conn = psycopg2.connect(
        dbname="postgres",
        user=dbuser,
        password=dbpass,
        host=dbhost,
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    dbnames = []
    cur.execute("SELECT datname FROM pg_database;")
    for dbn in cur.fetchall():
        dbnames.append(dbn[0])

    if dbname not in dbnames:
        cur.execute("CREATE DATABASE {};".format(dbname))
        conn.commit()
        cur.close()
        conn.close()
        conn = psycopg2.connect(
            dbname=dbname,
            user=dbuser,
            password=dbpass,
            host=dbhost,
        )
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA reopt_api;")
        cur.execute("ALTER SCHEMA reopt_api OWNER TO {};".format(dbuser))
        conn.commit()

    cur.close()
    conn.close()
