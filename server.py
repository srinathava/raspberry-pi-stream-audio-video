from twisted.internet import reactor, protocol, defer
from twisted.web import server, resource
from twisted.web.static import File
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver

import io
import re
from datetime import datetime

import Image
import ImageOps
import ImageFilter
import ImageChops

from MotionStateMachine import MotionStateMachine

class MJpegResource(resource.Resource):
    def __init__(self, queues):
        self.queues = queues

    @defer.inlineCallbacks
    def deferredRenderer(self, request):
        q = defer.DeferredQueue()
        self.queues.append(q)
        while True:
            data = yield q.get()
            request.write(data)

    def render_GET(self, request):
        request.setHeader("content-type", 'multipart/x-mixed-replace; boundary=--spionisto')
        self.deferredRenderer(request)
        return server.NOT_DONE_YET

class JpegStreamReader(protocol.Protocol):
    def connectionMade(self):
        print 'Image stream received'

    def dataReceived(self, data):
        for queue in self.factory.queues:
            queue.put(data)

class MotionDetectionStatusReaderProtocol(protocol.ProcessProtocol):
    PAT_STATUS = re.compile(r'(\d) (\d)')
    def __init__(self):
        self.data = ''
        self.motionDetected = False
        self.motionSustained = False

    def outReceived(self, data):
        self.data += data
        lines = self.data.split('\n')
        if len(lines) > 1:
            line = lines[-2]
            if self.PAT_STATUS.match(line):
                (self.motionDetected, self.motionSustained) = [int(word) for word in line.split()]

        self.data = lines[-1]

class OximeterReadProtocol(LineReceiver):
    PAT_LINE = re.compile(r'(?P<time>\d\d/\d\d/\d\d \d\d:\d\d:\d\d).*SPO2=(?P<SPO2>\d+).*BPM=(?P<BPM>\d+).*ALARM=(?P<alarm>\S+).*')

    def __init__(self):
        self.SPO2 = -1
        self.BPM = -1
        self.alarm = -1
        self.readTime = datetime.min
        self.motionDetected = False
        self.motionSustained = False
        self.setLineMode()

        self.alarmStateMachine = MotionStateMachine()
        self.alarmStateMachine.CALM_TIME = 0
        self.alarmStateMachine.SUSTAINED_TIME = 20

        self.motionStateMachine = MotionStateMachine()
        self.motionStateMachine.CALM_TIME = 100
        self.motionStateMachine.SUSTAINED_TIME  = 10

    def lineReceived(self, line):
        m = self.PAT_LINE.match(line)
        if m:
            self.SPO2 = int(m.group('SPO2'))
            self.BPM = int(m.group('BPM'))
            self.readTime = dateutil.parser.parse(m.group('time'))

            self.alarmStateMachine.step(self.SPO2 <= 94)
            self.alarm = int(m.group('alarm'), base=16) or self.alarmStateMachine.inSustainedMotion()

            self.motionDetected = (self.BPM >= 140)
            self.motionStateMachine.step(self.motionDetected)
            self.motionSustained = self.motionStateMachine.inSustainedMotion()

class StatusResource(resource.Resource):
    def __init__(self, motionDetectorStatusReader, oximeterReader):
        self.motionDetectorStatusReader = motionDetectorStatusReader
        self.oximeterReader = oximeterReader

    def render_GET(self, request):
        request.setHeader("content-type", 'application/json')

        status = {
                'SPO2': self.oximeterReader.SPO2,
                'BPM': self.oximeterReader.BPM,
                'alarm': bool(self.oximeter.alarm),
                'motion': int(self.motionDetectorStatusReader.motionSustained or self.oximeterReader.motionSustained),
                'readTime': self.oximeter.readTime.isoformat()
                }
        return json.dumps(status)

def startServer():
    queues = []

    oximeterReader = OximeterReadProtocol()
    try:
        SerialPort(oximeterReader, '/dev/ttyUSB0', reactor, timeout=3)
    except:
        pass

    motionDetectorStatusReader = MotionDetectionStatusReaderProtocol()
    reactor.spawnProcess(motionDetectorStatusReader, 'python', ['python', 'motion_server.py'])

    factory = protocol.Factory()
    factory.protocol = JpegStreamReader
    factory.queues = queues
    reactor.listenTCP(9999, factory)

    root = File('.')
    root.putChild('stream.mjpeg', MJpegResource(queues))
    root.putChild('status', StatusResource(motionDetectorStatusReader, oximeterReader))

    site = server.Site(root)
    reactor.listenTCP(8080, site)

    reactor.run()

if __name__ == "__main__":
    startServer()
