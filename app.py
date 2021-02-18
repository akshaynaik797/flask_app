import base64
import os
from datetime import datetime, timedelta

import mysql.connector
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from dbconf import get_db_conf
from gmailMailSender import GMAIL_SENDER
from make_log import log_exceptions, log_data
from otpgenerator import OtpGenerator
from outlookmailSender import OUTLOOK_SENDER

app = Flask(__name__)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

# app.config['UPLOAD_FOLDER']= "E:/vnu project/static"
app.config['UPLOAD_FOLDER'] = "/var/www/FlaskApp/FlaskApp/assest/mquery"
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# subprocess.Popen(['sh', '/home/akshay/sample.sh'])
# app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

# app.config['UPLOAD_FOLDER']= "static"

# app.config['MYSQL_HOST'] = "localhost"
# app.config['MYSQL_USER'] = "root"
# app.config['MYSQL_PASSWORD'] = "root123"
# app.config['MYSQL_DB'] = "PatientRecord"
# mysql= MySQL ( app )

# dbConfig = {}
# with open ( dirname ( abspath ( __file__ ) ) + "/databaseconfig.json" ) as json_data_file :
#     data = json.load ( json_data_file )
#     for keys in data.keys ( ) :
#         values = data[keys]
#         dbConfig[keys] = values

# app.config['MYSQL_HOST'] = dbConfig["Config"]['MYSQL_HOST']
# app.config['MYSQL_USER'] = dbConfig["Config"]['MYSQL_USER']
# app.config['MYSQL_PASSWORD'] = dbConfig["Config"]['MYSQL_PASSWORD']
# app.config['MYSQL_DB'] = dbConfig["Config"]['MYSQL_DB']
# mysql= MySQL ( app )


# app.config['MYSQL_DATABASE_HOST'] = dbConfig["Config"]['MYSQL_HOST']
# app.config['MYSQL_DATABASE_USER'] = dbConfig["Config"]['MYSQL_USER']
# app.config['MYSQL_DATABASE_PASSWORD'] = dbConfig["Config"]['MYSQL_PASSWORD']
# app.config['MYSQL_DATABASE_DB'] = dbConfig["Config"]['MYSQL_DB']
#
# mysql= MySQL ()
# mysql.init_app(app)

apiList = ['/api/OTPLogin', '/api/UserLogin', '/api/StatusTrack', '/api/ActiveCases',
           '/api/ActiveClarification', '/api/PatientSearch', '/api/incident', '/api/tsignature', '/api/trigger_alert'
                                                                                                 '/api/tSignatureUse',
           '/api/tQueryReply', '/api/EnhanceFinal', '/api/ClarificationReply', '/api/pQueryReply',
           '/api/pSignature', '/api/IncidentCreate', '/api/UserProfile', '/api/tSignatureCreate', '/api/get_from_query',
           '/api/get_from_query1', '/api/get_from_name', '/api/get_portal_submitted', '/api/update_ssdoc']


@app.route("/getstatustrack", methods=["POST"])
def getstatustrack():
    records = []
    fields = ('srno', 'PatientID_TreatmentID', 'Type', 'Type_Ref', 'Type_ID', 'status', 'HospitalID', 'time_difference',
              'responsible', 'comment', 'cdate', 'person_name', 'comment_date')
    data = request.form.to_dict()
    conn_data = get_db_conf(hosp=data['hospitalID'])
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        q = "select * from status_track where HospitalID=%s and Type_Ref=%s"
        cur.execute(q, (data['hospitalID'], data['refNo']))
        result_set = cur.fetchall()
        for result in result_set:
            temp = {}
            for key, value in zip(fields, result):
                temp[key] = value
            temp['docType'], temp['docPath'] = "", ""
            if temp['Type'] == 'PreAuth':
                q = "select Doctype, file_path from preauth_document where statustrackid=%s and flagId=%s limit 1"
                cur.execute(q, (temp['srno'], temp['Type_ID']))
                result = cur.fetchone()
                if result is not None:
                    temp['docType'], temp['docPath'] = result[0], result[1]
            if temp['Type'] == 'Claim':
                q = "select Doctype, file_path from claim_document where statustrackid=%s and flagId=%s limit 1"
                cur.execute(q, (temp['srno'], temp['Type_ID']))
                result = cur.fetchone()
                if result is not None:
                    temp['docType'], temp['docPath'] = result[0], result[1]
            records.append(temp)
    return jsonify(records)


@app.route("/getsmslog", methods=["POST"])
def getsmslog():
    result, records = [], []
    fields = (
    'snno', 'mobileno', 'type', 'notification_text', 'sms', 'push', 'timestamp', 'messageid', 'error', 'device_token',
    'ref_no')
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    data = request.form.to_dict()
    q = "select * from alerts_log where ref_no=%s and sms='X'"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (data['refNo'],))
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/getreminders", methods=["POST"])
def getreminders():
    records, result = [], []
    fields = (
    'srno', 'PatientID_TreatmentID', 'InsurerID', 'HospitalID', 'insurermail', 'subjectline', 'mail_template', 'status',
    'strcnt', 'cdate')
    data = request.form.to_dict()
    conn_data = get_db_conf(hosp=request.form['hospitalID'])
    q = "select * from reminder_log where HospitalID=%s and PatientID_TreatmentID=%s"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (data['hospitalID'], data['refNo'],))
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/getmailslog", methods=["POST"])
def getmailslog():
    records, result = [], []
    fields = ('srno', 'PatientID_TreatmentID', 'status', 'from_mail', 'to_mail', 'subjectline', 'message', 'sentornot',
              'saveornot', 'pagerror', 'requestime', 'responsetime', 'cdate')
    data = request.form.to_dict()
    conn_data = get_db_conf(hosp=request.form['hospitalID'])
    q = "select * from mail_log where PatientID_TreatmentID=%s"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (data['refNo'],))
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/gettransactionlog", methods=["POST"])
def gettransactionlog():
    records, result = [], []
    fields = (
    'srno', 'transactionID', 'PatientID_TreatmentID', 'patientName', 'insurerID', 'memberID', 'refno', 'status',
    'cdate', 'Type', 'formstatus', 'userName')
    data = request.form.to_dict()
    conn_data = get_db_conf(hosp=request.form['hospitalID'])
    q = "select * from transaction_log where refno=%s"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (data['refNo'],))
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/getinsurer", methods=["POST"])
def getinsurer():
    records, result = [], []
    fields = ('srno', 'InsurerId', 'HospitalID', 'InsurerMail', 'contactNo', 'userNm', 'password', 'link', 'submitvia',
              'HospitalMail', 'HospitalPass', 'IncomingHost', 'IncomingPort', 'OutgoingHost', 'OutgoingPort',
              'Gapppass', 'Type')
    data = request.form.to_dict()
    conn_data = get_db_conf(hosp=request.form['hospitalID'])
    q = "select * from mail_configration where HospitalID=%s and InsurerId=%s"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (data['hospitalID'], data['InsurerID']))
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/insertmailslog", methods=["POST"])
def insertmailslog():
    response = {
        "status": "success",
        "message": "Data Inserted Successfully"
    }
    data = request.form.to_dict()
    conn_data = get_db_conf(hosp=request.form['hospitalID'])
    q = "insert into mail_log (PatientID_TreatmentID, status, from_mail, to_mail, subjectline, message, sentornot, saveornot, pagerror, requestime, responsetime, cdate) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (
        data['refNo'], data['status'], data['from_mail'], data['to_mail'], data['subjectline'], data['message'],
        data['sentornot'], data['saveornot'], data['pagerror'], data['requestime'], data['responsetime'],
        datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
        con.commit()
        return response


@app.route("/insertuploaddocdetails", methods=["POST"])
def insertuploaddocdetails():
    response = {
        "status": "success",
        "message": "Data Inserted Successfully"
    }
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    data = request.form.to_dict()
    q = "insert into documentDetails (hospitalID, refNo, docName, docSize, status, approveFLag, docCount, `type`) values (%s, %s, %s, %s, %s, %s, %s, %s)"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, (
        data['hospitalID'], data['refNo'], data['docName'], data['docSize'], data['status'], data['approveFlag'],
        data['docCount'], data['type']))
        con.commit()
        return response


@app.route("/getuploaddocdetails", methods=["POST"])
def getuploaddocdetails():
    result, fields = [], (
    "srno", "hospitalID", "refNo", "docName", "docSize", "docCount", "status", "approveFlag", "cdate", "type")
    records = []
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    data = request.form.to_dict()
    q = "select `srno`, `hospitalID`, `refNo`, `docName`, `docSize`, `docCount`, `status`, `approveFlag`, `cdate`, " \
        "`type` from documentDetails where srno is not null"
    params = []
    data_fields = ("hospitalID", "refNo", "status", "approveFlag")
    for i in data_fields:
        if i in data:
            q = q + f' and {i}=%s'
            params = params + [data[i]]
    params = tuple(params)
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, params)
        result = cur.fetchall()
        for i in result:
            temp = {}
            for key, value in zip(fields, i):
                temp[key] = value
            records.append(temp)
    return jsonify(records)


@app.route("/getstatustags", methods=["POST"])
def getstatustags():
    result, fields = [], (
    "srno", "hospitalID", "refNo", "docName", "docSize", "docCount", "status", "approveFlag", "cdate")
    records = []
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    q = "select * from status_tag"
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q)
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/getstatuslist", methods=["POST"])
def getstatuslist():
    result, fields = [], ("srno","scode","name","descr","cdate")
    records = []
    data = request.form.to_dict()
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    q = "SELECT * FROM form_status where srno is not null "
    params = []

    if 'scode' in data:
        q = q + 'and scode=%s'
        params = params + [data['hospitalid']]
    if 'name' in data:
        q = q + ' and name=%s'
        params = params + [data['name']]

    params = tuple(params)
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, params)
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)

@app.route("/getinsurerlist", methods=["POST"])
def getinsurerlist():
    result, fields = [], ("srno","type","name","TPAInsurerID","TollfreeNo","FaxNo","Address","IRDANo","InsLogo",
                          "filesize","fileExtensions","otherdoc_limit","Cumulative_flag")
    records = []
    data = request.form.to_dict()
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    q = "SELECT * FROM insurer_tpa_master where srno is not null "
    params = []

    if 'TPAInsurerID' in data:
        q = q + 'and TPAInsurerID=%s'
        params = params + [data['TPAInsurerID']]

    params = tuple(params)
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, params)
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)

@app.route("/gethospitalslist", methods=["POST"])
def gethospitalslist():
    result, fields = [], ("srno","type","name","TPAInsurerID","TollfreeNo","FaxNo","Address","IRDANo","InsLogo",
                          "filesize","fileExtensions","otherdoc_limit","Cumulative_flag")
    records = []
    data = request.form.to_dict()
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    q = "SELECT * FROM hospitallist where status = 1 "
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q)
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)

@app.route("/getdocpath", methods=["POST"])
def getdocpath():
    result, fields = [],  ("srno", "hospitalID", "process", "docPath")
    records = []
    data = request.form.to_dict()
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    q = "SELECT * FROM docPath where srno is not null "
    params = []

    if 'hospitalID' in data:
        q = q + 'and hospitalID=%s'
        params = params + [data['hospitalID']]

    if 'process' in data:
        q = q + 'and process=%s'
        params = params + [data['process']]

    params = tuple(params)
    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, params)
        result = cur.fetchall()
    for i in result:
        temp = {}
        for key, value in zip(fields, i):
            temp[key] = value
        records.append(temp)
    return jsonify(records)


@app.route("/deletehospitaltlog", methods=["POST"])
def deletehospitaltlog():
    fields = ('PatientID_TreatmentID', 'Type_Ref', 'Type', 'status', 'HospitalID', 'cdate', 'person_name',
                'smsTrigger', 'pushTrigger', 'lock', 'error',
                'errorDescription', 'insurerID', 'fStatus', 'fLock', 'transactionID')
    data = request.form.to_dict()
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    if 'refNo' in data:
        q = "select * from hospitalTLog where Type_Ref=%s"
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(q, (data['refNo'],))
            result = cur.fetchall()
            for i in result:
                i = tuple(list(i)[1:])
                q = "insert into hospitalTLogDel (`PatientID_TreatmentID`,`transactionID`,`Type_Ref`,`Type`,`status`,`HospitalID`,`cdate`,`person_name`,`smsTrigger`,`pushTrigger`,`insurerID`,`fStatus`,`fLock`,`lock`,`error`,`errorDescription`) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                cur.execute(q, i)
            q = "delete from hospitalTLog where Type_Ref=%s"
            cur.execute(q, (data['refNo'],))
            con.commit()
        return jsonify('done')
    else:
        return jsonify('pass refNo')

