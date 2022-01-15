# given a map of one-hop nodes to two-hop
# neighbors; returns a set of mpr nodes.
def obtain_mpr(valid_bidir_map):
    # initially; all one-hop neighbors are MPR candidates.
    mpr_candidates = set(valid_bidir_map.keys())

    # OLSR allows suboptimal MPR sets; so the simplest
    # MPR selection algorithm would be to return here.
    # but of course, we can do better

    # throughout the algorithm, maintain a set of
    # two-hop nodes that are not yet covered by the
    # already-selected set of MPR nodes.
    # at the start; this is all two-hop nodes,
    # as no mpr nodes are selected yet.
    uncovered_two_hops = all_two_hops_for(mpr_candidates, valid_bidir_map)

    # as the low-hanging fruit; we can start by picking
    # one-hop nodes that have unique access to certain
    # two-hop nodes. that is; if node X is the only one-hop
    # neighbor with access to a two-hop neighbor node Y,
    # then node X simply cannot be excluded from the MPR set.
    # so we start by finding and adding these nodes.
    mpr = one_hops_with_unique_access(valid_bidir_map)
    # remove selected MPR nodes from candidates;
    # also remove their two-hop coverage from uncovered set
    mpr_candidates.difference_update(mpr)
    uncovered_two_hops.difference_update(all_two_hops_for(mpr, valid_bidir_map))

    # this part is greedy, and not guaranteed to give us the
    # most optimal set. however, I think it is a good heuristic
    # to cover most cases:
    # every iteration; we pick the one-hop neighbor that covers
    # most of the uncovered two-hop neighbors.
    # we must iterate until uncovered_two_hops is depleted
    while len(uncovered_two_hops) > 0:
        best_one_hop = max_coverage_neighbor(uncovered_two_hops, valid_bidir_map)
        if best_one_hop is not None:
            mpr.add(best_one_hop)
            # remove selected MPR node from candidates;
            # also remove its two-hop coverage from uncovered set
            mpr_candidates.discard(best_one_hop)
            uncovered_two_hops.difference_update(all_two_hops_for({best_one_hop}, valid_bidir_map))
    # validate the MPR set, just in case
    if not is_mpr_valid(mpr, valid_bidir_map):
        print("MPR selection does not work; reverting to the whole set")
        return set(valid_bidir_map.keys())
    return mpr


# validates that the selected MPR set covers
# all two-hop neighbors as the whole one-hop set
def is_mpr_valid(mpr_set, valid_bidir_map):
    all_one_hops = set(valid_bidir_map.keys())
    if all_one_hops == mpr_set:
        return True
    all_coverage = set()
    mpr_coverage = set()
    for one_hop in all_one_hops:
        all_coverage = all_coverage.union(valid_bidir_map[one_hop])
    for one_hop in mpr_set:
        mpr_coverage = mpr_coverage.union(valid_bidir_map[one_hop])
    return mpr_coverage.difference(all_one_hops) == all_coverage.difference(all_one_hops)


# returns the superset of two-hop nodes
# covered by a set of given one-hop nodes
def all_two_hops_for(one_hops, valid_bidir_map):
    two_hops = set()
    for one_hop in one_hops:
        if one_hop in valid_bidir_map:
            two_hops = two_hops.union(valid_bidir_map[one_hop])
    # exclude nodes that are already one-hop neighbors
    # we want a set of exclusively two-hop neighbors here
    for one_hop in valid_bidir_map.keys():
        two_hops.discard(one_hop)
    return two_hops


# returns the one-hop neighbor that is connected
# to the maximum number of interested two-hop neighbors
def max_coverage_neighbor(interested_two_hops, valid_bidir_map):
    max_coverage = 0
    best_node = None
    for one_hop, two_hops in valid_bidir_map.items():
        coverage = len(interested_two_hops.intersection(two_hops))
        if coverage > max_coverage:
            max_coverage = coverage
            best_node = one_hop
    return best_node


# returns the set of nodes with unique access to certain two-top nodes.
# that is, if two-hop node B is accessible only by one-hop node A; this
# func returns node A.
def one_hops_with_unique_access(valid_bidir_map):
    one_hop_with_uniq = set()
    for two_hop, one_hops in invert_bidir_map(valid_bidir_map).items():
        if len(one_hops) == 0:
            one_hop_with_uniq.add(list(one_hops)[0])
    return one_hop_with_uniq


# input map: one-hop neighbor -> list of two-hop neighbors it connects to
# output map: two-hop neighbor -> list of one-hop neighbors connected to it
def invert_bidir_map(valid_bidir_map):
    inv = {}
    for one_hop, two_hops in valid_bidir_map.items():
        for two_hop in two_hops:
            if two_hop not in inv:
                inv[two_hop] = set()
            inv[two_hop].add(one_hop)
    return inv
