import sys
import getopt

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
        self.sackMode=sackMode
        self.sack_elements=set()
        self.sack_seq_number=-1

    # Main sending loop.
    def start(self):
        seqno = 0
        data = self.infile.read(self.datasize)
        self.queue.append((seqno, data))
        while not self.shutdown:
            if seqno is 0:
                self.transmit_packet('start',seqno,data)
                response = self.receive(0.5)
                if response is None:
                    self.handle_timeout()
                elif Checksum.validate_checksum(response):
                    if(self.sackMode):
                        msg_type, seqno_sack, data, checksum =\
                          self.split_packet(response)
                        r_seqno,sack=seqno_sack.split(';')
                    else:
                        msg_type, r_seqno, data, checksum =\
                        self.split_packet(response)
                        sack=""
                    self.handle_sack(sack, int(r_seqno))
                    self.handle_new_ack(int(r_seqno))
                    seqno += 1
                    data = self.infile.read(self.datasize)
                    type = 'data'

            elif len(self.queue) < self.window and not self.finished:
                next_data = self.infile.read(self.datasize)
                if len(next_data) is 0:
                    self.finished = True
                    type = 'end'
                    self.end_seqno = seqno
                self.transmit_packet(type,seqno,data)
                self.queue.append((seqno,data))
                data = next_data
                seqno += 1

            else:
                response = self.receive(0.5)
                if response is None:
                    self.handle_timeout()
                else:
                    if Checksum.validate_checksum(response):
                         
                        if(self.sackMode):
                            r_msg_type, seqno_sack, r_data, r_checksum =\
                            self.split_packet(response)
                            r_seqno,sack=seqno_sack.split(';')
                        else:
                            r_msg_type, r_seqno, r_data, r_checksum =\
                            self.split_packet(response)
                            sack=""
                        seqnum = int(r_seqno)
                        self.handle_sack(sack,seqnum)
                        if seqnum is self.queue[0][0]:
                            self.handle_dup_ack(seqnum)
                        else:
                            self.handle_new_ack(seqnum)
        self.infile.close()

    def handle_sack(self, sack, seqnum):
        elements=sack.split(',')
        if seqnum>self.sack_seq_number:
            self.sack_elements=elements
            self.sack_seq_number=seqnum
        elif(seqnum==self.sack_seq_number):
            self.sack_elements=set(elements+list(self.sack_elements))

        self.sack_elements=filter(None, self.sack_elements)

    def handle_timeout(self):
        if not self.shutdown and self.queue:
            self.transmit_packet('data',self.queue[0][0],self.queue[0][1])
            self.send_selective_packets()

    def handle_new_ack(self, seqno):
        if self.end_seqno + 1 == seqno:
            self.shutdown = True
        while (len(self.queue) > 0 and seqno > self.queue[0][0]):
            self.queue.popleft()
        self.dup_count = 0
    
    def handle_dup_ack(self, seqno):
        self.dup_count += 1
        if self.dup_count >= self.dup_max:
            self.transmit_packet('data',seqno,self.queue[0][1])
            self.send_selective_packets()
            self.dup_count = 0

    def transmit_packet(self, type, seqno, data):
        packet = self.make_packet(type,seqno,data)
        self.send(packet)

    def log(self, msg):
        if self.debug:
            print msg

    def send_selective_packets(self):
        if len(self.sack_elements)==0:
            return

        m=max(self.sack_elements)
        for i in xrange(1,len(self.queue)):
            if self.sackMode and self.queue[i][0] not in self.sack_elements and self.queue[i][0]<m:
                self.transmit_packet('data',self.queue[i][0],self.queue[i][1])
        self.sack_elements=[]

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
