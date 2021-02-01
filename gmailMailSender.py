
import smtplib
from os.path import dirname,abspath
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase

class GMAIL_SENDER:
    def __init__(self):
        self.credential ={}
            
    def readEmailConfig(self):
        with open ( dirname ( abspath ( __file__ ) ) + "/emailconfig.json" ) as json_data_file :
            data = json.load ( json_data_file )
            for key in data.keys ( ) :
                if key == 'GMAIL':
                    values = data[key]
                    self.credential[key] = values
        
    def send_email(self,subject, body,fileList, rList):
        try:
            print("Inside Send_email[GMAIL]")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.credential["GMAIL"]["EMAIL_ADDRESS"]
            
            body1 = MIMEText(body, 'html')
            msg.attach(body1)
            
            for file in fileList:
                image=open(file['filepath'],'rb')
                p = MIMEBase('application', 'octet-stream') 
    
                p.set_payload(image.read()) 
               
                encoders.encode_base64(p) 
                
                p.add_header('Content-Disposition', "attachment; filename= %s" % file['fileName']) 
                
                msg.attach(p) 
             
            
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(self.credential["GMAIL"]["EMAIL_ADDRESS"], self.credential["GMAIL"]["PASSWORD"])
           
            server.sendmail(self.credential["GMAIL"]["EMAIL_ADDRESS"],rList, msg.as_string())
            server.quit()
            print("Success: Email sent!")
        except:
            print("Email failed to send.")

# subject = "Test subject"
# body =  """\

#     <p>Hi!<br>
#        Ashish?<br>
#        Here is the <a href="http://www.python.org">link</a> you wanted.
#     </p>
# """
# mList=["ashishkatariya19@gmail.com","ashish1613068@akgec.ac.in","ashishkatariya19@outlook.com"]

# gmailSender=GMAIL_SENDER()
# gmailSender.readEmailConfig()
# gmailSender.send_email(subject,body,mList)


