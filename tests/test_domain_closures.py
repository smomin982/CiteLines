"""A different URL can still depend on the same site."""
from domains import page_site
from route_map import Citation, CitationNetwork


def test_suffix_boundaries_and_private_sites():
    assert page_site("https://News.BBC.co.uk:443/story") == "bbc.co.uk"
    assert page_site("https://www.notbbc.co.uk/story") == "notbbc.co.uk"
    assert page_site("https://docs.example.github.io/page") == "example.github.io"
    assert page_site("https://www.city.kawasaki.jp/a") == "city.kawasaki.jp"
    assert page_site("https://a.b.ck/article") == "a.b.ck"
    assert page_site("https://127.0.0.1/page") == "127.0.0.1"


def test_domain_closure_is_independent_and_preserves_unrelated_sites():
    p,q,r = ("https://news.bbc.co.uk/a","https://sport.bbc.co.uk/b","https://notbbc.co.uk/c")
    rows = [Citation(post,k,"1",k,t) for t,k in enumerate([p,q,r]) for post in ["1","2"]]
    g = CitationNetwork(rows,1)
    assert g.route("1","2",p) == ["1",q,"2"]
    assert g.route("1","2",closed_site="bbc.co.uk") is None
    assert g.route("1","2") == ["1",p,"2"]
    later = CitationNetwork(rows,2)
    assert later.route("1","2",closed_site="bbc.co.uk") == ["1",r,"2"]
