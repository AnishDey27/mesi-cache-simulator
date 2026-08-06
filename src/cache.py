import math
from .constants import *

# ==============
# 1. Cache Line
# ==============
class CacheLine:
    def __init__(self):
        self.state = INVALID  
        self.tag = None

    def is_valid(self):
        return self.state != INVALID

    def update_state(self, new_state):
        self.state = new_state

# ==============
# 2. Cache Set
# ==============
class CacheSet:
    def __init__(self, associativity):
        self.associativity = associativity
        
        if not math.log2(associativity).is_integer():
            raise ValueError("Tree LRU requires associativity to be a power of 2.")

        self.lines = []
        for i in range(associativity):
            self.lines.append(CacheLine())

        self.tree_bits = []
        for i in range(associativity - 1):
            self.tree_bits.append(0)

    def find_line_by_tag(self, tag):
        for idx, line in enumerate(self.lines):
            if line.is_valid() and line.tag == tag:
                return line, idx
        return None, -1

    def get_plru_victim_index(self):
        # Fill invalid lines first to avoid unnecessary eviction
        for idx, line in enumerate(self.lines):
            if not line.is_valid():
                return idx
                
        # Tree Traversal
        node = 0
        line_idx = 0
        half_ways = self.associativity // 2
        
        while node < self.associativity - 1:
            bit = self.tree_bits[node]
            if bit == 0: # Go Left
                node = 2 * node + 1
            else:        # Go Right
                line_idx += half_ways
                node = 2 * node + 2
            half_ways //= 2
            
        return line_idx

    def update_plru_tree(self, accessed_index):
        node = 0
        half_ways = self.associativity // 2
        curr_idx = accessed_index
        
        while node < self.associativity - 1:
            if curr_idx < half_ways:
                self.tree_bits[node] = 1 # Accessed left, point right
                node = 2 * node + 1
            else:
                self.tree_bits[node] = 0 # Accessed right, point left
                curr_idx -= half_ways
                node = 2 * node + 2
            half_ways //= 2

# ===============
# 3. Cache Array 
# ===============
class Cache:
    def __init__(self, num_sets=256, associativity=4, line_size=DEFAULT_LINE_SIZE):
        if not math.log2(num_sets).is_integer():
            raise ValueError("Number of sets must be a power of 2.")

        self.num_sets = num_sets
        self.associativity = associativity
        self.line_size = line_size

        self.offset_bits = int(math.log2(line_size))
        self.index_bits = int(math.log2(num_sets))

        self.sets = []
        for i in range(num_sets):
            self.sets.append(CacheSet(associativity))

    def parse_address(self, address):
        index = (address >> self.offset_bits) & (self.num_sets - 1)
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index

    def read_cacheline(self, address):
        tag, index = self.parse_address(address)
        line, idx = self.sets[index].find_line_by_tag(tag)
        return line, idx
        
    def allocate_cacheline(self, address):
        tag, index = self.parse_address(address)
        cache_set = self.sets[index]
        
        victim_idx = cache_set.get_plru_victim_index()
        victim_line = cache_set.lines[victim_idx]
        
        evicted_state = victim_line.state
        victim_line.update_state(INVALID)
        victim_line.tag = tag
        
        return victim_line, evicted_state

    def update_lru(self, address):
        tag, index = self.parse_address(address)
        cache_set = self.sets[index]
        _, idx = cache_set.find_line_by_tag(tag)
        if idx != -1:
            cache_set.update_plru_tree(idx)