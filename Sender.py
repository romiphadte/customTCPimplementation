import sys
import getopt

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.window = 5
        if sackMode:
            raise NotImplementedError #remove this line when you implement SACK

    # Main sending loop.
    def start(self):
        # start packet
        seqno = 0
        data = self.infile.read(1400)
        start_msg = "start|%s|%s|" % (seqno,data)
        checksum = generate_checksum(start_msg)
        start_msg += checksum
        packet = self.make_packet('start',seqno,start_msg)
        self.send(packet)
        response = self.receive(500)
        if response is None:
            self.handle_timeout()
        # send data
        data = self.infile.read(1400)
        finished = False
        type = "data"
        while not finished:
            if in_flight <= window:
                seqno += 1
                next_data = self.infile.read(1400)
                if next_data is "":
                    finished = True
                    type = "end"
                msg = "%s|%s|%s|" % (type,seqno,data)
                checksum = generate_checksum(msg)
                msg += checksum
                packet = self.make_packet(type,seqno,msg)
                seqno += 1
                data = next_data
            else:
                response = self.receive(500)
                if response is None:
                    self.handle_timeout()
                elif self.splitpacket(response) #duplicate
                else: #new ack

        
        

        self.infile.close()

    def handle_timeout(self):
        pass

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

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
