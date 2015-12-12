

from epifpm.zfm20 import Fingerprint, FINGERPRINT_NOFINGER


with Fingerprint() as f:
    f.empty()
    IMG1 = '/tmp/imgae1'
    IMG2 = '/tmp/imgae1'

    print "registering and downloading 1rst image"
    f.get_image_until()
    f.image_2_tz(buffer=1)
    with open(IMG1, 'w') as image1:
        f.up_image(image1)

    f.get_image_until(condition=FINGERPRINT_NOFINGER)

    print "registering and downloading 2nd image"
    f.get_image_until()
    f.image_2_tz(buffer=2)
    with open(IMG2, 'w') as image2:
        f.up_image(image2)


    print "storing model and verifing that it works"
    f.store_model(id=1, buffer=1)

    f.get_image_until(condition=FINGERPRINT_NOFINGER)

    f.get_image_until()
    f.image_2_tz(buffer=1)
    print f.search(1)

    f.empty()

    with open(IMG1, 'r') as image1:
        f.down_image(fo=image1)
    f.image_2_tz(buffer=1)

    with open(IMG2, 'r') as image2:
        f.down_image(fo=image2)
    f.image_2_tz(buffer=2)

    print "storing model and verifing that it works"
    f.store_model(id=1, buffer=1)

    f.get_image_until(condition=FINGERPRINT_NOFINGER)

    f.get_image_until()
    f.image_2_tz(buffer=1)
    print f.search(1)












