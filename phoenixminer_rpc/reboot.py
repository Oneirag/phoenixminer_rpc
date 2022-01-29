"""
Performs a hard reboot
"""

import os
from phoenixminer_rpc import logger


def reboot():
    logger.info("Rebooting")
    # os.system('/sbin/reboot')
    script_path = os.path.join(os.path.dirname(__file__), "hard_reboot.sh")
    logger.debug(f"Executing {script_path}")
    os.system(script_path)
