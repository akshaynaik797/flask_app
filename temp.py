conn_data = get_db_conf(hosp=request.form['hospital_id'])

with mysql.connector.connect(**conn_data) as con:
    cur = con.cursor()
    cur.execute(query)