@app.route('/get_log', methods=["POST"])
def get_log():
    field_list = ('id', 'time', 'transactionid', 'referenceno', 'tab_id',
                  'insurer', 'process', 'step', 'status', 'message', 'url')
    records = []
    params = []
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    data = request.form.to_dict()
    for i in ('transactionid', 'referenceno', 'process'):
        if i not in data:
            return jsonify(f"pass {i} parameter")
    if 'fromdate' in data and 'todate' in data:
        for i in ('transactionid', 'referenceno', 'process', 'fromdate', 'todate'):
            params.append(data[i])
        q = "select * from logs where transactionid=%s and referenceno=%s and process=%s and time BETWEEN %s AND %s;"
    else:
        for i in ('transactionid', 'referenceno', 'process'):
            params.append(data[i])
        q = "select * from logs where transactionid=%s and referenceno=%s and process=%s;"

    with mysql.connector.connect(**conn_data) as con:
        cur = con.cursor()
        cur.execute(q, params)
        r = cur.fetchall()
        for i in r:
            datadict = dict()
            for j, k in zip(field_list, i):
                datadict[j] = k
            records.append(datadict)
    return jsonify(records)


@app.route('/api/get_mssno_data', methods=['POST'])
def get_mssno_data():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        fields = ('insid', 'CurrentStatus', 'refno', 'preauthNo')
        query = "SELECT insid, CurrentStatus, refno, preauthNo FROM preauth where insname=%s and `show`='1' and CurrentStatus like %s"
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query, (request.form['insname'], '%' + 'In Progress' + '%'))
            result = cur.fetchall()
        records = []
        for i in result:
            data = {}
            for j, k in zip(fields, i):
                data[j] = k
            records.append(data)
        return jsonify(records)
    except Exception as e:
        print(e)
        return str(e)


# @app.route('/api/trigger_alert', methods=['POST'])
# def trigger_alert():
#     try:
#         log_data(refno=request.form['ref_no'], hid=request.form['hospital_id'])
#         a = triggerAlert(request.form['ref_no'], request.form['hospital_id'])
#         return str(a)
#     except Exception as e:
#         log_exceptions()
#         return "fail " + str(e)


@app.route('/api/get_from_query1', methods=['POST'])
def get_from_query1():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        tempdict = {}
        query = """SELECT 
            tl.transactionID,
            tl.PatientID_TreatmentID,
            tl.patientName,
            imd.name,
            tl.memberID,
            tl.refno,
            tl.Type,
            tl.formstatus,
            tl.status,
            ts.text AS statusName,
            tl.userName,
            cdate
        FROM
            transaction_log AS tl
                LEFT JOIN
            transaction_status ts ON tl.status = ts.id
                LEFT JOIN
            insurer_tpa_master imd ON tl.insurerID = imd.TPAInsurerID
        WHERE
            tl.status = 'TS05'
                AND STR_TO_DATE(tl.cdate, '%d/%m/%Y') >= STR_TO_DATE('""" + request.form['start_date'] + """', '%d/%m/%Y')
                AND STR_TO_DATE(tl.cdate, '%d/%m/%Y') <= STR_TO_DATE('""" + request.form[
            'end_date'] + """', '%d/%m/%Y')"""
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        for i, j in enumerate(data):
            tempdict[i] = {'transactionID': j[0], 'PatientID_TreatmentID': j[1], 'patientName': j[2], 'name': j[3],
                           'memberID': j[4], 'refno': j[5], 'Type': j[6], 'formstatus': j[7], 'status': j[8],
                           'statusName': j[9], 'userName': j[10], 'cdate': j[11]}
        return jsonify(tempdict)

    except Exception as e:
        print(e)
        return str(e)


@app.route('/api/update_ssdoc', methods=['POST'])
def update_ssdoc():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        query = """update ssDoc 
            set flagVerify = ' """ + request.form['isverify'] + """ '
        where
            srno = ' """ + request.form['srno'] + """ ' """
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()
            return 'done'
    except Exception as e:
        print(e)
        return str(e)


@app.route('/api/get_portal_submitted', methods=['POST'])
def get_from_portal_submitted():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        tempdict = {}
        query = """SELECT 
            pa.PatientID_TreatmentID AS pID,
            pa.refno AS referenceNo,
            pa.preauthNo AS alNo,
            pa.MemberId AS memberID,
            pa.HospitalID AS hospitalID,
            pa.p_sname AS ptName,
            ss.stcdate AS entryDate,
            pa.admission_date AS DOA,
            pa.dischargedate AS DOD,
            pa.CurrentStatus AS currentStatus,
            imd.name AS insurerTpaName,
            pa.insname AS insurerTPA,
            pa.flag AS submitType,
            ss.file_path AS filePath,
            ss.date_time AS fileDateTime,
            ss.flagVerify AS isVerify,
	    ss.srno AS srno
        FROM
            preauth pa
                LEFT JOIN
            insurer_tpa_master imd ON pa.insname = imd.TPAInsurerID
                LEFT JOIN
            ssDoc ss ON pa.PatientID_TreatmentID = ss.PatientID_TreatmentID
                AND pa.refno = ss.refno
                 WHERE
            pa.CurrentStatus like '%Sent To TPA/ Insurer%'
                AND pa.show = 1
                AND pa.flag IN ('Portal_Submit')
		AND ( ss.flagVerify != '1' or ss.flagVerify is null )
                AND STR_TO_DATE(pa.up_date, '%d/%m/%y') >= STR_TO_DATE('""" + request.form[
            'date'] + """', '%d/%m/%y')"""
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        for i, j in enumerate(data):
            tempdict[i] = {'pID': j[0], 'referenceNo': j[1], 'alNo': j[2], 'memberID': j[3], 'hospitalID': j[4],
                           'ptName': j[5], 'entryDate': j[6], 'DOA': j[7], 'DOD': j[8], 'currentStatus': j[9],
                           'insurerTpaName': j[10], 'insurerTPA': j[11], 'submitType': j[12], 'filePath': j[13],
                           'fileDateTime': j[14], 'isVerify': j[15], 'srno': j[16]}
        return jsonify(tempdict)
    except Exception as e:
        return str(e)


@app.route('/api/get_from_query')
def get_from_query():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        query = """SELECT
            claimNo AS ReferenceNo,
            preauthNo AS PreAuthID,
            Patient_Name AS PatientName,
            Date_Of_Admission AS DateOfAdmision,
            Date_Of_Discharge AS DateOfDischarge,
            InsurerID AS InsurerTPAID,
            status AS Status
        FROM
            claim
        WHERE
            (status LIKE '%Sent To TPA/ Insurer%'
                OR status LIKE '%In Progress%')
                AND STR_TO_DATE(Date_of_Admission, '%d/%m/%Y') >= now() - interval 2 day
        UNION ALL SELECT
            refno AS ReferenceNo,
            preauthNo AS PreAuthID,
            p_sname AS PatientName,
            admission_date AS DateOfAdmision,
            dischargedate AS DateOfDischarge,
            insname AS InsurerTPAID,
            status AS Status
        FROM
            preauth
        WHERE
            (status LIKE '%Sent To TPA/ Insurer%'
                OR status LIKE '%In Progress%')
                AND STR_TO_DATE(admission_date, '%d/%m/%Y') >= now() - interval 2 day"""
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        return jsonify(data)
    except Exception as e:
        return jsonify(e)


@app.route('/api/get_from_name1', methods=['POST'])
def get_from_name1():
    try:
        records = []
        data = request.form.to_dict()
        conn_data = get_db_conf(hosp=data['hospital_id'])
        preauth_field_list = (
        "preauthNo", "MemberId", "p_sname", "admission_date", "dischargedate", "flag", "CurrentStatus", "cdate",
        "up_date", "hospital_name", "p_policy")
        q = "select preauthNo, MemberId, p_sname, admission_date, dischargedate, flag, " \
            "CurrentStatus, cdate, up_date, hospital_name, p_policy from preauth " \
            "where p_sname LIKE %s and insname=%s AND STR_TO_DATE(up_date, '%d/%m/%Y') >= now() - interval 5 day"
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(q, ('%' + data['name'] + '%', data['insid']))
            result = cur.fetchall()
            for row in result:
                temp = {}
                for k, v in zip(preauth_field_list, row):
                    temp[k] = v
                records.append(temp)
        return jsonify(records)
    except Exception as e:
        return str(e)


@app.route('/api/get_from_name', methods=['POST'])
def get_from_name():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        # l_date = CURDATE() - 15
        if request.form['insid'] != "I14":
            query = """SELECT
                    refno AS ReferenceNo,
                    preauthNo AS PreAuthID,
                    p_sname AS PatientName,
                    admission_date AS DateOfAdmision,
                    dischargedate AS DateOfDischarge,
                    insname AS InsurerTPAID,
                    CurrentStatus AS Status,
                    p_policy as PolicyNo,
                    MemberID,
                    `show`
                FROM
                    preauth
                WHERE
                    p_sname LIKE '%""" + request.form['name'] + """%'
                        AND insname  = '""" + request.form['insid'] + """'
                        AND STR_TO_DATE(up_date, '%d/%m/%Y') >= now() - interval 5 day"""
        else:
            query = """SELECT
                    refno AS ReferenceNo,
                    preauthNo AS PreAuthID,
                    p_sname AS PatientName,
                    admission_date AS DateOfAdmision,
                    dischargedate AS DateOfDischarge,
                    insname AS InsurerTPAID,
                    CurrentStatus AS Status,
                    p_policy as PolicyNo,
                    MemberID,
                    `show`
                FROM
                    preauth
                WHERE
                    p_sname LIKE '%""" + request.form['name'] + """%'
                        AND (insname  = 'I14' OR insname  = 'I04')
                        AND STR_TO_DATE(up_date, '%d/%m/%Y') >= now() - interval 5 day"""

        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            tempdict = {}
            data = cur.fetchall()
        for i, j in enumerate(data):
            tempdict[i] = {'ref_no': j[0], 'preauthno': j[1], 'patient_name': j[2], 'admis_date': j[3],
                           'disc_date': j[4], 'insname': j[5], 'currentstatus': j[6], 'PolicyNo': j[7],
                           'MemberId': j[8], 'show': j[9]}
        return jsonify({'data': tempdict})
    except Exception as e:
        return str(e)


@app.route('/api/get_from_transaction_log', methods=['POST'])
def get_from_transaction_log():
    try:
        conn_data = get_db_conf(hosp=request.form['hospital_id'])
        tempdict = {}
        status_list = request.form['status'].split(',')
        for status in status_list:
            query = """SELECT
                        tl.PatientID_TreatmentID,
                        tl.Type,
                        tl.formstatus,
                        tl.status,
                        ts.text AS statusName,
                        cdate
                    FROM
                        transaction_log AS tl
                        LEFT JOIN
                        transaction_status ts ON tl.status = ts.id
                    WHERE
                        tl.status='""" + str(status) + """'
                        AND STR_TO_DATE(cdate, '%d/%m/%Y') >= STR_TO_DATE('""" + request.form['start_date'] + """', '%d/%m/%Y')
                        AND STR_TO_DATE(cdate, '%d/%m/%Y') <= STR_TO_DATE('""" + request.form[
                'end_date'] + """', '%d/%m/%Y')"""
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            for i, j in enumerate(data):
                tempdict[i] = {'ptid': j[0], 'process': j[1], 'patient_status': j[2], 'status': j[3],
                               'status_desc': j[4], 'cdate': j[5], 'ref_no': ""}
        return jsonify({'data': tempdict})
    except Exception as e:
        return str(e) + str(status_list)


