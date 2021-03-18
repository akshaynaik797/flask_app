a = '24/02/2021 14:41:48'
from datetime import datetime
b = datetime.strptime(a, '%d/%m/%Y %H:%M:%S')
pass