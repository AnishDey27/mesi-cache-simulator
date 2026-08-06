# ==========================================
# MESI State Definitions
# ==========================================
INVALID = 'I'
SHARED = 'S'
EXCLUSIVE = 'E'
MODIFIED = 'M'

# ==========================================
# Processor Requests
# ==========================================
PR_READ = 'PrRd'   # CPU wants to read
PR_WRITE = 'PrWr'  # CPU wants to write

# ==========================================
# Bus (Snoop) Signals
# ==========================================
BUS_READ = 'BusRd'       # Another core wants to read
BUS_READ_EX = 'BusRdX'   # Another core wants to write (miss)
BUS_UPGRADE = 'BusUpgr'  # Another core wants to write (hit on Shared)
FLUSH = 'Flush'          # Forced memory write-back from 'M' state

# ==========================================
# Default Cache Architecture Parameters
# ==========================================
DEFAULT_LINE_SIZE = 64  # Bytes per cache line
DEFAULT_NUM_CORES = 4   # Standard quad-core setup

# ==========================================
# Simulated Latencies (Cycles)
# ==========================================
CACHE_HIT_LATENCY = 1          # L1 SRAM access time
CACHE_TO_CACHE_LATENCY = 15    # Peer-to-peer cache read time
BUS_BROADCAST_LATENCY = 2      # Overhead to broadcast on the shared bus
MEMORY_ACCESS_LATENCY = 100    # Main memory fetch or writeback time