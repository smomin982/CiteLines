"""A small cycle with a shared shortcut, a leaf and a late backup."""
from route_map import Citation, CitationNetwork


def network(cutoff=10):
    edges = [("1", "p", 1), ("2", "p", 1), ("4", "p", 1),
             ("1", "q", 1), ("3", "q", 1), ("3", "r", 1), ("2", "r", 5),
             ("1", "s", 7), ("2", "s", 7)]
    return CitationNetwork((Citation(a, b, str(i), b, t)
                            for i, (a, b, t) in enumerate(edges)), cutoff)


def test_shortest_beats_longer_eligible_path():
    assert network(5).route("1", "2") == ["1", "p", "2"]


def test_removal_and_inclusive_cutoff_change_reachability():
    assert network(4).route("1", "2", "p") is None
    assert network(5).route("1", "2", "p") == ["1", "q", "3", "r", "2"]


def test_equal_length_backup_is_not_a_detour():
    assert network(7).route("1", "2", "p") == ["1", "s", "2"]


def test_closure_isolates_leaf_without_mutating_graph():
    graph = network()
    assert graph.route("1", "4", "p") is None
    assert graph.route("1", "4") == ["1", "p", "4"]
