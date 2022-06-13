#!/usr/bin/env python3                                                                                                                                 
import socket
import json
import time
from phoenixminer_rpc.aemet import Aemet
import datetime
from phoenixminer_rpc import config, logger, START_MINER_DELAY, is_debugging, MAX_TEMP
from phoenixminer_rpc.reboot import reboot

#from endesa import punta_convenio

# time for reboot + claymore to get share and start hashing
loop_seconds = 60 * 20  # 20 minutes
loop_seconds = 60 * 10  # 10 minutes
loop_seconds = 10  # 10 seconds


class RigStatus(object):

    def __init__(self, host, port, password):
        self.host = host
        self.password = password
        self.port = port
        self.socket = None
        self.submitted_shares = 0
        self.cards_speed = list()
        self.cards_status = list()
        self.last_speed_change = datetime.datetime.now()

    def __connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.debug("connected")
        except Exception as e:
            logger.error(f"Error connecting to socket on {self.host}:{self.port}")
            raise e

    def __query(self, command):
        self.__connect()
        command_str = (json.dumps(command) + "\n").encode("utf-8")
        logger.debug(command_str)
        self.socket.send(command_str)
        resp = self.socket.recv(2048)
        logger.debug(f"Respuesta: {resp}")
        self.socket.close()
        return json.loads(resp)

    def get_command(self, **kwargs):
        command = {"id": 0,
                   "jsonrpc": "2.0",
                   "psw": self.password}
        command.update(kwargs)
        return command

    def get_status(self):
        command = self.get_command(method="miner_getstat1")
        status = self.__query(command)
        rig_speed_khs, submitted_hashes, rejected_hashes = (int(v) for v in status['result'][2].split(";"))
        rig_speed = rig_speed_khs / 1e3     # in MH/s
        # Cards speed in MH/s
        self.cards_speed = tuple(0 if v == "off" else float(v)/1e3 for v in status['result'][3].split(";"))
        if submitted_hashes != self.submitted_shares:
            self.last_speed_change = datetime.datetime.now()
            self.submitted_shares = submitted_hashes
        return status

    def get_detailed_status(self):
        return self.__query(self.get_command(method="miner_getstatdetail"))

    def check_speed(self, minutes=15):
        """Returns true if the time between submited shares is lower
        than value of informed minutes"""
        now = datetime.datetime.now()
        elapsed_minutes = (now - self.last_speed_change).seconds / 60
        logger.info(f"Elapsed minutes without shares change: {elapsed_minutes:.2f}")
        return elapsed_minutes < minutes

    def set_card_status(self, card: int, status: bool):
        command = self.get_command(method="control_gpu", params=[card, 1 if status else 0])
        return self.__query(command)['result']

    def restart_miner(self):
        logger.info("Restarting miner")
        return self.__query(rig_status.get_command(method="miner_restart"))

    def reboot_miner(self):
        logger.info("Rebooting miner")
        return self.__query(rig_status.get_command(method="miner_reboot"))

    def ping(self) -> bool:
        """Performs a ping, returns True if ping worked"""
        res = self.__query(self.get_command(method="miner_ping"))
        if res:
            return res.get("result") == "pong"
        return False

    def check_ping(self):
        """If ping is invalid, reboot"""
        return  # Phoenixminer seems not to accept pings
        if not rig_status.ping():
            logger.error("Ping method failed, rebooting")
            reboot()

    def check_detailed_status(self) -> bool:
        """Returns False if a card might be frozen (has hashrate=0 and it is not paused),
        True otherwise"""
        return False        # Assume card blocked, as phoneix does not implement this method

        detailed_status = rig_status.get_detailed_status()
        for card_id, card_status in enumerate(detailed_status['devices']):
            mining_status = card_status['mining']
            hashrate = mining_status['hasrate']
            if hashrate > 0:
                continue
            paused = mining_status['paused']
            if paused:
                logger.info(f"Card {card_id} skipped: it is paused")
            else:
                logger.error(f"Card {card_id} blocked: rebooting")
                reboot()
        logger.info("Card check ok, continuing mining")
        return True


def check_rig(host, port, min_hashrate, password):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((host, port))
        print("connected")

        command = {"id": 0,
                   "jsonrpc": "2.0",
                   "method": "miner_getstat1",
                   "psw": password}

        command.update({"method": "control_gpu", "params": [0, 1]})
        # command.update({'id': 50})
        command_str = (json.dumps(command) + "\n").encode("utf-8")
        print(command_str)

        # HOST = "127.0.0.1"
        # socketWraped = ssl.create_default_context().wrap_socket(s, server_hostname="miner-ubuntu.local")
        # socketWraped.connect((HOST, port))
        # # CONNECT AND PRINT REPLY
        # socketWraped.send(command_str)
        # print(socketWraped.recv(1280))

        s.send(command_str)
        # s.send('{"id":0,"jsonrpc":"2.0","method":"miner_getstat1", "psw": "1234"}'.encode("utf-8"))
        j = s.recv(2048)
        print(f"Respuesta: {j}")
        s.close()
        if j:
            resp = json.loads(j.decode("utf-8"))
            resp = resp['result']
            if resp != "true":
                hashes = int(resp[2].split(';')[0])
                print("m/h=" + str(hashes))
                hash_ok = min_hashrate < hashes
                print("hashes ok is: " + str(hash_ok))
                return hash_ok
            else:
                return True
    except TimeoutError:
        print("connection timeout")
    except ConnectionRefusedError:
        print("connection refused")
    except Exception as e:
        print(f"exception: {e}")

    return False


if __name__ == '__main__':

    host = "127.0.0.1"
    rig_status = RigStatus(host, port=config("CDM_PORT"),
                           password=config("CDM_PASS"))
    pred = Aemet()
    logger.info("Starting rig management")

    if not is_debugging():
        time.sleep(START_MINER_DELAY)      # Wait 5 minutes for rig to start

    # main loop
    while True:
        rig_status.check_ping()
        status = rig_status.get_status()
        logger.info(status)
        min_without_shares = 15
        current_temp = pred.get_pred_hour(tipo="temperatura")
        status = current_temp < MAX_TEMP
        logger.info(f"Current temperature: {current_temp} so setting cards to {status}")
        # # If punta_convenio then switch all cards off
        # is_peak = punta_convenio()
        # status = status and not is_peak
        # log.info(f"Peak time is: {is_peak} so setting cards to {status}")
        for card in range(n_cards):
            logger.info(f"Setting card {card} to status {status}")
            logger.info(rig_status.set_card_status(card, status))
        if status:  # Only check for the rest if temperature is lower than MAX
            if not rig_status.check_speed(min_without_shares):
                # Restart
                logger.error(f"Rebooting due to minutes without shares {min_without_shares=}")
                reboot()
                # Restart miner
                rig_status.restart_miner()
                # rig_status.get_command("miner_reboot")  # Calls reboot.sh
            n_cards = len(rig_status.cards_speed)
            if any(speed == 0 for speed in rig_status.cards_speed):
                logger.info(f"Cards with 0 speed found: {rig_status.cards_speed}")
                if not rig_status.check_detailed_status():
                    logger.error("Frozen cards found, rebooting")
                    reboot()
        next_loop = datetime.datetime.now() + datetime.timedelta(seconds=loop_seconds)
        logger.info(f"loop sleep. Next loop at {next_loop}")
        time.sleep(loop_seconds)
