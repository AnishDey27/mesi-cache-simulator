import logging
from .constants import *

logger = logging.getLogger("MESI_Bus")

class Bus:
    def __init__(self):
        self.cores = [] 

    def connect_cores(self, cores):
        self.cores = cores

    def broadcast(self, sender_core_id, bus_signal, address):
        shared_signal = False
        
        if bus_signal is None:
            return False

        for core in self.cores:
            if core.core_id == sender_core_id:
                continue

            has_shared, snoop_action = core.handle_bus_snoop(address, bus_signal)
            
            if has_shared:
                shared_signal = True
            
            if snoop_action == FLUSH:
                logger.info(f"Core {core.core_id} FLUSH     | Protocol Snoop: Dirty data written back!")

        return shared_signal