__author__ = 'aleivag'

import logging
import serial
from cStringIO import StringIO

HEADER = [0xEF, 0x01]

PACKAGE_HANDSHAKE = 0x17 #: To greet (and posible ping) the fingerprint
PACKAGE_EMPTY = 0x0d
PACKAGE_GETIMAGE = 0x01
PACKAGE_IMAGE2TZ = 0x02
PACKAGE_REGMODEL = 0x05
PACKAGE_RANDOM = 0x14
PACKAGE_STORE = 0x06
PACKAGE_MATCH = 0x03
PACKAGE_SEARCH = 0x04
PACKAGE_TEMPLATE_NUM = 0x1d
PACKAGE_UP_IMAGE = 0x0A

FINGERPRINT_OK = 0x00
FINGERPRINT_NOFINGER = 0x02
FINGERPRINT_ENROLLMISMATCH = 0x0A

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Fingerprint(object):
    def __init__(self, port='/dev/ttyAMA0', baudrate=57600, timeout=2):

        self.password = 0
        self.address = [0xFF, 0xFF, 0xFF, 0xFF]

        self.serial = None
        self.port = port
        self.baudrate=baudrate
        self.timeout=timeout

    def connect(self):
        self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def close(self):
        self.serial.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, instruction_code, data):

        size = len(data) + 3

        packet_size = list(divmod(size, 256))

        checksum = 0x01 + sum(packet_size) + instruction_code + sum(data)

        checksum = list(divmod(checksum, 256))

        buffer = map(
            lambda x: chr(x),
            HEADER + self.address + [0x01] + packet_size + [instruction_code] + data + checksum
        )

        self.last_write_package = buffer
        logger.debug('write package: %s' % repr(buffer))
        #print "==>", buffer
        self.serial.write(''.join(buffer))

    def read(self):
        header = self.serial.read(2)
        addr = self.serial.read(4)
        pi = self.serial.read(1)
        length = self.serial.read(2)
        confirmation_code = self.serial.read(1)
        ilen = sum([ord(i) for i in length])
        edata=''

        if ilen>3:
            edata=self.serial.read(ilen-3)

        csum = self.serial.read(2)

        self.last_read_package = [header, addr, pi, length, confirmation_code, edata, csum]

        logger.debug('read package: %s' % self.last_read_package)
        return dict(
            confirmation_code=ord(confirmation_code),
            extra_data=edata
        )

    def handshake(self):
        self.write(instruction_code=PACKAGE_HANDSHAKE, data=[0])
        print self.read()

    def empty(self):
        self.write(instruction_code=PACKAGE_EMPTY, data=[])
        print self.read()

    def get_image(self):
        self.write(instruction_code=PACKAGE_GETIMAGE, data=[])
        return self.read()

    def up_image(self):
        logger.info('UPLOAD IMAGE')
        self.write(instruction_code=PACKAGE_UP_IMAGE, data=[])
        resp = self.read()
        resp['image'] = StringIO()
        for i in xrange(288):
            r = self.serial.read(256/2)
            logger.debug('   => %s ' % [r])
            resp['image'].write(r)
        resp['image'].seek(0)

        return resp


    def image_2_tz(self, buffer):
        self.write(instruction_code=PACKAGE_IMAGE2TZ, data=[buffer])
        return self.read()

    def match(self):
        self.write(instruction_code=PACKAGE_MATCH, data=[])
        resp = self.read()
        resp['score'] = sum(map(ord, resp['extra_data']))
        return resp

    def register_model(self):
        self.write(instruction_code=PACKAGE_REGMODEL, data=[])
        return self.read()

    def store_model(self, id, buffer=0x01):
        self.write(instruction_code=PACKAGE_STORE, data=[buffer] + list(divmod(id, 255)))
        return self.read()

    def template_number(self):
        self.write(instruction_code=PACKAGE_TEMPLATE_NUM, data=[])
        resp = self.read()
        resp['number'] = sum(map(ord, resp['extra_data']))
        return resp

    def get_random_code(self):
        self.write(instruction_code=PACKAGE_RANDOM, data=[])
        resp = self.read()
        resp['random'] = sum(map(ord, resp['extra_data']))
        return resp

    def search(self, buffer, start_page=0, page_num=0x00a3):
        self.write(instruction_code=PACKAGE_SEARCH, data=[buffer] + list(divmod(start_page, 255)) + list(divmod(page_num, 255)))
        resp = self.read()

        resp['page_id'] = sum(map(ord, resp['extra_data'][:2]))
        resp['score'] = sum(map(ord, resp['extra_data'][2:]))

        if resp['confirmation_code'] == 0:
            resp['confirmation_desc'] = 'OK'
        elif resp['confirmation_code'] == 9:
            resp['desc'] = "No matching in the library (both the PageID and matching score are 0)"

        return resp


def register_finger(id):
    with Fingerprint() as f:

        print "place finger"
        while f.get_image().get('confirmation_code') != FINGERPRINT_OK: pass
        f.image_2_tz(buffer=1)

        print "remove your finger"
        while f.get_image().get('confirmation_code') != FINGERPRINT_NOFINGER: pass

        print "place finger again"
        while f.get_image().get('confirmation_code') != FINGERPRINT_OK: pass

        f.image_2_tz(buffer=2)

        model = f.register_model()
        if model['confirmation_code'] != FINGERPRINT_OK:
            raise Exception("No Match")

        print f.store_model(id=id, buffer=1)

def validate_finger():
    with Fingerprint() as f:
        print "place finger"
        while f.get_image().get('confirmation_code') != FINGERPRINT_OK:
            pass
        print f.image_2_tz(0x01)
        print f.search(buffer=0x01)

if __name__ == '__main__':
    with Fingerprint() as f:
        f.handshake()
        f.empty()
        while f.get_image().get('confirmation_code') != FINGERPRINT_OK:pass
        f.up_image()


