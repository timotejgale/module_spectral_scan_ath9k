import os
import sys
import time
import logging
import random
import wishful_upis as upis
import wishful_framework as wishful_module
import queue
import numpy as np
import threading
import warnings
import subprocess
from itertools import islice


@wishful_module.build_module
class SpectralScanUsrpModule(wishful_module.AgentModule):
    def __init__(self):
        super(SpectralScanUsrpModule, self).__init__()

        self.log = logging.getLogger('wifi_module.main')
        self.bgd_thread = threading.Thread()
        self.bgd_run = False
        self.bgd_sendq = queue.Queue(maxsize=0)

    def psd_bgd_fun(self):
        print("psd_bgd_fun(): Entering.")

        base_usrp_path = "%s/usrpse" % os.path.dirname(os.path.abspath(__file__))
        scanner_command = "%s/usrpse_sweeping" % base_usrp_path
        uhd_find_command = "%s/uhd_find_devices" % base_usrp_path

        p = subprocess.Popen(uhd_find_command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        if p_status > 0:
            raise RuntimeError("Can't find USRP's IP address.")

        # python uhd library is not used due to its limitations
        try:
            usrp_ip_line = list(filter(lambda x:"addr:" in x, output.decode(sys.stdout.encoding).split("\n")))[0]
            usrp_ip = usrp_ip_line.strip().split(" ")[1]
            usrp_ip_arg = "addr=%s" % usrp_ip
        except:
            raise RuntimeError("Can't find USRP's IP address.")

        args = (scanner_command, "--gain", self.gain, "--spb", self.spb, "--fftsize", self.fftsize,\
                 "--numofchannel", self.numofchannel, "--firstchannel", self.firstchannel,\
                 "--channelwidth", self.channelwidth, "--channeloffset", self.channeloffset,\
                 "--args", usrp_ip_arg, "--bps", self.bps, "--freqbegin", self.freqbegin, "--mode", self.mode)
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        while True:
            psd_iter = iter(lambda: p.stdout.readline(), b'')
            for psd in islice(psd_iter, 40, None): # number of info lines at the beginning
                s_psd = psd.decode(sys.stdout.encoding).strip().split(",")
                print(s_psd)
                self.bgd_sendq.put(s_psd)
                p.stdout.flush()
                if not self.bgd_run:
                    break


    def psd_bgd_start(self):
        print("psd_bgd_start(): Entering.")

        self.bgd_run = True
        self.bgd_thread = threading.Thread(target=self.psd_bgd_fun)
        self.bgd_thread.daemon = True
        self.bgd_thread.start()


    def psd_bgd_stop(self):
        print("psd_bgd_stop(): Entering.")

        if not self.bgd_thread.is_alive():
            warnings.warn('Scanner daemon already stopped.', RuntimeWarning, stacklevel=2)
            return

        # stop background daemon
        self.bgd_run = False
        self.bgd_thread.join()

    @wishful_module.bind_function(upis.radio.scand_start)
    def scand_start(self, iface="eno2", gain="30", spb="4194304", fftsize="1024",\
                     numofchannel="13", firstchannel="2412000000", channelwidth="20000000",\
                     channeloffset="5000000", bps="4", freqbegin="2410000000", mode="2"):
        print("scand_start(): Entering.")

        if self.bgd_thread.is_alive():
            warnings.warn('Scanner daemon already running.', RuntimeWarning, stacklevel=2)
            return

        # drain send queue
        while not self.bgd_sendq.empty():
            self.bgd_sendq.get()

        # set scanning params
        self.iface = iface
        self.gain = gain
        self.spb = spb
        self.fftsize = fftsize
        self.numofchannel = numofchannel
        self.firstchannel = firstchannel
        self.channelwidth = channelwidth
        self.channeloffset = channeloffset
        self.bps = bps
        self.freqbegin = freqbegin
        self.mode = mode

        # start backgound daemon
        self.psd_bgd_start()


    @wishful_module.bind_function(upis.radio.scand_stop)
    def scand_stop(self):
        print("scand_stop(): Entering.")

        # stop backgound daemon
        self.psd_bgd_stop()

        # drain send queue
        while not self.bgd_sendq.empty():
            self.bgd_sendq.get()


    @wishful_module.bind_function(upis.radio.scand_reconf)
    def scand_reconf(self, iface="eno2", gain="30", spb="4194304", fftsize="1024",\
                      numofchannel="13", firstchannel="2412000000", channelwidth="20000000",\
                      channeloffset="5000000", bps="4", freqbegin="2410000000", mode="2"):
        print("scand_reconf(): Entering.")

        # stop backgound daemon
        if self.bgd_thread.is_alive():
            self.psd_bgd_stop()

        # drain send queue
        while not self.bgd_sendq.empty():
            self.bgd_sendq.get()

        # update scanning params
        self.iface = iface
        self.gain = gain
        self.spb = spb
        self.fftsize = fftsize
        self.numofchannel = numofchannel
        self.firstchannel = firstchannel
        self.channelwidth = channelwidth
        self.channeloffset = channeloffset
        self.bps = bps
        self.freqbegin = freqbegin
        self.mode = mode

        # start backgound daemon again
        self.psd_bgd_start()


    @wishful_module.bind_function(upis.radio.scand_read)
    def scand_read(self):
        print("scand_read(): Entering.")

        qsize = self.bgd_sendq.qsize()
        print("scand_read(): Current send queue size: %d." % qsize)

        if (qsize > 0):
            first_psd = self.bgd_sendq.get()
            ret = np.full((qsize, len(first_psd)), (np.nan), dtype=np.int64)
            ret[0, :] = first_psd
            for i in range(1, qsize):
                psd = self.bgd_sendq.get()
                ret[i, :] = psd
        else:
            ret = np.full((0), (np.nan), dtype=np.int64)

        return ret