@app.route('/', methods=['GET'])
def listMyApi():
    if request.method == 'GET':
        finalResponse = {}
        finalResponse['api_list'] = apiList
        return jsonify(finalResponse)


@app.route('/api/OTPLogin', methods=['POST'])
def otplogin():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    otp = None
    flag = False
    mobile_no = ''
    finalResponse = {}
    con = None
    if request.method != 'POST':
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mobile_no = request.form['mobileNo']

    if mobile_no == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'mobile number field is empty'
            }
        )
    try:
        query = """select * from hospital_employee where he_mobile='%s'""" % mobile_no
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
        data = cur.fetchone()
        if data:
            otpgen = OtpGenerator()
            otp = otpgen.generateOTP(4)
            otp = otpgen.sendOTP(otp, mobile_no)
            query = """UPDATE hospital_employee SET he_otp =%s, he_is_otp_verify=%s where he_mobile='%s'""" % (
            int(otp), 0, mobile_no)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()
            flag = True
            msg = "Otp has been sent to your mobile no=" + mobile_no
            finalResponse['status'] = 'success'
            finalResponse['message'] = msg
        else:
            otpgen = OtpGenerator()
            otp = otpgen.generateOTP(4)
            otp = otpgen.sendOTP(otp, mobile_no)
            query = """select * from patient_master where mobile='%s'""" % mobile_no
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data is None:
                query = """insert into patient_master(mobile,status,otp,otp_verify) values ('%s','%s',%s,%s)""" % (
                mobile_no, 0, otp, 0)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    con.commit()
            else:
                query = """UPDATE patient_master SET otp =%s, otp_verify=%s where mobile='%s'""" % (
                int(otp), 0, mobile_no)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    con.commit()
            msg = "Otp has been sent to your mobile no=" + mobile_no
            finalResponse['status'] = 'success'
            finalResponse['message'] = msg
    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/UserLogin', methods=['GET', 'POST'])
def userLogin():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    mobile_no = ''
    otp = ''
    if request.method != 'POST':
        return jsonify(
            {
                'APIstatus': 'failed',
                'reason': 'inavlid request method.Only Post method Allowed',
                'mobileNo': '',
                'userName': '',
                'timeStamp': str(datetime.now()),
                'userType': '',
                'status': ''
            }
        )
    if request.form.get('mobileNo') != None:
        mobile_no = request.form['mobileNo']
    if request.form.get('otp') != None:
        otp = request.form['otp']
    if mobile_no == '' or otp == '':
        return jsonify(
            {
                'APIstatus': 'failed',
                'reason': 'inavlid parameter',
                'mobileNo': '',
                'userName': '',
                'timeStamp': str(datetime.now()),
                'userType': '',
                'status': ''
            }
        )

    flag = 'T'
    try:
        query = """select he_name, he_mobile, status, he_hospital_id from hospital_employee where he_mobile=%s and he_otp=%s""" % (
        mobile_no, int(otp))
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            finalResponse = {
                'APIstatus': 'success',
                'mobileNo': data[1],
                'userName': data[0],
                'hospital_id': data[3],
                'timeStamp': str(datetime.now()),
                'userType': flag,
                'status': data[2]
            }
            print("Data is present in hospital_employee")
            query = """UPDATE hospital_employee SET he_is_otp_verify=%s where he_mobile='%s' and he_otp=%s""" % (
            1, mobile_no, otp)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()

        else:
            flag = 'P'
            print('No data in hospital_employee table.Looking into patient_master table')
            query = """select mobile, pname, status from patient_master  where mobile=%s and otp=%s""" % (
            mobile_no, int(otp))
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data:
                finalResponse = {
                    'APIstatus': 'success',
                    'mobileNo': data[0],
                    'userName': data[1],
                    'timeStamp': str(datetime.now()),
                    'userType': flag,
                    'status': data[2]
                }
            else:
                finalResponse = {
                    'APIstatus': 'failed',
                    'mobileNo': '',
                    'userName': '',
                    'timeStamp': str(datetime.now()),
                    'userType': flag,
                    'status': ''
                }
    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/ActiveCases', methods=['POST'])
def activeCases():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    mobileNo = ''
    finalResponse = {}
    mList = []
    mylist = []
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form['mobileNo'] != '':
        mobileNo = request.form['mobileNo']

    if mobileNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        query = """select he_hospital_id from hospital_employee where he_mobile=%s"""
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query, (mobileNo,))
            data = cur.fetchone()
        if data:
            today = datetime.today().date()
            today = str(today.strftime("%d/%m/%Y"))
            print(today)

            yesterday = datetime.today().date() - timedelta(days=1)
            yesterday = str(yesterday.strftime("%d/%m/%Y"))
            print(yesterday)

            dateformat = '%d/%m/%Y'
            hospitalId = data[0]
            query1 = """select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
                    LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
                    pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID WHERE\
                    STR_TO_DATE(pa.dischargedate, '%s')>= STR_TO_DATE('%s', '%s') AND """ % (
            dateformat, today, dateformat)

            query2 = """pa.HospitalID='%s' \
                    AND (st.status!='Create Pre-Auth') AND pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND \
                    st.srno = (SELECT MAX(srno) FROM `status_track` WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) \
                    GROUP BY pa.PatientID_TreatmentID UNION ALL select  pa.PatientID_TreatmentID,pa.insname,pa.admission_date,\
                    pa.p_sname,st.status FROM preauth pa LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN \
                    status_track st ON pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON \
                    pa.VNUPatientID=m.VNUPatientID""" % hospitalId

            query3 = """ WHERE STR_TO_DATE(pa.dischargedate, '%s')>= STR_TO_DATE('%s', '%s')\
                    AND """ % ((dateformat, today, dateformat))
            query4 = """ pa.HospitalID='%s'""" % hospitalId
            query5 = """ AND (st.status='Create Pre-Auth' AND \
                    STR_TO_DATE(st.cdate, '%s')>=STR_TO_DATE('%s', '%s')) AND \
                    pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM `status_track`\
                    WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID""" % (
            (dateformat, yesterday, dateformat))

            query = query1 + query2 + query3 + query4 + query5
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            if data:
                finalResponse['count'] = len(data)

            for row in data:
                localResponse = {}
                print(row)
                localResponse['name'] = row[3]
                localResponse['id'] = row[0]
                localResponse['insure_name'] = row[1]
                localResponse['admission_date'] = str(row[2])
                localResponse['status'] = row[4]
                localResponse['deadline'] = 'NA'
                mylist.append(localResponse)
            finalResponse['result'] = mylist
            # return jsonify(finalResponse)
        else:
            finalResponse['status'] = "failed"
            finalResponse[
                'message'] = 'Hospital ID is not present in hospital_employee table with respect to Mobile Number'
            # finalResponse['count']=len(data)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)
        # if data:
        #     finalResponse['count']=len(data)

        #     for row in data:
        #         localResponse={}
        #         print(row)
        #         localResponse['name']=row[3]
        #         localResponse['id']=row[0]
        #         localResponse['insure_name']=row[1]
        #         localResponse['admission_date']=str(row[2])
        #         localResponse['status']=row[4]
        #         localResponse['deadline']='NA'
        #         mylist.append(localResponse)
        #     finalResponse['result']=mylist
        #     return jsonify(finalResponse)
        # else:
        #     finalResponse['count']=len(data)
        #     return jsonify(finalResponse)


@app.route('/api/ActiveClarification', methods=['POST'])
def activeCaseClarification():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    cur = None
    finalResponse = {}
    mList = []
    mobileNo = ''
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form['mobileNo'] != '':
        mobileNo = request.form['mobileNo']

    if mobileNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        query = """select he_hospital_id from hospital_employee where he_mobile=%s"""
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query, (mobileNo,))
            data = cur.fetchone()
        if data:
            hospitalId = data[0]
            data = None
            # query= "select UTR_No, status from settlementutrupdate where HospitalID=%s"
            # cur.execute(query,(hospitalId,))
            query = """select UTR_No, status from settlementutrupdate where  status in ('C', 'CR') and HospitalID='%s'""" % hospitalId
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            if data:
                for row in data:
                    utrNo = row[0]
                    status_set = row[1]
                    localdic = {}
                    localdic['URT_NO'] = utrNo
                    localdic['status'] = status_set
                    data1 = None
                    query = """select InsurerID, PatientName from RawMasterSettlement where UTRNo='%s'""" % utrNo
                    print(query)
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        data1 = cur.fetchone()
                    if data1:
                        insID = data1[0]
                        pName = data1[1]
                        localdic['InsurerID'] = insID
                        localdic['PatientName'] = pName

                        query = """select name from insurer_tpa_master where TPAInsurerID='%s'""" % insID
                        print(query)
                        with mysql.connector.connect(**conn_data) as con:
                            cur = con.cursor()
                            cur.execute(query)
                            data1 = cur.fetchone()
                        if data1:
                            name = data1[0]
                            localdic['insurer_name'] = name
                        else:
                            localdic['insurer_name'] = ''

                    else:
                        localdic['InsurerID'] = ''
                        localdic['PatientName'] = ''
                        localdic['insurer_name'] = ''

                    data1 = None
                    query = "select clari_msg, clari_user,status,cdate from clarification_manage where utr_no='%s'" % utrNo
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        data1 = cur.fetchall()
                    if data1:
                        historyList = []
                        for row in data1:
                            clari_msg = row[0]
                            clari_user = row[1]
                            cdate = str(row[3])
                            localdic1 = {}
                            localdic1['clari_msg'] = clari_msg
                            localdic1['clari_user'] = clari_user
                            localdic1['cdate'] = cdate
                            print(row)
                            historyList.append(localdic1)

                        localdic['history'] = historyList
                    mList.append(localdic)
                finalResponse['result'] = mList
            else:
                finalResponse['status'] = "failed"
                finalResponse[
                    'message'] = 'UTR_No and status Are Not Present from settlementutrupdate table because status must in C and CR with respect to HospitalID'


        else:
            finalResponse['status'] = "failed"
            finalResponse[
                'message'] = 'Hospital ID is not present in hospital_employee Table with respect to Mobile Number'

    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        return jsonify(finalResponse)


@app.route('/api/StatusTrack', methods=['POST'])
def statusTrack():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    patientId = ''
    filepath = ''
    finalResponse = {}
    mList = []
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form['patientId'] != '':
        patientId = request.form['patientId']

    if patientId == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        query = """select status, cdate , srno , type FROM (`status_track`) WHERE `PatientID_TreatmentID` = '%s'""" % patientId
        query = query + """ORDER BY STR_TO_DATE(`cdate`, '%d/%m/%Y %H:%i:%s') DESC"""
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            for row in data:
                localDic = {}
                print(row)
                type1 = row[3]
                srno = row[2]
                localDic['status'] = row[0]
                localDic['date_time'] = str(row[1])
                data1 = None
                if type1 == 'PreAuth':
                    query = """select file_path from preauth_document where statustrackid = '%s'""" % (srno)
                else:
                    query = """select file_path from claim_document where statustrackid = '%s' """ % (srno)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    data1 = cur.fetchone()
                doctype = ''
                url = ''
                if type1 == 'PreAuth':
                    url = 'https://vnusoftware.com/iclaimtestmax/assets/upload/preauth/'
                else:
                    url = 'https://vnusoftware.com/iclaimtestmax/assets/upload/claim/'
                if data1:
                    for row in data1:
                        filename = data1[0]

                        print(filename)

                        # url=request.url_root
                        # url=url+'api/downloadfile?filename='
                        url = url + filename
                        localDic['url'] = url
                        mList.append(localDic)
            finalResponse['patientId'] = patientId
            finalResponse['statusTrack'] = mList
        else:
            finalResponse['status'] = "failed"
            finalResponse[
                'message'] = 'PatientID_TreatmentID not present in status_track table with respect to patientId OR Record does not found with respect to PatientID_TreatmentID'

    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfully")
        return jsonify(finalResponse)


# @app.route('/api/PatientSearch', methods=['POST'])
# def patientSearch():
#     data=None
#     patientId=''
#     patientName=''
#     mobileNo=''
#     mList=[]
#     finalResponse = {}
#     if request.method == "POST":
#         patientId=None
#         patientName=None
#         mobileNumber=None
#         if request.form.get('patientId')!= None :
#             patientId = request.form['patientId']
#         if request.form.get('patientName') != None:
#             patientName = request.form['patientName']
#         if request.form.get('mobileNo') != None:
#             mobileNumber = request.form['mobileNo']

