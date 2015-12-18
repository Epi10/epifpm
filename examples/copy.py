from epifpm.zfm20 import Fingerprint, FINGERPRINT_NOFINGER


import logging

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

f = Fingerprint()
f.connect()


f.empty()


print "get image 1"
f.get_image_until()
f.image_2_tz(buffer=1)
image1 = f.up_image()['image']

print "get image 2"
f.get_image_until()
f.image_2_tz(buffer=2)
image2 = f.up_image()['image']

print "Guardando modelo 1"
f.store_model(id=1, buffer=1)

print "buscando 1"
f.get_image_until()
f.image_2_tz(buffer=1)
print f.search(1)

f.empty()
