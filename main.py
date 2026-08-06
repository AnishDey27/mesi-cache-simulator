import os
import logging
from src.constants import *
from src.cache import Cache
from src.bus import Bus
from src.core import Core

os.makedirs("logs", exist_ok=True)
log_file_path = "logs/simulator.log"

logging.basicConfig(
    level=logging.INFO, 
    format='%(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='w')
    ]
)
logger = logging.getLogger("MESI_Testbench")

def print_cache_states(cores, address):
    states_str = ""
    
    for i in range(len(cores)):
        line, _ = cores[i].cache.read_cacheline(address)
        state = line.state if line else INVALID
        
        states_str += f"Core {cores[i].core_id}: {state}"
        
        if i < len(cores) - 1:
            states_str += ", "
    
    logger.info(f"STATES -> {states_str}")
    logger.info("-" * 65)

def print_statistics(cores):
    total_accesses = sum(c.accesses for c in cores)
    total_hits = sum(c.hits for c in cores)
    total_misses = sum(c.misses for c in cores)
    total_cycles = sum(c.total_cycles for c in cores)
    
    hit_rate = (total_hits / total_accesses * 100) if total_accesses > 0 else 0
    miss_rate = (total_misses / total_accesses * 100) if total_accesses > 0 else 0
    amat = (total_cycles / total_accesses) if total_accesses > 0 else 0
    
    logger.info("=================================================================")
    logger.info("                     SYSTEM STATISTICS                           ")
    logger.info("=================================================================")
    logger.info(f"Total Accesses : {total_accesses}")
    logger.info(f"Total Cycles   : {total_cycles}")
    logger.info(f"Global Hits    : {total_hits} ({hit_rate:.2f}%)")
    logger.info(f"Global Misses  : {total_misses} ({miss_rate:.2f}%)")
    logger.info(f"System AMAT    : {amat:.2f} cycles")
    logger.info("=================================================================")

def run_trace(cores, filepath):
    """Reads a trace file and executes the commands on the simulated cores."""
    if not os.path.exists(filepath):
        logger.error(f"ERROR: Could not find {filepath}.")
        return

    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            core_id = int(parts[0])
            operation_str = parts[1].upper()
            address = int(parts[2], 16) 
            
            operation = PR_READ if operation_str == 'R' else PR_WRITE
            
            cores[core_id].handle_core_request(operation, address)
            print_cache_states(cores, address)

def main():
    print("Simulation started.")
    
    bus = Bus()
    cores = []
    
    for i in range(DEFAULT_NUM_CORES):
        cache = Cache(num_sets=4, associativity=2)
        core = Core(core_id=i, cache=cache, bus=bus)
        cores.append(core)
        
    bus.connect_cores(cores)

    run_trace(cores, "traces/instructions.txt")
    print_statistics(cores)
    
    print(f"Simulation complete, logs: {log_file_path}\n")

if __name__ == "__main__":
    main()