#         if patientId != None:
#             try:
#                 con=mysql.connect()
#                 cur = con.cursor ( )
#                 query="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status,st.srno from preauth pa   \
#                     left join status_track st on pa.PatientID_TreatmentID=st.PatientID_TreatmentID where pa.PatientID_TreatmentID='%s' ORDER BY st.srno DESC LIMIT 1"""%patientId
#                 # query2="""select status from status_track where PatientID_TreatmentID='%s'"""%patientId
#                 print(query)
#                 cur.execute(query)
#                 data=cur.fetchall()
#                 if data !=None:
#                     for row in data:
#                         print(row)
#                         localDic = {}
#                         localDic['PatientID'] = row[0]
#                         localDic['name'] = row[3]
#                         localDic['insurer_name'] = row[1]
#                         localDic['admission_date'] = str(row[2])
#                         localDic['status'] = row[4]
#                         localDic['deadline'] = 'NA'
#                         mList.append ( localDic )

#                     finalResponse['patients:'] = mList
#             except Exception as e:
#                 print(e)
#                 finalResponse['status']="failed"
#                 finalResponse['message']='Something went wrong.Pls try after Some time or contact Support'
#                 finalResponse['reason']=e.__str__()

#             finally:
#                 cur.close()
#                 return jsonify(finalResponse)

#         elif mobileNumber != None:
#             try:
#                 con=mysql.connect()
#                 cur = con.cursor ( )
#                 query="""select he_hospital_id from hospital_employee where he_mobile='%s'"""%mobileNumber
#                 cur.execute(query)
#                 data=cur.fetchone()
#                 if data !=None:
#                     today=datetime.today().date()
#                     today = str(today.strftime("%d/%m/%Y"))
#                     print(today)

#                     yesterday = datetime.today().date() - timedelta(days=1)
#                     yesterday=str(yesterday.strftime("%d/%m/%Y"))
#                     print(yesterday)

#                     dateformat='%d/%m/%Y'

#                     hospitalID=data[0]
#                     data=None

#                     query0="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
#                     LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
#                     pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID \
#                     WHERE STR_TO_DATE(pa.dischargedate, '%s')>= STR_TO_DATE('%s', '%s') AND """%(dateformat,today,dateformat)

#                     query1="""pa.HospitalID='%s' AND (st.status!='Create Pre-Auth') AND \
#                     pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM \
#                     status_track WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID \
#                     UNION ALL select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
#                     LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
#                     pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID """%hospitalID

#                     query2="""WHERE STR_TO_DATE(pa.dischargedate, '%s')>= STR_TO_DATE('%s', '%s') """%(dateformat,today,dateformat)

#                     query3="""AND pa.HospitalID='%s' AND (st.status='Create Pre-Auth'AND """%hospitalID

#                     query4="""STR_TO_DATE(st.cdate, '%s')>=STR_TO_DATE('%s', '%s')) AND \
#                     pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM status_track\
#                     WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID """ % (dateformat,yesterday,dateformat)
#                     query=query0+query1+query2+query3+query4
#                     print(query)
#                     cur.execute(query)
#                     data=cur.fetchall()
#                     if data:
#                         for row in data:
#                             print(row)
#                             localDic = {}
#                             localDic['id'] = row[0]
#                             localDic['name'] = row[3]
#                             localDic['insurer_name'] = row[1]
#                             localDic['admission_date'] = str(row[2])
#                             localDic['status'] = row[4]
#                             localDic['deadline'] = 'NA'
#                             mList.append ( localDic )

#                         finalResponse['patients:'] = mList

#             except Exception as e:
#                 print(e)
#                 finalResponse['status']="failed"
#                 finalResponse['message']='Something went wrong.Pls try after Some time or contact Support'
#                 finalResponse['reason']=e.__str__()

#             finally:
#                 cur.close()
#                 return jsonify(finalResponse)

#         elif patientName != None:
#             try:
#                # pattern='%'
#                 data=None
#                 con=mysql.connect()
#                 cur = con.cursor ( )
#                 # query="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname, st.status from preauth pa   \
#                 #     left join status_track st on pa.PatientID_TreatmentID=st.PatientID_TreatmentID where pa.p_sname LIKE '%s%s%s'"""%(pattern,patientName,pattern)
#                 query="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname, st.status from preauth pa   \
#                     left join status_track st on pa.PatientID_TreatmentID=st.PatientID_TreatmentID where pa.p_sname ='%s'"""%patientName
#                 print(query)
#                 cur.execute(query)
#                 data=cur.fetchall()
#                 if data !=None:
#                     for row in data:
#                         print(row)
#                         localDic = {}
#                         localDic['PatientID'] = row[0]
#                         localDic['name'] = row[3]
#                         localDic['insurer_name'] = row[1]
#                         localDic['admission_date'] = str(row[2])
#                         localDic['status'] = row[4]
#                         localDic['deadline'] = 'NA'
#                         mList.append ( localDic )

#                     finalResponse['patients:'] = mList
#             except Exception as e:
#                 print(e)
#                 finalResponse['status']="failed"
#                 finalResponse['message']='Something went wrong.Pls try after Some time or contact Support'
#                 finalResponse['reason']=e.__str__()

#             finally:
#                 con.commit ( )
#                 cur.close()
#                 return jsonify(finalResponse)


@app.route('/api/PatientSearch', methods=['POST'])
def patientSearch():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    patientId = ''
    patientName = ''
    mobileNo = ''
    mList = []
    con = None
    finalResponse = {}
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )

    if request.form.get('patientId') != None:
        patientId = request.form['patientId']
    if request.form.get('patientName') != None:
        patientName = request.form['patientName']
    if request.form.get('mobileNo') != None:
        mobileNo = request.form['mobileNo']

    try:
        if patientId != '':
            query = """select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status,st.srno from preauth pa   \
                left join status_track st on pa.PatientID_TreatmentID=st.PatientID_TreatmentID where pa.PatientID_TreatmentID='%s' ORDER BY st.srno DESC LIMIT 1""" % patientId

            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            if data != None:
                for row in data:
                    print(row)
                    localDic = {}
                    localDic['PatientID'] = row[0]
                    localDic['name'] = row[3]
                    localDic['insurer_name'] = row[1]
                    localDic['admission_date'] = str(row[2])
                    localDic['status'] = row[4]
                    localDic['deadline'] = 'NA'
                    mList.append(localDic)
                finalResponse['patients:'] = mList
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in preauth table with respect to patientId'

        elif mobileNo != '':
            data = None
            query = """select he_hospital_id from hospital_employee where he_mobile='%s'""" % mobileNo
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data != None:
                today = datetime.today().date()
                today = str(today.strftime("%d/%m/%Y"))
                print(today)

                yesterday = datetime.today().date() - timedelta(days=1)
                yesterday = str(yesterday.strftime("%d/%m/%Y"))
                print(yesterday)

                dateformat = '%d/%m/%Y'

                hospitalID = data[0]
                data = None

                query0 = """select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
                LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
                pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID \
                WHERE STR_TO_DATE(pa.dischargedate, '%s')>= STR_TO_DATE('%s', '%s') AND """ % (
                dateformat, today, dateformat)

                query1 = """pa.HospitalID='%s' AND (st.status!='Create Pre-Auth') AND \
                pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM \
                status_track WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID \
                UNION ALL select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
                LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
                pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID """ % hospitalID

                query2 = """WHERE STR_TO_DATE(pa.dischargedate, '%s')>= STR_TO_DATE('%s', '%s') """ % (
                dateformat, today, dateformat)

                query3 = """AND pa.HospitalID='%s' AND (st.status='Create Pre-Auth'AND """ % hospitalID

                query4 = """STR_TO_DATE(st.cdate, '%s')>=STR_TO_DATE('%s', '%s')) AND \
                pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM status_track\
                WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID """ % (
                dateformat, yesterday, dateformat)
                query = query0 + query1 + query2 + query3 + query4
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    data = cur.fetchall()
                if data:
                    for row in data:
                        print(row)
                        localDic = {}
                        localDic['id'] = row[0]
                        localDic['name'] = row[3]
                        localDic['insurer_name'] = row[1]
                        localDic['admission_date'] = str(row[2])
                        localDic['status'] = row[4]
                        localDic['deadline'] = 'NA'
                        mList.append(localDic)
                    finalResponse['patients:'] = mList

            else:
                finalResponse['status'] = 'failed'
                finalResponse[
                    'message'] = 'Hospital ID is not present in hospital_employee table with respect to Mobile Number'

        elif patientName != '':
            data = None
            query = """select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname, st.status from preauth pa   \
                left join status_track st on pa.PatientID_TreatmentID=st.PatientID_TreatmentID where pa.p_sname ='%s'""" % patientName
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            if data != None:
                for row in data:
                    print(row)
                    localDic = {}
                    localDic['PatientID'] = row[0]
                    localDic['name'] = row[3]
                    localDic['insurer_name'] = row[1]
                    localDic['admission_date'] = str(row[2])
                    localDic['status'] = row[4]
                    localDic['deadline'] = 'NA'
                    mList.append(localDic)
                finalResponse['patients:'] = mList
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in preauth table with respect to patientName'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        return jsonify(finalResponse)


@app.route('/api/ClarificationReply', methods=['POST'])
def clarificationreply():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    utr_no = ''
    date1 = ''
    clari_msg = ''
    clari_user = ''
    user = ''
    status = ''
    doc = ''
    finalResponse = {}
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )

    if request.form.get('utr_no') != None:
        utr_no = request.form.get('utr_no')
    if request.form.get('date_time') != None:
        date1 = request.form.get('date_time')
    if request.form.get('comment') != None:
        clari_msg = request.form.get('comment')
    if request.form.get('user_name') != None:
        user = request.form.get('user_name')
    if request.form.get('status') != None:
        status = request.form.get('status')

    try:
        files = request.files.getlist("Documents")
        uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
        return jsonify(finalResponse)

    if utr_no == '' and date1 == '' and clari_msg == '' and user == '' and status == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        query = """INSERT INTO clarification_manage (utr_no,clari_msg,clari_user,`status`)  VALUES ('%s','%s','%s','C')""" % (
        utr_no, clari_msg, user)
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()
        query = """UPDATE settlementutrupdate SET `status`='C'  where UTR_No='%s' """ % utr_no
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()
        # query = """UPDATE clarification_manage SET clari_msg='%s', clari_user ='%s' ,status ='%s' ,cdate =DATE('%s') \
        #     where utr_no='%s'"""  %(clari_msg,user,status,date1,utr_no)
        # cur.execute (query )
        finalResponse['status'] = "success"
        finalResponse['message'] = 'Update Successfully'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        return jsonify(finalResponse)


@app.route('/api/incident', methods=['POST'])
def incident():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    finalResponse = {}
    mList = []
    mobileNo = ''
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mobileNo = request.form.get('mobileNo')

    if mobileNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'mobile number field is empty'
            }
        )

    try:
        query = """select he_hospital_id from hospital_employee where he_mobile=%s""" % mobileNo
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            hospitalId = data[0]
            data = None
            query = """select srno,tracking_no, Short_Description ,Urgency, Status, Created_TimeStamps from incident where Reported_By='%s'""" % hospitalId
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            if data:
                for row in data:
                    srno = row[0]
                    localDict = {}
                    localDict['tracking_no'] = row[1]
                    localDict['shortDesc'] = row[2]
                    localDict['urgency'] = row[3]
                    localDict['status'] = row[4]
                    localDict['timestamp'] = str(row[5])
                    # finalResponse['incident']=localDict

                    query = """select senderId,message from incident_comment  where srno=%s""" % srno
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        data1 = cur.fetchall()
                    if data1:
                        mList1 = []
                        for row in data1:
                            localDict1 = {}
                            localDict1['senderId'] = row[0]
                            localDict1['message'] = row[1]
                            mList1.append(localDict1)
                        localDict['log'] = mList1
                    mList.append(localDict)
                finalResponse['incident'] = mList
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in incident table with respect to hospitalId'
        else:
            finalResponse['status'] = 'failed'
            finalResponse[
                'message'] = 'Hospital ID is not present in hospital_employee table with respect to Mobile Number'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfully")
        return jsonify(finalResponse)


