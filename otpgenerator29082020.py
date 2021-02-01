import requests
import json
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

    def sendOTP(self,otp,mobileNo):
        url = ' https://api.msg91.com/api/v5/flow/'
        body = {
        "mobiles" : mobileNo,
        "flow_id" : "5f09b7a4d6fc050b9e6dda48",
        "OTP" : otp 
        }
        headers = {
            'Content-ype': 'application/vnd.api+json',
            'authkey':'167826ARvnR1lKl5cee8065'
        }

        r = requests.post(url, data=json.dumps(body), headers=headers)
        response=r.json()
        print(response)
        return otp

# otpgen=OtpGenerator()
# otp=otpgen.generateOTP(4)
# otpgen.sendOTP(otp,'7838928285')