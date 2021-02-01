import mysql.connector

conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                  'user': "admin",
                  'password': "Welcome1!",
                  'database': 'portals'}
def get_db_conf(**kwargs):
    fields = ('host', 'database', 'port', 'user', 'password')
    if 'env' not in kwargs:
        kwargs['env'] = 'live'
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        q = 'SELECT host, dbName, port, userName, password FROM dbConfiguration where hospitalID=%s and environment=%s limit 1;'
        cur.execute(q, (kwargs['hosp'], kwargs['env']))
        result = cur.fetchone()
        if result is not None:
            conf_data = dict()
            for key, value in zip(fields, result):
                conf_data[key] = value
            return conf_data
if __name__ == '__main__':
    a = get_db_conf(hosp='8900080427990')
    with mysql.connector.connect(**a) as con:
        cur = con.cursor()
        pass