@app.route('/api/tSignature', methods=['POST'])
def tsignature():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])

    mobileNo = ''
    fromdate = ''
    todate = ''
    finalResponse = {}
    mList = []
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mobileNo = request.form.get('mobileNo')
    if request.form.get('fromdate') != None:
        fromdate = request.form.get('fromdate')
    if request.form.get('todate') != None:
        todate = request.form.get('todate')
    dateformat = '%d/%m/%Y'
    # dateformat='%d/%m/%Y %H:%M:%S'

    if mobileNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'mobile number field is empty'
            }
        )
    try:
        query = """select he_hospital_id from hospital_employee where he_mobile='%s'""" % mobileNo
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            hospitalId = data[0]
            data = None

            if fromdate != '' and todate != '':
                query = """select PatientID_TreatmentID,Mobile,Name, cdate,status, validity,path from signature_request where  HospitalID='%s' \
                and STR_TO_DATE(cdate, '%s') between STR_TO_DATE('%s', '%s')\
                    and STR_TO_DATE('%s', '%s')""" % (hospitalId, dateformat, fromdate, dateformat, todate, dateformat)
            else:
                query = """select PatientID_TreatmentID,Mobile,Name, cdate,status, validity,path from signature_request where \
                HospitalID='%s'""" % hospitalId
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchall()
            if data:
                for row in data:
                    localDict = {}
                    localDict['PatientID_TreatmentID'] = row[0]
                    localDict['patient_mobileNo'] = row[1]
                    localDict['Name'] = row[2]
                    localDict['cdate'] = str(row[3])
                    localDict['status'] = row[4]
                    localDict['path'] = row[6]

                    cdate = str(row[3])
                    patient_treatmentID = row[0]
                    validity = int(row[5])

                    oldtime = datetime.strptime(cdate, '%d/%m/%Y')
                    # oldtime=datetime.strptime(cdate,'%d/%m/%Y %H:%M:%S' )

                    new_time = datetime.now()

                    timeInterval = (new_time - oldtime).total_seconds() / 60

                    print(new_time)
                    print(oldtime)
                    print(timeInterval)
                    if timeInterval > validity:
                        query = """UPDATE signature_request SET status ='Expired' where PatientID_TreatmentID='%s' """ % patient_treatmentID
                        print(query)
                        with mysql.connector.connect(**conn_data) as con:
                            cur = con.cursor()
                            cur.execute(query)
                            con.commit()
                        localDict['status'] = 'Expired'
                    mList.append(localDict)
                finalResponse['result'] = mList
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in signature_request table with respect to hospitalId'
        else:
            finalResponse['status'] = 'failed'
            finalResponse[
                'message'] = 'Hospital ID is not present in hospital_employee table with respect to Mobile Number'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfully")
        return jsonify(finalResponse)


@app.route('/api/tSignatureCancel', methods=['POST'])
def tsignatureusecancel():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    mNo = ''
    pId = ''
    status = ' '
    remark = ''
    finalResponse = {}
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('PatientId') != None:
        pId = request.form.get('PatientId')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')
    if request.form.get('status') != None:
        status = request.form.get('status')
    if request.form.get('remark') != None:
        remark = request.form.get('remark')

    if mNo == '' or pId == '' or hId == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        data = None
        con = mysql.connect()
        cur = con.cursor()
        query = """select status from signature_request where Mobile=%s and PatientID_TreatmentID='%s' \
            and HospitalID='%s' """ % (mNo, pId, hId)
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            t_status = data[0]
            if t_status != 'Expired':
                query = """UPDATE signature_request SET status ='%s', remarks='%s' where Mobile=%s \
                    and PatientID_TreatmentID='%s' and HospitalID='%s' """ % (status, remark, mNo, pId, hId)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    con.commit()
                finalResponse['status'] = "success"
                finalResponse['message'] = "update Successfully"
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Signature request is already Expired. No action Required'
        else:
            finalResponse['status'] = "failed"
            finalResponse[
                'message'] = 'status is not present Signature request table with respect to Mobile number,PatientID_TreatmentID And HospitalID '

    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/tSignatureUse', methods=['POST'])
def tsignatureuse():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])

    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    mNo = ''
    pId = ''
    status = ''
    hId = ''
    sign = ''
    finalResponse = {}
    result = 'failure'
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('PatientId') != None:
        pId = request.form.get('PatientId')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')
    if request.form.get('status') != None:
        status = request.form.get('status')

    if mNo == '' and pId == '' and hId == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        data = None
        result = None
        query = """select * from signature_request where Mobile=%s and PatientID_TreatmentID='%s'""" % (mNo, pId)
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            query = """UPDATE signature_request SET status ='%s'  where Mobile=%s and PatientID_TreatmentID='%s'""" % (
            status, mNo, pId)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()
            finalResponse['status'] = "success"
            finalResponse['message'] = 'update Successfully'
        else:
            finalResponse['status'] = "failed"
            finalResponse[
                'message'] = 'Record does not found in signature_request table with respect to Mobile And PatientID_TreatmentID'

    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfully")
        return jsonify(finalResponse)


