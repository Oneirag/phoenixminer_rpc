from ong_utils import OngConfig, is_debugging

cfg = OngConfig("phoenixminer_rpc",
                cfg_filename="/home/ongpi/.config/ongpi/phoenixminer_rpc.yaml")
logger = cfg.logger
config = cfg.config
wallet = hex(config("WALLET"))      # This must be translated back to hex
START_MINER_DELAY = 15 * 60         # wait 15 mins for miner to start before checks
MAX_TEMP = config("MAX_TEMP", 30)
