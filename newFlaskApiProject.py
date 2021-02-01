from flask import Flask, render_template, request,jsonify
from flask_mysqldb import MySQL
import mysql.connector
from mysql.connector import Error
import json
from os.path import dirname,abspath
from datetime import datetime
app = Flask(__name__)

#
# app.config['MYSQL_HOST'] = "localhost"
# app.config['MYSQL_USER'] = "root"
# app.config['MYSQL_PASSWORD'] = "root123"
# app.config['MYSQL_DB'] = "PatientRecord"
# mysql= MySQL ( app )

dbConfig = {}
with open ( dirname ( abspath ( __file__ ) ) + "/databaseconfig.json" ) as json_data_file :
    data = json.load ( json_data_file )
    for keys in data.keys ( ) :
        values = data[keys]
        dbConfig[keys] = values

app.config['MYSQL_HOST'] = dbConfig["Config"]['MYSQL_HOST']
app.config['MYSQL_USER'] = dbConfig["Config"]['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = dbConfig["Config"]['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = dbConfig["Config"]['MYSQL_DB']
mysql= MySQL ( app )


@app.route('/APIUserLogin', methods=['POST'])
def userLogin():
    data=None
    if request.method=='POST':
        if request.form['mobileNo'] !='':
            mobile_no = request.form['mobileNo']
        # mobile_no=request.args['mobileNo']
            flag='T'
            try :
                cur = mysql.connection.cursor()
                query = """select he_name, he_mobile, status from hospital_employee where he_mobile=%s"""
                cur.execute(query,(mobile_no,))
                data = cur.fetchone()

                if data:
                    print("Data is present in hospital_employee")
                else:
                    flag='P'
                    print('No data in hospital_employee table.Looking into patient_master table')
                    query = """select mobile, name, status from patient_master e where mobile=%s"""
                    # query="""select * FROM incident WHERE Reported_By=%s AND Status=%s """
                    cur.execute ( query , (mobile_no ,) )
                    data = cur.fetchone()
            except Error as E :
                print ( f'Error while fatching {E.__str__ ( )}' )
            finally :
                mysql.connection.commit ( )
                cur.close ( )
                print ( "Connection has been closed successfuilly" )
                finalResponse = {}
                if data :
                    finalResponse['timeStamp'] = str(datetime.now ( ))
                    finalResponse['userType'] = flag
                    finalResponse['status'] = data[2]
                    finalResponse['mobileNo'] = data[1]
                    finalResponse['userName'] = data[0]
                    finalResponse['APIstatus'] = 'successful'
                    print(finalResponse.__str__())
                else:
                    finalResponse['timeStamp'] = str(datetime.now ( ))
                    finalResponse['userType'] = ''
                    finalResponse['status'] = ''
                    finalResponse['mobileNo'] = ''
                    finalResponse['userName'] = ''                
                    finalResponse['APIstatus'] = 'No Data'
                    print ( finalResponse.__str__ ( ) )
                return json.dumps(finalResponse)

    else:
        finalResponse = {}
        finalResponse['timeStamp'] = datetime.now ( )
        finalResponse['userType'] = ''
        finalResponse['status'] = ''
        finalResponse['mobileNo'] = ''
        finalResponse['userName'] = ''
        finalResponse['APIstatus'] = 'Failed'
        print( finalResponse)
        return  json.dumps(finalResponse)



@app.route ( '/APIActiveCases' , methods=['POST'] )
def activeCases () :
    data = None
    if request.method == "POST" :
        if request.form['mobileNo'] != '' :
            mobileNo = request.form['mobileNo']
            finalResponse = {}
            mylist = []
            try :
                cur = mysql.connection.cursor ( )
                query = """select he_hospital_id from hospital_employee where he_mobile=%s"""
                cur.execute ( query , (mobileNo ,) )
                data = cur.fetchone ( )
                if data:
                    hospitalId=data[0]
                    query1="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
                            LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
                            pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID WHERE\
                            STR_TO_DATE(pa.dischargedate, '%d/%m/%Y')>= STR_TO_DATE('07/07/2020', '%d/%m/%Y') AND """
                            
                    query2="""pa.HospitalID='%s' \
                            AND (st.status!='Create Pre-Auth') AND pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND \
                            st.srno = (SELECT MAX(srno) FROM `status_track` WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) \
                            GROUP BY pa.PatientID_TreatmentID UNION ALL select  pa.PatientID_TreatmentID,pa.insname,pa.admission_date,\
                            pa.p_sname,st.status FROM preauth pa LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN \
                            status_track st ON pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON \
                            pa.VNUPatientID=m.VNUPatientID""" % hospitalId
                            
                    query3= """ WHERE STR_TO_DATE(pa.dischargedate, '%d/%m/%Y')>= STR_TO_DATE('07/07/2020', '%d/%m/%Y')\
                            AND """
                    query4= """ pa.HospitalID='%s'""" % hospitalId
                    query5= """ AND (st.status='Create Pre-Auth' AND \
                            STR_TO_DATE(st.cdate, '%d/%m/%Y')>=STR_TO_DATE('06/07/2020', '%d/%m/%Y')) AND \
                            pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM `status_track`\
                            WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID"""
                            
                    query=query1+query2+query3+query4+query5
                    print(query)
                    cur.execute (query)
                    data = cur.fetchall()
                else:
                    finalResponse['count']=len(data)
                    finalResponse['comment']='Mobile No is not present'
                    return json.dumps(finalResponse)
            except Exception as e:
                print (e)
            finally :
                mysql.connection.commit ( )
                cur.close ( )
                print ( "Connection has been closed successfuilly" )
                if data:
                    finalResponse['count']=len(data)
                   
                    for row in data:
                        localResponse={}
                        print(row)
                        localResponse['name']=row[3]
                        localResponse['id']=row[0]
                        localResponse['insure_name']=row[1]
                        localResponse['admission_date']=str(row[2])
                        localResponse['status']=row[4]
                        localResponse['deadline']='NA'
                        mylist.append(localResponse)
                    finalResponse['result']=mylist
                    return json.dumps(finalResponse)
                else:
                    finalResponse['count']=len(data)
                    return json.dumps(finalResponse)
  

@app.route ( '/APIActiveClarification' , methods=['POST'] )
def activeCaseClarification () :
    data = None
    if request.method == "POST" :
        if request.form['mobileNo'] != '' :
            mobileNo = request.form['mobileNo']
            try :
                finalResponse={}
                historyList=[]
                cur = mysql.connection.cursor ( )
                query = """select he_hospital_id from hospital_employee where he_mobile=%s"""
                cur.execute ( query , (mobileNo ,) )
                data = cur.fetchone ( )
                if data:
                    hospitalId=data[0]
                    data=None
                    # query= "select UTR_No, status from settlementutrupdate where HospitalID=%s"
                    # cur.execute(query,(hospitalId,))
                    query= "select UTR_No, status from settlementutrupdate where HospitalID='%s'"% hospitalId
                    print(query)
                    cur.execute(query)
                    data = cur.fetchall()
                    if data:
                        for row in data:
                            utrNo=row[0]
                            status_set=row[1]
                            data1=None
                            query= "select clari_msg, clari_user,status,cdate from clarification_manage where utr_no='%s'" % utrNo
                            cur.execute(query)
                            data1 = cur.fetchall( )
                            if data1:
                                localdic={}
                                for row in data1:

                                    clari_msg=row[0]
                                    clari_user=row[1]
                                    status=row[2]
                                    cdate=str(row[3])
                                    localdic['URT_NO']=utrNo
                                    localdic['status']=status_set
                                    localdic['clari_msg']=clari_msg
                                    localdic['clari_user']=clari_user
                                    localdic['cdate']=cdate
                                    print(row)
                                    historyList.append(localdic)
                                    
                    finalResponse['result']=historyList
                else:
                    print('No record present')

            except Exception as E :
                print ( f'Error while fatching {E.__str__ ( )}' )
            finally :
                mysql.connection.commit ( )
                cur.close ( )
                return json.dumps(finalResponse)


@app.route ( '/APIStatusTrack' , methods=['POST'] )
def statusTrack () :
    data = None
    if request.method == "POST":
        if request.form['patientId'] != '':
            patientId = request.form['patientId']
            try :
                finalResponse={}
                finalResponse['patientId']=patientId
                mList=[]
                cur = mysql.connection.cursor ( )
                query = """select status, cdate , srno , type FROM (`status_track`) WHERE `PatientID_TreatmentID` = '%s'""" % patientId
                query= query+"""ORDER BY STR_TO_DATE(`cdate`, '%d/%m/%Y %H:%i:%s') DESC"""
                cur.execute(query)
                data = cur.fetchall()
                if data:
                    for row in data:
                        localDic = {}
                        print(row)
                        type1=row[3]
                        srno=row[2]

                        if type1 == 'PreAuth':
                            query="""select Doctype from preauth_document where statustrackid = '%s' AND status = '%s'""" %(srno,type1)
                        else:
                            query="""select Doctype from claim_document where statustrackid = '%s' AND status = '%s'""" %(srno,type1)
                        data1=None
                        cur.execute(query)
                        data1=cur.fetchone()
                        doctype=None
                        if data1:
                            doctype=data1[0]
                            localDic['status']=row[0]
                            localDic['date_time'] = str(row[1])
                            localDic['document'] = doctype
                            mList.append(localDic)

                finalResponse['statusTrack']=mList


            except Exception as E :
                print ( f'Error while fatching {E.__str__ ( )}' )
            finally :
                mysql.connection.commit ( )
                cur.close ( )
                print ( "Connection has been closed successfuilly" )
                return json.dumps(finalResponse)


@app.route('/APIPatientSearch', methods=['POST'])
def patientSearch():
    data=None
    if request.method == "POST":
        patientId=None
        patientName=None
        mobileNumber=None
        if request.form.get('patientId')!= None :
            patientId = request.form['patientId']
        if request.form.get('patientName') != None:
            patientName = request.form['patientName']
        if request.form.get('mobileNumber') != None:
            mobileNumber = request.form['mobileNumber']    
        finalResponse = {}
        mList=[]

        if patientId != None:
            try:
                cur = mysql.connection.cursor ( )
                query="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname, st.status from preauth pa   \
                    left join status_track st on pa.PatientID_TreatmentID=st.PatientID_TreatmentID where pa.PatientID_TreatmentID=%s"""%patientId
                # query2="""select status from status_track where PatientID_TreatmentID='%s'"""%patientId
                print(query)
                cur.execute(query)
                data=cur.fetchall()
                if data !=None:
                    for row in data:
                        print(row)
                        localDic = {}
                        localDic['PatientID'] = row[0]
                        localDic['name'] = row[3]
                        localDic['insurer_name'] = row[1]
                        localDic['admission_date'] = str(row[2])
                        localDic['status'] = row[4]
                        localDic['deadline'] = 'NA'
                        mList.append ( localDic )

                    finalResponse['patients:'] = mList
            except Exception as E:
                print(f'Error while fetching {E.__str__()}')
            finally:
                mysql.connection.commit()
                cur.close()
                return json.dumps(finalResponse)

        elif mobileNumber != None:
            try:
                cur = mysql.connection.cursor ( )
                query="""select he_hospital_id from hospital_employee where he_mobile='%s'"""%mobileNumber
                cur.execute(query)
                data=cur.fetchone()
                if data !=None:

                    hospitalID=data[0]
                    data=None
                    query0="""select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
                    LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
                    pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID \
                    WHERE STR_TO_DATE(pa.dischargedate, '%d/%m/%Y')>= STR_TO_DATE('07/07/2020', '%d/%m/%Y') AND """

                    query1="""pa.HospitalID='%s' AND (st.status!='Create Pre-Auth') AND \
                    pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM \
                    status_track WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID \
                    UNION ALL select pa.PatientID_TreatmentID,pa.insname,pa.admission_date,pa.p_sname,st.status FROM preauth pa \
                    LEFT JOIN claim clm ON pa.VNUPatientID=clm.VNUPatientID LEFT JOIN status_track st ON \
                    pa.PatientID_TreatmentID=st.PatientID_TreatmentID LEFT JOIN master m ON pa.VNUPatientID=m.VNUPatientID """%hospitalID

                    query2="""WHERE STR_TO_DATE(pa.dischargedate, '%d/%m/%Y')>= STR_TO_DATE('07/07/2020', '%d/%m/%Y') """

                    query3="""AND pa.HospitalID='%s' AND (st.status='Create Pre-Auth'AND """%hospitalID

                    query4="""STR_TO_DATE(st.cdate, '%d/%m/%Y')>=STR_TO_DATE('06/07/2020', '%d/%m/%Y')) AND \
                    pa.PatientID_TreatmentID = st.PatientID_TreatmentID AND st.srno = (SELECT MAX(srno) FROM status_track\
                    WHERE PatientID_TreatmentID=pa.PatientID_TreatmentID) GROUP BY pa.PatientID_TreatmentID """
                    query=query0+query1+query2+query3+query4
                    print(query)
                    cur.execute(query)
                    data=cur.fetchall()
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
                            mList.append ( localDic )

                        finalResponse['patients:'] = mList

            except Exception as E:
                print(f'Error while fetching {E.__str__()}')
            finally:
                mysql.connection.commit()
                cur.close()
                return json.dumps(finalResponse)


@app.route('/APIUserProfile', methods=['POST'])
def userProfile():
    data = None
    if request.method == "POST" :
        if request.args['mobileNo'] != '' :
            mobileNo = request.args['mobileNo']
            try :
                cur = mysql.connection.cursor ( )
                query = """select he_hospital_id from hospital_employee where he_mobile=%s"""
                cur.execute ( query , (mobileNo ,) )
                data = cur.fetchone ( )
            except Error as E:
                print ( f'Error while fatching {E.__str__ ( )}' )
            finally :
                mysql.connection.commit ( )
                cur.close ( )
                print ( "Connection has been closed successfuilly" )
                return "success"



@app.route('/APIincident', methods=['POST'])
def incident():
    data = None
    finalResponse={}
    mList=[]
    if request.method == "POST" :
        if request.form.get('mobileNo') != None :
            mobileNo = request.form.get('mobileNo')
            try :
                cur = mysql.connection.cursor ( )
                query = """select he_hospital_id from hospital_employee where he_mobile=%s"""
                cur.execute ( query , (mobileNo ,) )
                data = cur.fetchone()
                if data:
                    hospitalId=data[0]
                    data=None
                    query="""select srno,tracking_no, Short_Description ,Urgency, Status, Created_TimeStamps from incident where Reported_By='%s'"""% hospitalId
                    cur.execute ( query )
                    data = cur.fetchall()
                    if data:
                        for row in data:
                            srno=row[0]
                            localDict={}
                            localDict['tracking_no']=row[1]
                            localDict['shortDesc']=row[2]
                            localDict['urgency']=row[3]
                            localDict['status']=row[4]
                            localDict['timestamp']=str(row[5])
                            # finalResponse['incident']=localDict

                            query = """select senderId,message from incident_comment  where srno=%s""" % srno

                            cur.execute ( query )
                            cur.execute ( query )
                            data1=None
                            data1 = cur.fetchall ( )
                            if data1 :
                                mList1=[]
                                for row1 in data:
                                    localDict1={}
                                    localDict1['senderId']=row[0]
                                    localDict1['message']=row[1]
                                    mList1.append(localDict1)
                                localDict['log']=mList1
                            mList.append(localDict)
                        finalResponse['incident']=mList
                            
            except Exception as E:
                print ( f'Error while fatching {E.__str__ ( )}' )
            finally :
                mysql.connection.commit ( )
                cur.close ( )
                print ( "Connection has been closed successfuilly" )
                return json.dumps(finalResponse)






if __name__ == '__main__':

    app.run(host="0.0.0.0",port=8000)