@app.route('/api/tQueryReply', methods=['POST'])
def tqueryreply():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    finalResponse = {}
    mNo = ''
    hId = ''
    pId = ''
    desc = ''
    qFlag = ''
    cstatus = ''
    amount = ''
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')
    if request.form.get('PatientID') != None:
        pId = request.form.get('PatientID')
    if request.form.get('Description') != None:
        desc = request.form.get('Description')
    if request.form.get('qFlag') != None:
        qFlag = request.form.get('qFlag')
    if request.form.get('CurrentStatus') != None:
        cstatus = request.form.get('CurrentStatus')
    if request.form.get('amount') != None:
        amount = request.form.get('amount')

    try:
        # files = request.files.getlist("files")
        Documents = request.files.getlist("Documents")
        # uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        return jsonify(finalResponse)

    if mNo == '' or pId == '' or hId == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    try:
        fileNameList = []
        for file in Documents:
            if file and allowed_file(file.filename):
                data = None
                filename = secure_filename(file.filename)
                fileNameList.append(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        query = """select Type,cdate from status_track \
                where PatientID_TreatmentID='%s'  ORDER BY cdate DESC ;""" % pId
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            type1 = str(data[0])
            cdate = str(data[1])

            if type1 == 'Claim':
                print("Inside claim")
                query = """INSERT  INTO tmTrans (HospitalID,PatientID_TreatmentID,Flag,`Type`,CurrentStatus,`Description`,amount ,Processed ,`Lock`,cdate) \
                VALUES ( '%s' , '%s' , '%s' , '%s' , '%s' , '%s','%s' ,'0','0','%s')""" % (
                hId, pId, qFlag, type1, cstatus, desc, amount, cdate)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    con.commit()

                for filename in fileNameList:
                    query = """INSERT INTO tmTrans_doc (refernceNo,document,cdate) \
                    VALUES ( '%s','%s','%s')""" % (pId, filename, cdate)
                    print(query)
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        con.commit()
                finalResponse['status'] = "success"
                finalResponse['message'] = " Update Successfully"

            elif type1 == 'PreAuth':
                print("Inside preauth")

                if cstatus == 'Enhancement Information Awaiting':
                    query = """INSERT  INTO tmTrans (HospitalID,PatientID_TreatmentID,Flag,`Type`,CurrentStatus,`Description` ,Processed,amount ,`Lock`,cdate) \
                    VALUES ( '%s','%s','%s','%s','%s','%s','%s','0','0','%s')""" % (
                    hId, pId, qFlag, type1, cstatus, amount, desc, cdate)
                    print(query)
                    cur.execute(query)

                    for filename in fileNameList:
                        query = """INSERT INTO tmTrans_doc (refernceNo,document,cdate) \
                        VALUES ( '%s','%s','%s')""" % (pId, filename, cdate)
                        print(query)
                        with mysql.connector.connect(**conn_data) as con:
                            cur = con.cursor()
                            cur.execute(query)
                            con.commit()
                    finalResponse['status'] = "success"
                    finalResponse['message'] = " Update Successfully"

                elif cstatus == 'Information Awaiting':
                    query = """INSERT  INTO tmTrans (HospitalID,PatientID_TreatmentID,Flag,`Type`,CurrentStatus,`Description`,amount ,Processed ,`Lock`,cdate) \
                    VALUES ( '%s','%s','%s','%s','%s','%s','%s','0','0','%s')""" % (
                    hId, pId, qFlag, type1, cstatus, desc, amount, cdate)
                    print(query)
                    cur.execute(query)
                    for filename in fileNameList:
                        query = """INSERT INTO tmTrans_doc (refernceNo,document,cdate) \
                        VALUES ( '%s','%s','%s')""" % (pId, filename, cdate)
                        print(query)
                        with mysql.connector.connect(**conn_data) as con:
                            cur = con.cursor()
                            cur.execute(query)
                            con.commit()
                    finalResponse['status'] = "success"
                    finalResponse['message'] = " Update Successfully"
        else:
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Record does not found in status_track table with respect to PatientID'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfully")
        return jsonify(finalResponse)


@app.route('/api/EnhanceFinal', methods=['POST'])
def enhancefinal():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    finalResponse = {}
    mNo = ''
    hId = ''
    pId = ''
    desc = ''
    flag = ''
    files = ''
    Documents = ''
    amount = ''
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )

    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')
    if request.form.get('PatientID') != None:
        pId = request.form.get('PatientID')
    if request.form.get('Description') != None:
        desc = request.form.get('Description')
    if request.form.get('Flag') != None:
        flag = request.form.get('Flag')
    if request.form.get('amount') != None:
        amount = request.form.get('amount')
    try:
        # files = request.files.getlist("files")
        Documents = request.files.getlist("Documents")
        # uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
        return jsonify(finalResponse)

    if mNo == '' or pId == '' or hId == '' or flag == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    if flag == 'e' or flag == 'E':
        try:
            data = None
            fileNameList = []
            for file in Documents:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    fileNameList.append(filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            query = """select Type,cdate from status_track where PatientID_TreatmentID='%s' ORDER BY cdate DESC ;""" % pId
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data:
                type1 = str(data[0])
                cdate = str(data[1])
                query = """INSERT INTO tmTrans (HospitalID,PatientID_TreatmentID,Flag,`Type`,`Description` ,amount,Processed ,`Lock`,cdate) \
                VALUES ( '%s' , '%s' , '%s' , '%s' ,'%s','%s' ,'0','0','%s') """ % (
                hId, pId, flag, type1, desc, amount, cdate)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    con.commit()
                query = """SELECT srno from tmTrans where PatientID_TreatmentID='%s'""" % pId
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    data = cur.fetchall()
                for filename in fileNameList:
                    if data:
                        for row in data:
                            srno = row[0]
                            query = """INSERT INTO tmTrans_doc (refernceNo,document,cdate) \
                            VALUES ( '%s','%s','%s')""" % (srno, filename, cdate)
                            print(query)
                            with mysql.connector.connect(**conn_data) as con:
                                cur = con.cursor()
                                cur.execute(query)
                                con.commit()
                        finalResponse['status'] = "success"
                        finalResponse['message'] = " Update Successfully"
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in status_track table with respect to PatientID'
        except Exception as e:
            print(e)
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
            finalResponse['reason'] = e.__str__()

        finally:
            print("Connection has been closed successfully")
            return jsonify(finalResponse)


    elif flag == 'F' or flag == 'f':
        print("Inside f")
        print("k")
        try:
            print("h")
            data = None
            fileNameList = []
            for file in Documents:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    fileNameList.append(filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            query = """select Type,cdate from status_track where PatientID_TreatmentID='%s' ORDER BY cdate DESC ;""" % pId
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data:
                type1 = str(data[0])
                cdate = str(data[1])
                query = """INSERT INTO tmTrans (HospitalID,PatientID_TreatmentID,Flag,`Type`,`Description` ,amount,Processed ,`Lock`,cdate) \
                VALUES ( '%s' , '%s' , '%s' , '%s' ,'%s','%s' ,'0','0','%s') """ % (
                hId, pId, flag, type1, desc, amount, cdate)
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    con.commit()
                query = """SELECT srno from tmTrans where PatientID_TreatmentID='%s'""" % pId
                print(query)
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    data = cur.fetchall()
                for filename in fileNameList:
                    if data:
                        for row in data:
                            srno = row[0]
                            query = """INSERT INTO tmTrans_doc (refernceNo,document,cdate) \
                            VALUES ( '%s','%s','%s')""" % (srno, filename, cdate)
                            print(query)
                            with mysql.connector.connect(**conn_data) as con:
                                cur = con.cursor()
                                cur.execute(query)
                                con.commit()
                        finalResponse['status'] = "success"
                        finalResponse['message'] = " Update Successfully"
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in status_track table with respect to PatientID'
        except Exception as e:
            print(e)
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
            finalResponse['reason'] = e.__str__()

        finally:
            print("Connection has been closed successfuilly")
            return jsonify(finalResponse)


@app.route('/api/IncidentCreate', methods=['POST'])
def incidentcreate():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    data = None
    finalResponse = {}
    desc = ''
    reportedto = ''
    reportby = ''
    pId = ''
    urg = ''
    phoneNo = ''
    emailId = ''
    issueDesc = ''
    mList = []
    Documents = ''
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('description') != None:
        desc = request.form.get('description')
        desc = desc.replace("'", '')
        desc = desc.replace('"', '')
    if request.form.get('raisedto') != None:
        reportedto = request.form.get('raisedto')
    if request.form.get('reportedby') != None:
        reportby = request.form.get('reportedby')
    if request.form.get('patientId') != None:
        pId = request.form.get('patientId')
    if request.form.get('urgency') != None:
        urg = request.form.get('urgency')
    if request.form.get('hospital_phoneNumber') != None:
        phoneNo = request.form.get('hospital_phoneNumber')
    if request.form.get('emailid') != None:
        emailId = request.form.get('emailid')
    if request.form.get('issue_description') != None:
        issueDesc = request.form.get('issue_description')
        issueDesc = issueDesc.replace("'", '')
        issueDesc = issueDesc.replace('"', '')

    try:
        files = request.files.getlist("Documents")
        uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
        return jsonify(finalResponse)

    if desc != '' and reportedto != '' and reportby != '' and pId != '' \
            and urg != '' and phoneNo != '' and emailId != '' and issueDesc != '':
        try:
            query = """select max(srno) from incident"""
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data:
                srno = data[0]
                data = None
                query = """select srno,tracking_no from incident where srno=%s""" % srno
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    data = cur.fetchone()
                if data:
                    trackingNo = data[1]

                    list1 = trackingNo.split('-')
                    if (len(list1) > 1):
                        latestno = int(list1[1]) + 1
                        newtrackingno = list1[0] + "-" + str(latestno)
                        query = "INSERT INTO incident (srno,VNUPatientID,tracking_no,Short_Description, \
                        Urgency,`Status`,Reported_By,Reported_To,Email_ID,Phone,Issue_Description)\
                        VALUES (%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') \
                        " % (srno + 1, pId, newtrackingno, desc, urg, 'open', reportby, reportedto, emailId, phoneNo,
                             issueDesc)
                        print(query)
                        with mysql.connector.connect(**conn_data) as con:
                            cur = con.cursor()
                            cur.execute(query)
                            con.commit()
                        finalResponse['status'] = "success"
                else:
                    finalResponse['status'] = "failed"
                    finalResponse['message'] = 'Record does not found in incident table'
            else:
                finalResponse['status'] = "failed"
                finalResponse['message'] = 'Record does not found in incident table'
        except Exception as e:
            print(e)
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
            finalResponse['reason'] = e.__str__()


        finally:
            temDict = {}
            temDict['incident_no'] = newtrackingno
            temDict['description'] = desc
            temDict['raisedto'] = reportedto
            temDict['reportedby'] = reportby
            temDict['patientId'] = pId
            temDict['urgency'] = urg
            temDict['hospital_phoneNumber'] = phoneNo
            temDict['emailid'] = emailId
            temDict['issue_description'] = issueDesc
            mList.append(temDict)
            finalResponse['data'] = mList
            print("Connection has been closed successfuilly")
            # finalResponse['incident_no']=newtrackingno
            # finalResponse['description']=desc
            # finalResponse['raisedto']=reportedto
            # finalResponse['reportedby']=reportby
            # finalResponse['patientId']=pId
            # finalResponse['urgency']=urg
            # finalResponse['hospital_phoneNumber']=phoneNo
            # finalResponse['emailid']=emailId
            # finalResponse['issue_description']=issueDesc
            return jsonify(finalResponse)
    else:
        temDict = {}
        temDict['incident_no'] = ''
        temDict['description'] = ''
        temDict['raisedto'] = ''
        temDict['reportedby'] = ''
        temDict['patientId'] = ''
        temDict['urgency'] = ''
        temDict['hospital_phoneNumber'] = ''
        temDict['emailid'] = emailId
        temDict['issue_description'] = ''
        mList.append(temDict)
        finalResponse['status'] = 'failure'
        finalResponse['data'] = mList
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/pSignature', methods=['POST'])
def pSignature():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    finalResponse = {}
    mList = []
    mobileNo = ''
    todate = ''
    fromdate = ''
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mobileNo = request.form.get('mobileNo')
    if request.form.get('fromdate') != None:
        fromdate = request.form.get('fromdate')
    if request.form.get('todate') != None:
        todate = request.form.get('todate')
    dateformat = '%d/%m/%Y'
    if mobileNo == '':
        finalResponse['status'] = 'failure'
        finalResponse['reason'] = "Parameter Field Are Empty"
        return jsonify(finalResponse)

    try:
        data = None
        if fromdate != '' and todate != '':
            query = """select HospitalID,PatientID_TreatmentID,validity,cdate,status,path from signature_request where Mobile='%s' \
            and STR_TO_DATE(cdate, '%s') between STR_TO_DATE('%s', '%s') \
            and STR_TO_DATE('%s', '%s')""" % (mobileNo, dateformat, fromdate, dateformat, todate, dateformat)
        else:
            query = """select HospitalID,PatientID_TreatmentID,validity,cdate,status,path from signature_request where Mobile='%s' """ % mobileNo
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            for row in data:
                temDict = {}
                temDict['hospitalId'] = row[0]
                temDict['patientId'] = row[1]
                temDict['validity'] = row[2]
                temDict['cdate'] = row[3]
                temDict['status'] = row[4]
                temDict['path'] = row[5]
                mList.append(temDict)
            finalResponse['status'] = "success"
            finalResponse['data'] = mList
        else:
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Record does not found in signature_request table'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed",
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/tSignatureRequest', methods=['POST'])
def tsignatureuserequest():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    mNo = ''
    pId = ''
    status = ' '
    path = ''
    cdate = ''
    validity = ''
    remark = ''
    Documents = ''
    finalResponse = {}
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('PatientId') != None:
        pId = request.form.get('PatientId')
    if request.form.get('cdate') != None:
        cdate = request.form.get('cdate')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')
    if request.form.get('status') != None:
        status = request.form.get('status')
    if request.form.get('validity') != None:
        validity = request.form.get('validity')
    if request.form.get('remark') != None:
        remark = request.form.get('remark')

    try:
        files = request.files.getlist("Documents")
        uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
        return jsonify(finalResponse)

    if mNo == '' or hId == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    finalResponse = {}
    try:
        query = """select pname from patient_master where mobile='%s' """ % mNo
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            pName = data[0]
            today = datetime.today().date()
            today1 = str(today.strftime("%d/%m/%Y %H:%M:%S"))
            query = """select PatientID_TreatmentID from preauth where p_contact='%s'""" % mNo
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data:
                ptreatmentid = data[0]
                query = """select status from signature_request where Mobile='%s'""" % mNo
                print(query)
                data = None
                with mysql.connector.connect(**conn_data) as con:
                    cur = con.cursor()
                    cur.execute(query)
                    data = cur.fetchone()
                flag = 0

                if data:
                    status = data[0]
                    if status == "Expired":
                        # query="""UPDATE signature_request SET PatientID_TreatmentID ='%s',Mobile='%s',`Name`='%s',cdate='%s',`status`='Requested',HospitalID='%s',validity='30',`path`='%s',remarks='%s'""" %(ptreatmentid,int(mNo),pName,today1,hId,path,remark)
                        query = """UPDATE signature_request SET `status`='Requested',validity='30'  where Mobile='%s' """ % mNo

                        with mysql.connector.connect(**conn_data) as con:
                            cur = con.cursor()
                            cur.execute(query)
                            con.commit()
                        finalResponse['status'] = "Success"
                        finalResponse['message'] = 'Request generated successfully for Patient. Validity is 30 min only'

                elif data is None:

                    query = """insert into signature_request(PatientID_TreatmentID,Mobile,Name,cdate,status,HospitalID,\
                    validity,path,remarks) values('%s',%s,'%s','%s','Requested','%s','30','%s','%s') """ % (
                    ptreatmentid, int(mNo), pName, today1, hId, path, remark)
                    print(query)
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        con.commit()
                    finalResponse['status'] = "Success"
                    finalResponse['message'] = 'Request generated successfully for Patient. Validity is 30 min only'
                if flag == 1:
                    finalResponse['status'] = 'Failed'
                    finalResponse['message'] = ' Signature request is already in Progress'

                if len(finalResponse) == 0:
                    finalResponse['status'] = 'Failed'
                    finalResponse['message'] = 'Signature request is already in Progress'

            else:
                finalResponse['status'] = 'Failed'
                finalResponse[
                    'message'] = 'PatientID_TreatmentID Not Found from preauth table with respect to Mobile Number'

        else:
            finalResponse['status'] = 'Failed'
            finalResponse['message'] = 'pname Not Found from patient_master table with respect to Mobile Number'


    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/UserProfile', methods=['POST'])
def userProfile():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )

    mNo = ''
    mList = []
    finalResponse = {}
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if mNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    try:
        query = """select pname,gender,dob,r_name,r_mobile,r_relation from patient_master where mobile=%s""" % mNo
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data != None:
            print(data)
            localDic = {}
            finalResponse['pname'] = data[0]
            finalResponse['gender'] = data[1]
            finalResponse['dob'] = data[2]
            localDic['r_name'] = str(data[3])
            localDic['r-mobile'] = data[4]
            localDic['r_relation'] = data[5]
            mList.append(localDic)

            finalResponse['relative'] = mList
        else:
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Record does not found in patient_master table with respect to Mobile Number'
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/UserProfileSave', methods=['POST'])
def userProfilesave():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    mNo = ''
    pName = ''
    gender = ''
    dob = ''
    relative = ''
    mList = []
    finalResponse = {}
    conn = None
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('patientname') != None:
        pName = request.form.get('patientname')
    if request.form.get('gender') != None:
        gender = request.form.get('gender')
    if request.form.get('dob') != None:
        dob = request.form.get('dob')
    if request.form.get('relative') != None:
        relative = request.form.get('relative')
    relativeList = None
    try:
        print(relative)
        relativeList = eval(relative)
        print(len(relativeList))
    except Exception as e:
        print(e.__str__())
        return jsonify({"status": "failure"})

    if mNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    try:
        query = "update patient_master set "
        if pName != '':
            query = query + "pname='%s', " % pName
        if gender != '':
            query = query + "gender='%s', " % gender
        if dob != '':
            query = query + "dob='%s' " % dob

        if len(query) > len("update patient_master set "):
            query = query + " where mobile='%s'" % mNo
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()
            finalResponse['status'] = "success"
            finalResponse['message'] = "Profile Update Successfully"

            if relativeList is not None:
                for relative in relativeList:
                    print(relative)
                    relative_dic = dict(relative)

                    query = """insert into e_relation(mobile,r_name,r_mobilel,r_relation) \
                    values('%s','%s','%s','%s')""" % (
                    mNo, relative_dic['r_name'], relative_dic['r_mobile'], relative_dic['r_relation'])
                    print(query)
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        con.commit()
        else:
            finalResponse['status'] = "failed "
            finalResponse['message'] = "Something went wrong, please try in some time or contact support"

    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/pQueryReply', methods=['POST'])
def pqueryreply():
    mNo = ''
    hId = ''
    datetime = ''
    status = ''
    doc = ''
    finalResponse = {}
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('HospitalID') != None:
        hId = request.form.get('HospitalID')
    if request.form.get('datetime') != None:
        datetime = request.form.get('datetime')
    if request.form.get('status') != None:
        status = request.form.get('status')

    try:
        files = request.files.getlist("Documents")
        uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        return jsonify(finalResponse)

    if mNo == '' or hId == '' or datetime == '' or status == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    try:
        print("Logic needs to written later")
        finalResponse['status'] = "success"
        finalResponse['message'] = "Update Successfully"

    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        # mysql.connect().commit ( )
        # cur.close ( )
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/pQuery', methods=['POST'])
def pquery():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    mobileNo = ''
    fromdate = ''
    todate = ''
    finalResponse = {}
    mList = []
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mobileNo = request.form.get('mobileNo')
    if request.form.get('fromdate') != None:
        fromdate = request.form.get('fromdate')
    if request.form.get('todate') != None:
        todate = request.form.get('todate')
    dateformat = '%d/%m/%Y'

    if mobileNo == '':
        finalResponse['status'] = "failed"
        finalResponse['reason'] = "Parameter Field Are Empty"
        return jsonify(finalResponse)

    try:
        if fromdate != '' and todate != '':
            query = """select VNUPatientID,status,cdate  from patient_claimquery where  mobile=%s \
            and STR_TO_DATE(cdate, '%s') between STR_TO_DATE('%s', '%s')\
            and STR_TO_DATE('%s', '%s')""" % (mobileNo, dateformat, fromdate, dateformat, todate, dateformat)
        else:
            query = """select VNUPatientID,status,cdate from patient_claimquery where \
                mobile=%s""" % (mobileNo)

        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            for row in data:
                tempdic = {}
                print(data)
                tempdic['VNUPatientID'] = row[0]
                tempdic['status'] = row[1]
                tempdic['cdate'] = row[2]
                mList.append(tempdic)
            finalResponse['status'] = 'success'
            finalResponse['data'] = mList
        else:
            finalResponse['status'] = "failed"
            finalResponse['message'] = 'Record does not found in patient_claimquery table'
    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed',
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/pSignatureResponse', methods=['POST'])
def pSignatureresponse():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    pId = ''
    hId = ''
    datetime = ''
    status = ''
    doc = ''
    finalResponse = {}

    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('PatientID') != None:
        pId = request.form.get('PatientID')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')
    if request.form.get('datetime') != None:
        datetime = request.form.get('datetime')
    if request.form.get('status') != None:
        status = request.form.get('status')

    try:
        files = request.files.getlist("Documents")
        uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        return jsonify(finalResponse)

    if pId == '' or hId == '' or datetime == '' or status == '' or doc == '':
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Parameter Field Are Empty'
        return jsonify(finalResponse)

    try:
        query = """UPDATE signature_request SET cdate ='%s',status ='%s',path ='%s' \
            where PatientID_TreatmentID='%s'""" % (datetime, status, doc, pId)
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            con.commit()
        finalResponse['status'] = "success"
        finalResponse['message'] = "Update Successfully"
    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed',
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/downloadfile', methods=['GET', 'POST'])
def downloadFile():
    if request.args['filename'] != None:
        filename = request.args['filename']
    print("filename=", filename)
    # filepath1=r"C:\Users\91798\Desktop\trial_shikha-master2\hdfc\attachments_pdf_denial\PreAuthDenialLe_RC-HS19-10809032_1_202_20200129142830250_19897.pdf"
    # filepath=filepath.replace("\\", "/")
    # mylist=filepath.split('/')
    # filename=mylist[-1]

    # dirname=os.path.dirname(filepath)
    dirname = app.config['UPLOAD_FOLDER']
    try:
        # return send_from_directory(r"C:\Users\91798\Desktop\download\templates", filename='ASHISHKUMAR_IT.pdf', as_attachment=True)
        return send_from_directory(dirname, filename=filename, as_attachment=True)
    except Exception as e:
        print(e.__str__())
        return jsonify(
            {
                'status': 'failed',
                'message': 'file does not exist at resources'
            }
        )


@app.route('/api/mydoc1', methods=['POST'])
def mydoc():
    base64String = ''
    mobile_no = ''
    cdate = ''
    path = ''
    decs = ''
    type = ''

    if request.method == "POST":
        if request.method != 'POST':
            return jsonify(
                {
                    'status': 'failed',
                    'message': 'inavlid request method.Only Post method Allowed'
                }
            )
    if request.form.get('mobileNo') != None:
        mobile_no = request.form['mobileNo']
    if request.form.get('cdate') != None:
        cdate = request.form['cdate']
    if request.form.get('path') != None:
        path = request.form['path']
    if request.form.get('description') != None:
        decs = request.form['description']
    if request.form.get('type') != None:
        type = request.form['type']

    if mobile_no == '' or cdate == '' or decs == '' or type == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    if request.form.get('base64_string') != None:
        base64String = request.form.get('base64_string')
        print(base64String)
        with open("./static/myimage.png", "wb") as fh:
            fh.write(base64.decodebytes(base64String.encode()))
            print('file write successfully')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def uploadFile(files):
    fileList = []
    for file in files:
        if file and allowed_file(file.filename):
            tempDict = {}
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            tempDict['fileName'] = filename
            tempDict['filepath'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            fileList.append(tempDict)
    return fileList


@app.route('/api/UserDoc', methods=['POST'])
def userDoc():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    mobile_no = ''
    cdate = ''
    desc = ''
    r_type = ''
    Insurer_Name = ''
    InsurerID = ''
    PolicyID = ''
    Expiry_date = ''
    Sum_insurance = ''
    conn = None
    cur = None

    finalResponse = {}
    mList = []
    if request.method == "POST":
        if request.method != 'POST':
            return jsonify(
                {
                    'status': 'failed',
                    'message': 'inavlid request method.Only Post method Allowed'
                }
            )
    if request.form.get('mobileNo') != None:
        mobile_no = request.form['mobileNo']
    if request.form.get('type') != None:
        r_type = request.form['type']

    if 'cdate' in request.form:
        cdate = request.form.getlist('cdate')

    if 'description' in request.form:
        desc = request.form.getlist('description')

    if 'Insurer_Name' in request.form:
        Insurer_Name = request.form.getlist('Insurer_Name')
    if 'InsurerID' in request.form:
        InsurerID = request.form.getlist('InsurerID')
    # if 'PolicyID' in request.form:
    PolicyID = request.form.getlist('PolicyID')
    # if 'ExpiryDate' in request.form:
    Expiry_date = request.form.getlist('ExpiryDate')
    # if 'Sum_insurance' in request.form:
    Sum_insurance = request.form.getlist('Sum_insurance')

    if mobile_no == '' or r_type == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    if 'files' not in request.files:
        return jsonify(
            {"status": "failed",
             'message': 'No File Selected'
             })
    files = request.files.getlist("files")
    conn = None
    if r_type == 'Insurance':
        if ((len(files) != len(Insurer_Name)) or (len(files) != len(InsurerID)) or (len(files) != len(Expiry_date)) or (
                len(files) != len(Sum_insurance))):
            finalResponse['status'] = 'failed'
            finalResponse[
                'message'] = 'length of files, Insurer_Name,InsurerID,Expiry_date,Sum_insurance should be same'
            return jsonify(finalResponse)

    elif r_type == 'IDCardDetails' or r_type == 'Reports' or r_type == 'Others':
        if ((len(files) != len(cdate)) or (len(files) != len(desc))):
            print("hiii")
            finalResponse['status'] = 'failed'
            finalResponse['message'] = 'length of files, cdate,description should be same'
            return jsonify(finalResponse)

    try:
        if r_type == 'Insurance':
            index = 0
            for file in files:
                if file and allowed_file(file.filename):
                    localRespons = {}
                    data = None
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    url = request.url_root
                    url = url + 'api/downloadfile?filename='
                    url = url + filename
                    localRespons['file'] = filename
                    localRespons['url'] = url
                    mList.append(localRespons)
                    # f_path=app.config['UPLOAD_FOLDER'])+"/"+filename
                    query = """insert into patient_ndoc(mobile,`type`,path,Insurer_Name,InsurerID,PolicyID,Expiry_date,Sum_insurance) values ('%s','%s','%s','%s','%s','%s','%s','%s')""" % (
                    mobile_no, r_type, filename, Insurer_Name[index], InsurerID[index], PolicyID[index],
                    Expiry_date[index], Sum_insurance[index])
                    print(query)
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        con.commit()
                    index = index + 1

            if len(mList) <= 0:
                finalResponse['status'] = 'failed'
                finalResponse['message'] = 'Documents can not not be saved since file field is empty'
            else:
                finalResponse['status'] = 'success'
                finalResponse['message'] = 'Document Saved Successfully'
            finalResponse['docList'] = mList
            return jsonify(finalResponse)

        elif r_type == 'IDCardDetails' or r_type == 'Reports' or r_type == 'Others':

            index = 0
            for file in files:
                if file and allowed_file(file.filename):
                    localRespons = {}
                    data = None
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                    url = request.url_root
                    url = url + 'api/downloadfile?filename='
                    url = url + filename
                    localRespons['file'] = filename
                    localRespons['url'] = url
                    mList.append(localRespons)
                    # f_path=app.config['UPLOAD_FOLDER'])+"/"+filename
                    query = """insert into patient_mdocs(mobile,`type`,path,cdate,`desc`) values (%s,'%s','%s','%s','%s')""" % (
                    int(mobile_no), r_type, filename, cdate[index], desc[index])
                    print(query)
                    with mysql.connector.connect(**conn_data) as con:
                        cur = con.cursor()
                        cur.execute(query)
                        con.commit()
                    index = index + 1

            if len(mList) <= 0:
                finalResponse['status'] = 'failed'
                finalResponse['message'] = 'Documents can not not be saved since file field is empty'
            else:
                finalResponse['status'] = 'success'
                finalResponse['message'] = 'Document Saved Successfully'
            finalResponse['docList'] = mList

    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed',
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/pDelete', methods=['POST'])
def pdelete():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    reason = ''
    mNo = ''
    datetime = ''
    status = ''
    finalResponse = {}
    conn = None
    cur = None
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('MobileNo') != None:
        mNo = request.form.get('MobileNo')
    if request.form.get('reason') != None:
        reason = request.form.get('reason')
    if request.form.get('datetime') != None:
        datetime = request.form.get('datetime')
    if request.form.get('status') != None:
        status = request.form.get('status')

    if mNo == '' or status == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )
    try:
        query = """select * from patient_master where mobile='%s'""" % mNo
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            query = """UPDATE patient_master SET `status` ='%s',cdate ='%s' \
                where mobile='%s'""" % (status, datetime, mNo)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()
            if status.lower() == 'd':
                finalResponse['status'] = "success"
                finalResponse['message'] = "Your Account has been Deleted"

            elif status.lower() == 'da':
                finalResponse['status'] = "success"
                finalResponse['message'] = "Your Account has been Deactivated"
        else:
            finalResponse['status'] = 'failed'
            finalResponse["message"] = 'Record does not found in patient_master Table with respect to Mobile Number'

    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/pClaim', methods=['POST'])
def pclaim():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    mNo = ''
    finalResponse = {}
    mList = []
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')

    if mNo == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    try:
        query = """select HospitalID,hospital_name,insname,p_sname,provisional_diagnosis,admission_date,dischargedate,status,cdate from preauth where p_contact='%s'""" % mNo
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            for row in data:
                temDict = {}
                temDict['HospitalID'] = row[0]
                temDict['hospital_name'] = row[1]
                temDict['insname'] = row[2]
                temDict['p_sname'] = row[3]
                temDict['provisional_diagnosis'] = row[4]
                temDict['admission_date'] = row[5]
                temDict['dischargedate'] = row[6]
                temDict['status'] = row[7]
                temDict['cdate'] = row[8]
                mList.append(temDict)
            finalResponse['data'] = mList
            finalResponse['status'] = "success"

        else:
            finalResponse['status'] = 'failed'
            finalResponse["message"] = 'Record does not found in preauth Table with respect to Mobile Number'

    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/HospitalList', methods=['POST'])
def hospitalList():
    conn_data = {'host': "iclaimdev.caq5osti8c47.ap-south-1.rds.amazonaws.com",
                 'user': "admin",
                 'password': "Welcome1!",
                 'database': 'portals'}
    finalResponse = {}
    mList = []
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    conn = None

    try:
        query = """select Hospital_Name,HospitalID from hospital where status='1'"""
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            for row in data:
                temDict = {}
                temDict['Hospital_Name'] = row[0]
                temDict['HospitalID'] = row[1]
                mList.append(temDict)
            finalResponse['data'] = mList
            finalResponse['status'] = "success"

        else:
            finalResponse['status'] = 'failed'
            finalResponse[
                "message"] = 'Hospital_Name,HospitalID Are not present in hospital Table when status equal to 1'

    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/ClaimDeficiency', methods=['POST'])
def claimdeficiency():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    finalResponse = {}
    mList = []
    todate = ''
    fromdate = ''
    hospitalId = ''
    conn = None
    cur = None
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('fromdate') != None:
        fromdate = request.form.get('fromdate')
    if request.form.get('todate') != None:
        todate = request.form.get('todate')
    if request.form.get('hospitalId') != None:
        hospitalId = request.form.get('hospitalId')
    dateformat = '%d/%m/%Y'

    if fromdate != '' and todate != '':
        fromdate = datetime.strptime(fromdate, '%Y-%m-%d').strftime(dateformat)
        todate = datetime.strptime(todate, '%Y-%m-%d').strftime(dateformat)

    try:
        data = None
        if fromdate != '' and todate != '':
            query = """SELECT p.HospitalID,p.PatientID_TreatmentID AS PatientID,p.preauthNo AS PreAuthNo, p.MemberId,p.p_sname AS PatientName,p.admission_date AS AdmissionDate, \
            p.dischargedate AS DischargeDate,p.status AS `Status`,c.PatientID_TreatmentID,p.Total_expected_cost AS ExpectedAmount \
            FROM  preauth p left JOIN claim c ON c.PatientID_TreatmentID = p.PatientID_TreatmentID WHERE \
            p.status IN ('approved' , 'Approved') AND  c.PatientID_TreatmentID is null and STR_TO_DATE(p.admission_date, '%s') between STR_TO_DATE('%s', '%s')\
            and STR_TO_DATE('%s', '%s') AND p.HospitalID='%s'""" % (
            dateformat, fromdate, dateformat, todate, dateformat, hospitalId)
        else:
            query = """SELECT p.HospitalID,p.PatientID_TreatmentID AS PatientID,p.preauthNo AS PreAuthNo, p.MemberId,p.p_sname AS PatientName,p.admission_date AS AdmissionDate, \
            p.dischargedate AS DischargeDate,p.status AS `Status`,c.PatientID_TreatmentID,p.Total_expected_cost AS ExpectedAmount \
            FROM  preauth p left JOIN claim c ON c.PatientID_TreatmentID = p.PatientID_TreatmentID WHERE \
            p.status IN ('approved' , 'Approved') AND  c.PatientID_TreatmentID is null """

        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            for row in data:
                temDict = {}
                temDict['HospitalID'] = row[0]
                temDict['PatientID'] = row[1]
                temDict['PreAuthNo'] = row[2]
                temDict['MemberId'] = row[3]
                temDict['PatientName'] = row[4]
                temDict['admission_date'] = row[5]
                temDict['DischargeDate'] = row[6]
                temDict['Status'] = row[7]
                temDict['PatientID_TreatmentID'] = row[8]
                temDict['ExpectedAmount'] = row[9]
                mList.append(temDict)
            finalResponse['status'] = "success"
            finalResponse['data'] = mList
        else:
            finalResponse['status'] = 'failed'
            finalResponse["message"] = 'Record does not found'

    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)
        # return render_template('exporttable.html',claimdata=finalResponse)


