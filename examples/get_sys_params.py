from pprint import pprint
from epifpm.zfm20 import Fingerprint

with Fingerprint() as f:
    pprint(f.get_system_parameters())
