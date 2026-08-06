import logging
from .constants import *

logger = logging.getLogger("MESI_Core")

class Core:
    def __init__(self, core_id, cache, bus):
        self.core_id = core_id
        self.cache = cache
        self.bus = bus
        
        self.accesses = 0
        self.hits = 0
        self.misses = 0
        self.total_cycles = 0

    # ===========
    # FSM LOGIC
    # ===========
    def _fsm_for_bus_snoop(self, state, bus_signal):
        action = None
        next_state = state

        if state == SHARED:
            if bus_signal == BUS_READ_EX or bus_signal == BUS_UPGRADE:
                next_state = INVALID
        elif state == EXCLUSIVE:
            if bus_signal == BUS_READ:
                next_state = SHARED
            elif bus_signal == BUS_READ_EX:
                next_state = INVALID
        elif state == MODIFIED:
            if bus_signal == BUS_READ:
                action = FLUSH
                next_state = SHARED
            elif bus_signal == BUS_READ_EX:
                action = FLUSH
                next_state = INVALID

        return next_state, action

    def _fsm_for_core(self, state, pr_request, shared_signal):
        next_state = state

        if state == INVALID:
            if pr_request == PR_READ:
                next_state = SHARED if shared_signal else EXCLUSIVE
            elif pr_request == PR_WRITE:
                next_state = MODIFIED
        elif state == SHARED:
            if pr_request == PR_WRITE:
                next_state = MODIFIED
        elif state == EXCLUSIVE:
            if pr_request == PR_WRITE:
                next_state = MODIFIED  
        
        return next_state

    # ============
    # CONTROLLER
    # ============
    def handle_bus_snoop(self, address, bus_signal):
        """Hardware Bus Interface Unit routing snoops into the FSM."""
        line, _ = self.cache.read_cacheline(address)
        
        shared_signal = False
        action = None
        
        if line and line.is_valid():
            shared_signal = True
            next_state, action = self._fsm_for_bus_snoop(line.state, bus_signal)
            line.update_state(next_state)
            
        return shared_signal, action

    def handle_core_request(self, operation, address):
        """Main CPU execution routing."""
        self.accesses += 1
        cycle_cost = CACHE_HIT_LATENCY
        
        line, _ = self.cache.read_cacheline(address)
        bus_signal = None
        hit_miss = "HIT "
        
        if not line or not line.is_valid():
            current_state = INVALID
            bus_signal = BUS_READ if operation == PR_READ else BUS_READ_EX
            hit_miss = "MISS"
            self.misses += 1
        else:
            current_state = line.state
            self.hits += 1
            if current_state == SHARED and operation == PR_WRITE:
                bus_signal = BUS_UPGRADE
                
        if bus_signal:
            cycle_cost += BUS_BROADCAST_LATENCY

        shared_signal = False
        source_core_id = None
        if bus_signal:
            for core in self.bus.cores:
                if core.core_id != self.core_id:
                    line_other, _ = core.cache.read_cacheline(address)
                    if line_other and line_other.is_valid():
                        shared_signal = True
                        source_core_id = core.core_id
                        break

        if hit_miss == "MISS":
            tag, index = self.cache.parse_address(address)
            victim_idx = self.cache.sets[index].get_plru_victim_index()
            if self.cache.sets[index].lines[victim_idx].state == MODIFIED:
                cycle_cost += MEMORY_ACCESS_LATENCY

            if shared_signal:
                cycle_cost += CACHE_TO_CACHE_LATENCY
            else:
                cycle_cost += MEMORY_ACCESS_LATENCY

        bus_str = bus_signal if bus_signal else "(No Bus Traffic)"
        logger.info(f"Core {self.core_id} {operation} {hex(address)} | {hit_miss} | {bus_str:<16} | {cycle_cost} cycles")


        if hit_miss == "MISS":
            if shared_signal:
                logger.info(f"Core {self.core_id} FETCH     | Peer cache-to-cache transfer from Core {source_core_id}")
            else:
                logger.info(f"Core {self.core_id} FETCH     | Main Memory fetch")
                
        actual_shared_signal = self.bus.broadcast(self.core_id, bus_signal, address)
        next_state = self._fsm_for_core(current_state, operation, actual_shared_signal)
        
        if current_state == INVALID:
            line, evicted_state = self.cache.allocate_cacheline(address)
            if evicted_state == MODIFIED:
                logger.info(f"Core {self.core_id} FLUSH     | Eviction: Dirty data written to Main Memory")
                
        line.update_state(next_state)
        self.cache.update_lru(address)
        self.total_cycles += cycle_cost