@app.route('/api/SupportNumber', methods=['POST'])
def supportnumber():
    finalResponse = {}
    try:
        conn = mysql.connect()
        cur = conn.cursor()
        finalResponse['status'] = "success"
        finalResponse['mobileNo'] = "9999999999"


    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        conn.commit()
        cur.close()
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/LoadClaimDeficiency', methods=['GET'])
def LoadClaimDeficiency():
    return render_template('exporttable11.html')


@app.route('/api/saveUserToken', methods=['POST'])
def saveUserToken():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    userId = ''
    mNo = ''
    tokenNo = ''
    deviceId = ''
    cdate = ''
    conn = None
    cur = None
    finalResponse = {}
    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )
    if request.form.get('mobileNo') != None:
        mNo = request.form.get('mobileNo')
    if request.form.get('userId') != None:
        userId = request.form.get('userId')
    if request.form.get('deviceId') != None:
        deviceId = request.form.get('deviceId')
    if request.form.get('tokenNo') != None:
        tokenNo = request.form.get('tokenNo')
    if request.form.get('cdate') != None:
        cdate = request.form.get('cdate')

    if mNo == '' and userId == '' and deviceId == '' and tokenNo == '' and cdate == '':
        return jsonify(
            {
                'status': 'failed',
                'message': 'Parameter Field Are Empty'
            }
        )

    try:
        # query=""" select deviceId from device_Token"""
        query = """ select * from device_Token where deviceId='%s' """ % deviceId
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchall()
        if data:
            query = """UPDATE device_Token SET mobileNo ='%s',userId ='%s',tokenNo ='%s',cdate ='%s' \
                where deviceId='%s'""" % (mNo, userId, tokenNo, cdate, deviceId)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()
            finalResponse['status'] = "success"
            finalResponse['message'] = "Update Successfully"

        else:
            query = """insert into device_Token(mobileNo,userId,deviceId,tokenNo,cdate) values ('%s','%s','%s','%s','%s')""" \
                    % (mNo, userId, deviceId, tokenNo, cdate)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                con.commit()
            finalResponse['status'] = "success"
            finalResponse['message'] = "Update Successfully"

    except Exception as e:
        print(e)

        finalResponse['status'] = 'failed'
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()

    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


