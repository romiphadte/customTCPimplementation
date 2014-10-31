import sys
import getopt
import time

import Checksum
import BasicSender
from collections import deque

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.window = 5
        self.shutdown = False
        self.finished = False
        self.queue = deque()
        self.datasize = 1400
        self.dup_count = 0
        self.dup_max = 3
        self.end_seqno = float("inf")
        if sackMode:
            raise NotImplementedError #remove this line when you implement SACK

    # Main sending loop.
    def start(self):
        # start packet
        seqno = 0
        data = self.infile.read(self.datasize)
        self.transmit_packet('start',seqno,data)
        self.queue.append((seqno, data))
        response = self.receive(500)
        if response is None:
            self.handle_timeout()
        else:
            msg_type, seqnum, data, checksum = self.split_packet(response)
            self.handle_new_ack(int(seqnum))
        # send data
        data = self.infile.read(self.datasize)
        type = "data"
        while not self.shutdown:
            time.sleep(1)
            # send as much as possible
            if len(self.queue) < self.window and not self.finished:
                seqno += 1
                next_data = self.infile.read(self.datasize)
                print "next_data: %s" % (next_data)
                if len(next_data) is 0:
                    self.finished = True
                    type = 'end'
                    self.end_seqno = seqno
                self.transmit_packet(type,seqno,data)
                self.queue.append((seqno,data))
                data = next_data
            # then wait for responses
            else:
                response = self.receive(500)
                if response is None:
                    print "receive: None"
                    self.handle_timeout()
                else:
                    msg_type, seqnum, data, checksum = self.split_packet(response)
                    seqnum = int(seqnum)
                    print "receive: %s %s" % (msg_type,seqnum)
                    #TODO validate checksum
                    if seqnum is self.queue[0][0]: #if seqno is first element in queue, then received ack > seqno but still waiting for seqno
                        self.handle_dup_ack(int(seqnum))
                    else:
                        self.handle_new_ack(int(seqnum))
        print "closing infile"
        self.infile.close()

    def handle_timeout(self):
        print "timeout: resend %s" % (self.queue[0][0])
        self.transmit_packet('data',self.queue[0][0],self.queue[0][1])

    def handle_new_ack(self, seqno):
        if self.end_seqno + 1 is seqno:
            self.shutdown = True
        seqnum = self.queue.popleft()[0]
        print "popping seqno: %s" % (seqnum)
        while (seqno > seqnum + 1):
            if isinstance(seqno, basestring):
                print "string"
            else:
                print "int"
            if isinstance(seqnum, basestring):
                print "string"
            else:
                print "int"
            seqnum = self.queue.popleft()[0]
            print "popping seqno: %s because seqno %s > seqnum %s" % (seqnum,seqno,seqnum)
        print "done with ack %s" % (seqno)
    
    def handle_dup_ack(self, seqno):
        self.dup_count += 1
        if self.dup_count >= self.dup_max:
            self.transmit_packet('data',seqno,self.queue[0][1])
            self.dup_count = 0

    def transmit_packet(self, type, seqno, data):
        print "send:%s %s" % (type,seqno)
        msg = "%s|%s|%s|" % (type,seqno,data)
        checksum = Checksum.generate_checksum(msg)
        msg += checksum
        packet = self.make_packet(type,seqno,msg)
        self.send(packet)

    def log(self, msg):
        if self.debug:
            print msg


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"
        print "-k | --sack Enable selective acknowledgement mode"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 :
