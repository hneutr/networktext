import os
from collections import defaultdict
import copy
import json
import math
import sys

from . import entities

class TextNetwork():
    def __init__(self, storage, file_names, entity_interface, accumulative=True, edge_threshold=50, edge_repeat_threshold=50, min_occurrences=3):
        self.storage = storage
        self.accumulative = accumulative
        self.edge_threshold = edge_threshold
        self.edge_repeat_threshold = edge_repeat_threshold

        self.section_networks = []
        for file_name in file_names:
            kwargs = {
                'edge_threshold' : self.edge_threshold,
                'edge_repeat_threshold' : self.edge_repeat_threshold,
            }

            if accumulative and bool(self.section_networks):
                kwargs['existing_edges'] = self.section_networks[-1].edges
                kwargs['existing_nodes'] = self.section_networks[-1].nodes

            raw_matches = self.storage.raw_matches[file_name]
            section_matches = entity_interface.add_entity_keys_to_matches(raw_matches)

            self.section_networks.append(
                SectionNetwork(section_matches, **kwargs)
            )

class SectionNetwork():
    """a network of a text section."""
    def __init__(self, matches, edge_threshold=50, edge_repeat_threshold=50,
                 existing_edges=list(),
                 existing_nodes=set()
                 ):

        self.matches = sorted(copy.deepcopy(matches), key=lambda m: m['start'])
        self.edge_threshold = 50
        self.edge_repeat_threshold = 50

        self.nodes = {e.key for e in self.matches}

        # add nodes in from previous sections if passed
        for node in existing_nodes:
            self.nodes.add(node)

        self.edges = self.make_edges(self.matches, existing_edges)

    def make_edges(self, matches, existing_edges):
        edges_dict = defaultdict(defaultdict(int).copy)

        # add edges in from previous sections if passed
        for entity_one, entity_two, weight in existing_edges:
            edges_dict[entity_one][entity_two] = weight

        # dict for tracking edge thresholds for smoothing.
        # heuristic to avoid multi-counting
        block_until = defaultdict(defaultdict(int).copy)

        for i, first in enumerate(matches[:-1]):
            for second in matches[i + 1:]:
                match_start = min(first.start, second.start)
                match_end = max(first.end, second.end)

                # don't make an edge out of the threshold
                # don't evaluate further `seconds` for this `first` if the
                # `second` is out of range
                if second.start - first.end > self.edge_threshold:
                    break

                # at this point, we have a possible edge, so to make the
                # dictionaries easier, sort by key
                if first.key > second.key:
                    first, second = second, first

                # don't repeat edges within a threshold
                if match_start < block_until[first.key][second.key]:
                    continue

                # don't make edges between the same node
                if first.key == second.key:
                    continue
                
                edges_dict[first.key][second.key] += 1
                block_until[first.key][second.key] = match_end + self.edge_repeat_threshold

        edges = []
        for entity_one, entity_one_edges in edges_dict.items():
            for entity_two, edge_weight in entity_one_edges.items():
                if edge_weight:
                    edges.append([entity_one, entity_two, edge_weight])

        return edges

class Graphify:
    def should_regenerate(self):
        """ there are two types of regenerations, 
        1. 'all' - where the entities have changed
        2. 'edges' - where the edges have changed
        (we can also not need to reload at all)
        """
        if not os.path.exists(self.cached_state_path):
            return 'all'

        with open(self.cached_state_path, 'r') as f:
            old_cache_info = json.load(f)

        if old_cache_info['entities_hash'] != self.cache_info['entities_hash']:
            return 'all'
        else:
            for key, value in self.cache_info.items():
                if old_cache_info[key] != value:
                    return 'edges'

            return 'none'

        return 'all'
