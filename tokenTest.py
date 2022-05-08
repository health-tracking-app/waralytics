
from sqlalchemy import create_engine
from datetime import datetime
import os

# connect to PostgresQL DB

conn_string = os.environ['POSTGRES_CONN_STRING']

engine = create_engine(conn_string)

engine.execute("insert into public.log_test(date_) values ('" + str(datetime.now()) + "')")


