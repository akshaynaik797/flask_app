import smtplib
from os.path import dirname,abspath
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase


class OUTLOOK_SENDER:
    def __init__(self):
        self.credential ={}
            
    def readEmailConfig(self):
        with open ( dirname ( abspath ( __file__ ) ) + "/emailconfig.json" ) as json_data_file :
            data = json.load ( json_data_file )
            for key in data.keys ( ) :
                if key == 'OUTLOOK':
                    values = data[key]
                    self.credential[key] = values
        


    # def send_email(self,subject, msg, mList):
    #     try:
    #         server = smtplib.SMTP('smtp.office365.com', port=587)
    #         server.ehlo()
    #         server.starttls()
    #         server.login(self.credential["OUTLOOK"]["EMAIL_ADDRESS"], self.credential["OUTLOOK"]["PASSWORD"])
    #         message = 'Subject: {}\n\n{}'.format(subject, msg)
    #         server.sendmail(self.credential["OUTLOOK"]["EMAIL_ADDRESS"],mList, message)
    #         server.quit()
    #         print("Success: Email sent!")
    #     except:
    #         print("Email failed to send.")
    
    def send_email(self,subject, body,fileList, rList):
        try:
            print("Inside Send_email[OUTLOOK]")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.credential["OUTLOOK"]["EMAIL_ADDRESS"]
            
            body1 = MIMEText(body, 'html')
            msg.attach(body1)
            
            for file in fileList:
                image=open(file['filepath'],'rb')
                p = MIMEBase('application', 'octet-stream') 
    
                p.set_payload(image.read()) 
                
                encoders.encode_base64(p) 
                
                p.add_header('Content-Disposition', "attachment; filename= %s" % file['fileName']) 
                
                msg.attach(p) 
             
            
            server = smtplib.SMTP('smtp.office365.com', port=587)
            server.ehlo()
            server.starttls()
            server.login(self.credential["OUTLOOK"]["EMAIL_ADDRESS"], self.credential["OUTLOOK"]["PASSWORD"])
            server.sendmail(self.credential["OUTLOOK"]["EMAIL_ADDRESS"],rList, msg.as_string())
            server.quit()
            print("Success: Email sent!")
        except:
            print("Email failed to send.")

# subject = "Test subject"
# msg = "Hello there, how are you today?"
# mList=["ashishkatariya19@gmail.com","ashish1613068@akgec.ac.in","ashishkatariya19@outlook.com","maneesh@vnusoftware.com"]

# send_email(subject, msg, mList)