@app.route('/api/EmailSend', methods=['POST'])
def EmailSend():
    conn_data = get_db_conf(hosp=request.form['hospital_id'])
    ProcessType = ''
    hId = ''
    MemberID = ''
    conn = None
    cur = None
    PatientName = ''
    InsurerID = ''
    Documents = ''
    finalResponse = {}

    if request.method != "POST":
        return jsonify(
            {
                'status': 'failed',
                'message': 'inavlid request method.Only Post method Allowed'
            }
        )

    if request.form.get('ProcessType') != None:
        ProcessType = request.form.get('ProcessType')

    if request.form.get('InsurerID') != None:
        InsurerID = request.form.get('InsurerID')
    if request.form.get('hospital_id') != None:
        hId = request.form.get('hospital_id')

    if request.form.get('MemberID') != None:
        MemberID = request.form.get('MemberID')
    if request.form.get('PatientName') != None:
        PatientName = request.form.get('PatientName')
    fileList = None
    try:
        files = request.files.getlist("Documents")

        fileList = uploadFile(files)
    except Exception as e:
        print(e)
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Something went wrong.Pls try after Some time or contact Support'
        return jsonify(finalResponse)

    if InsurerID == '' or hId == '':
        finalResponse['status'] = "failed"
        finalResponse['message'] = 'Parameter Field Are Empty'
        return jsonify(finalResponse)

    try:
        query = """select InsurerMail,submitvia,HospitalMail,HospitalPass,IncomingHost,IncomingPort,OutgoingHost, \
        OutgoingPort,Type from mail_configration where InsurerID='%s' and HospitalID='%s' """ % (InsurerID, hId)
        print(query)
        with mysql.connector.connect(**conn_data) as con:
            cur = con.cursor()
            cur.execute(query)
            data = cur.fetchone()
        if data:
            submitvia = data[1]
            Type = data[8]
            finalResponse['InsurerMail'] = data[0]
            emailstr = data[0]

            finalResponse['submitvia'] = data[1]
            finalResponse['HospitalMail'] = data[2]
            finalResponse['HospitalPass'] = data[3]
            finalResponse['IncomingHost'] = data[4]
            finalResponse['IncomingPort'] = data[5]
            finalResponse['OutgoingHost'] = data[6]
            finalResponse['OutgoingPort'] = data[7]
            finalResponse['Type'] = data[8]

            query = """select mail_template from mail_template where HospitalID='%s'""" % (hId)
            print(query)
            with mysql.connector.connect(**conn_data) as con:
                cur = con.cursor()
                cur.execute(query)
                data = cur.fetchone()
            if data:
                mailTemplate = data[0]

                if Type == 'Gmail':
                    recepientList = []
                    subject = None
                    if ProcessType == 'PA':
                        subject = 'PreAuth Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    elif ProcessType == 'EN':
                        subject = 'Enhancement Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    elif ProcessType == 'FB':
                        subject = 'Discharge Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    elif ProcessType == 'NU':
                        subject = 'Non-Utilization Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    msg = mailTemplate
                    if submitvia == 'portalsubmit':
                        print("gmail hi")
                        gmailSender = GMAIL_SENDER()
                        gmailSender.readEmailConfig()
                        # recepientList=["ashishkatariya19@gmail.com","ashish1613068@akgec.ac.in","ashishkatariya19@outlook.com","maneesh@vnusoftware.com"]
                        recepientList.append("claim.vnusoftware.com@gmail.com")
                        gmailSender.send_email(subject, msg, fileList, recepientList)

                    elif submitvia == 'emailsubmit':
                        print("gmail hello")

                        if emailstr is not None and emailstr.find(",") != -1:
                            recepientList = emailstr.split(',')
                        else:
                            recepientList.append(emailstr)
                        gmailSender = GMAIL_SENDER()
                        gmailSender.readEmailConfig()
                        # recepientList=["ashishkatariya19@gmail.com","ashish1613068@akgec.ac.in","ashishkatariya19@outlook.com"]

                        gmailSender.send_email(subject, msg, fileList, recepientList)



                elif Type == 'Outlook':
                    recepientList = []
                    subject = None
                    if ProcessType == 'PA':
                        subject = 'PreAuth Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    elif ProcessType == 'EN':
                        subject = 'Enhancement Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    elif ProcessType == 'FB':
                        subject = 'Discharge Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    elif ProcessType == 'NU':
                        subject = 'Non-Utilization Request for Patient Name <<%s>>: <<%s>>' % (PatientName, MemberID)
                    msg = mailTemplate

                    if submitvia == 'portalsubmit':
                        print("outlook hi")
                        outlookSender = OUTLOOK_SENDER()
                        outlookSender.readEmailConfig()
                        recepientList.append("claim.vnusoftware.com@gmail.com")
                        outlookSender.send_email(subject, msg, fileList, recepientList)

                    elif submitvia == 'emailsubmit':
                        print("outlook hello")
                        if emailstr is not None and emailstr.find(",") != -1:
                            recepientList = emailstr.split(',')
                        else:
                            recepientList.append(emailstr)
                        outlookSender = OUTLOOK_SENDER()
                        outlookSender.readEmailConfig()
                        # recepientList=["ashishkatariya19@gmail.com","ashish1613068@akgec.ac.in","ashishkatariya19@outlook.com"]

                        outlookSender.send_email(subject, msg, fileList, recepientList)


        else:
            finalResponse['status'] = "failed"
            finalResponse[
                'message'] = 'Record does not found in mail_configration table with respect to InsurerID And HospitalID'
    except Exception as e:
        print(e)
        finalResponse['status'] = 'failed',
        finalResponse["message"] = 'Something went wrong.Pls try after Some time or contact Support'
        finalResponse['reason'] = e.__str__()
    finally:
        print("Connection has been closed successfuilly")
        return jsonify(finalResponse)


if __name__ == '__main__':
    # app.run(threaded=True)
    app.run(host="0.0.0.0", port=9982)
    # app.run()
