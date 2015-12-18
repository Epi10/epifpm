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
PACKAGE_UP_CHAR = 0x08
PACKAGE_GET_SYS_PARS = 0x0f

PACKAGE_DOWN_IMAGE = 0x0B

PACKAGE_COMMAND = 0x01
PACKAGE_DATA = 0x02
PACKAGE_ACK = 0x07
PACKAGE_END_OF_DATA = 0x08

FINGERPRINT_OK = 0x00
FINGERPRINT_NOFINGER = 0x02
FINGERPRINT_ENROLLMISMATCH = 0x0A

#logging.basicConfig(level=logging.DEBUG)
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

    def write(self, instruction_code, data, identifier=PACKAGE_COMMAND):

        size = len(data) + 3

        packet_size = list(divmod(size, 256))

        checksum = identifier + sum(packet_size) + (instruction_code or 0) + sum(data)

        checksum = list(divmod(checksum, 256))

        buffer = map(
            lambda x: chr(x),
            HEADER + self.address + [identifier] + packet_size + filter(None, [instruction_code]) + data + checksum
        )

        self.last_write_package = buffer
        logger.debug('write package: %s' % repr(buffer))
        self.serial.write(''.join(buffer))

    def read(self):
        header = self.serial.read(2)
        addr = self.serial.read(4)
        pi = ord(self.serial.read(1))
        length = self.serial.read(2)

        ilen = sum([ord(i) for i in length])
        edata=self.serial.read(ilen-2)
        resp = {'identifier': pi}

        if pi == 0x07:
            resp['confirmation_code'] = ord(edata[0])
            edata = edata[1:]

        resp['extra_data'] = edata

        csum = self.serial.read(2)

        self.last_read_package = [header, addr, pi, length, resp.get('confirmation_code'), edata, csum]

        logger.debug('read package: %s' % self.last_read_package)
        logger.debug('return read dict: %s' % resp)
        return resp

    def handshake(self):
        self.write(instruction_code=PACKAGE_HANDSHAKE, data=[0])
        return self.read()

    def get_system_parameters(self):
        self.write(instruction_code=PACKAGE_GET_SYS_PARS, data=[])
        ret = self.read()

        ret['Status register'] = ret['extra_data'][0:0+1]
        ret['System identifier code'] = ret['extra_data'][1:1+1]
        ret['Finger library size'] = ret['extra_data'][2:2+1]
        ret['Security level'] = ret['extra_data'][3:3+1]
        ret['Device address'] = ret['extra_data'][4:4+2]
        ret['Data packet size'] = ord(ret['extra_data'][6:6+1])
        ret['Baud settings'] = ret['extra_data'][7:7+1]

        return ret


    def empty(self):
        self.write(instruction_code=PACKAGE_EMPTY, data=[])
        print self.read()

    def get_image(self):
        """Get a single read from the sensor looking for a fingerprint and load it into a "ImageBuffer" if successful"""
        self.write(instruction_code=PACKAGE_GETIMAGE, data=[])
        return self.read()

    def get_image_until(self, condition=FINGERPRINT_OK):
        """ Will continuously lookup for a fingerprint from the sensor until a condition """
        r = self.get_image()
        while r.get('confirmation_code') != condition:
            r = self.get_image()
        return r

    def up_image(self, fo=None):
        """ Get Image src from ImageBuffer """
        logger.info('UPLOAD IMAGE')
        self.write(instruction_code=PACKAGE_UP_IMAGE, data=[])
        resp = self.read()
        resp['image'] = StringIO()
        r = {'identifier': 0x00}

        r = self.read()
        while r['identifier'] != 0x08:
            resp['image'].write(r['extra_data'])
            logger.debug("get %s bytes" % len(r['extra_data']))
            if fo:
                fo.write(r['extra_data'])

            r = self.read()

        resp['image'].write(r['extra_data'])

        resp['image'].seek(0)

        return resp

    def down_image(self, fo, chunks=128):
        """ Not finish """
        logger.info('DOWNLOAD IMAGE')
        self.write(instruction_code=PACKAGE_DOWN_IMAGE, data=[])
        rdata = []
        data = fo.read(chunks)
        while data:
            rdata.append(map(ord, data))
            data = fo.read(chunks)

        for idata in rdata[:-1]:
            self.write(instruction_code=None, data=idata, identifier=PACKAGE_DATA)
        self.write(instruction_code=None, data=rdata[-1], identifier=PACKAGE_END_OF_DATA)

    #def up_char(self, fo, buffer, chunks=128):
    #    logger.info('uploading char')
    #    self.write(instruction_code=PACKAGE_UP_CHAR, data=[buffer])
    #    # add read sequence


    def image_2_tz(self, buffer):
        self.write(instruction_code=PACKAGE_IMAGE2TZ, data=[buffer])
        return self.read()

    def up_char(self, buffer, fo=None):
        self.write(instruction_code=PACKAGE_UP_CHAR, data=[buffer])
        resp = self.read()
        resp['char'] = StringIO()
        r = {'identifier': 0x00}

        while r['identifier'] != 0x08:
            r = self.read()
            resp['char'].write(r['extra_data'])
            if fo: fo.write(r['extra_data'])

        resp['char'].seek(0)

        return resp

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
        f.get_image_until()
        f.image_2_tz(buffer=1)


        print "remove your finger"
        f.get_image_until(condition=FINGERPRINT_NOFINGER)

        print "place finger again"
        f.get_image_until()

        f.image_2_tz(buffer=2)

        model = f.register_model()
        if model['confirmation_code'] != FINGERPRINT_OK:
            raise Exception("No Match")

        print f.store_model(id=id, buffer=1)


def validate_finger():
    with Fingerprint() as f:
        print "place finger"
        f.get_image_until()
        print f.image_2_tz(0x01)
        print f.search(buffer=0x01)

if __name__ == '__main__':
    with Fingerprint() as f:
        f.handshake()
        f.empty()
        image = f.get_image_until()

        print image
