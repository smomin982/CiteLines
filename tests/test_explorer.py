"""Independent closures must not accumulate; radius counts minimum distance."""
from datetime import date

from explorer import render
from route_map import Citation, CitationNetwork


def graph():
    # 1-p-2-q-3; closing p disconnects 1, but closing q leaves 2-r-4-s-3.
    rows = {"p": "12", "q": "23", "r": "24", "s": "43", "t": "35"}
    return CitationNetwork((Citation(n, page, "99", page, 0)
                            for page, nodes in rows.items() for n in nodes), 0)


def test_independent_closures_on_a_multitransfer_route():
    g = graph()
    path = g.route("1", "3")
    assert g.closures(path) == [
        ("p", None, None),
        ("q", ["1", "p", "2", "r", "4", "s", "3"], 1),
    ]


def test_neighborhood_excludes_origin_and_three_transfer_destinations():
    g = graph()
    assert g.nearby("1", 1) == {"2": 1}
    assert g.nearby("1", 2) == {"2": 1, "3": 2, "4": 2}


def test_stress_view_accepts_permalink_and_preserves_cutoff():
    def snapshot(day):
        assert day == date(2025, 1, 12)
        return graph()
    html = render(dict(a="https://x.com/example/status/1", b="3",
                       mode="stress", day="2025-01-12"), snapshot)
    assert "Disconnected" in html and "Detour: +1" in html
    assert "Inspect both citations" in html
