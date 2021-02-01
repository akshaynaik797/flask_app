from twilio.rest import Client
import random 
import string 

class OtpGenerator:

    def __init__(self):
        self.account_sid = 'AC9490df28adc36c37931cc674aa96f6fb'
        self.auth_token = '005739625baf94955b403121cfd14ada'

    def generateOTP(self,size): 
        # generate_pass = ''.join([random.choice( string.digits+
        #                                         string.ascii_uppercase +
        #                                         string.ascii_lowercase 
        #                                         ) 
        #                                         for n in range(size)]) 

        generate_pass = ''.join([random.choice( string.digits) for n in range(size)]) 
                                
        return generate_pass 

    def sendOTP(self,mobileNo):

        otp = self.generateOTP(4)
        print(otp) 
        client = Client(self.account_sid, self.auth_token)
        otpcode=otp+" is your VNU Login verification code.Enjoy"
        message = client.messages \
                        .create(
                            body=otpcode,
                            from_='+12564641403',
                            to='+91'+str(mobileNo)
                        )

        print(message.sid)
        return otp


# otpgen=OtpGenerator()
# otpgen.sendOTP(7042533620)