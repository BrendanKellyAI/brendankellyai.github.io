from hub.build import build
from hub.link_checker import check_links, extract_links, main


def test_extract_links_covers_anchors_stylesheets_images_and_scripts():
    html = """
    <a href="/about/">About</a>
    <link rel="stylesheet" href="/static/css/style.css">
    <img src="/static/social/default-og.png">
    <script src="/static/app.js"></script>
    """
    links = extract_links(html)
    assert "/about/" in links
    assert "/static/css/style.css" in links
    assert "/static/social/default-og.png" in links
    assert "/static/app.js" in links


def test_check_links_passes_when_every_internal_link_resolves(tmp_path):
    (tmp_path / "about").mkdir()
    (tmp_path / "about" / "index.html").write_text("<p>About</p>", encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<a href="/about/">About</a><a href="#content">Skip</a>'
        '<a href="https://example.com/">External</a>',
        encoding="utf-8",
    )
    assert check_links(tmp_path) == []


def test_check_links_reports_a_missing_directory_page(tmp_path):
    (tmp_path / "index.html").write_text('<a href="/missing/">Missing</a>', encoding="utf-8")
    broken = check_links(tmp_path)
    assert len(broken) == 1
    assert "/missing/" in broken[0]
    assert "index.html" in broken[0]


def test_check_links_reports_a_missing_asset_file(tmp_path):
    (tmp_path / "index.html").write_text(
        '<link rel="stylesheet" href="/static/css/missing.css">', encoding="utf-8"
    )
    broken = check_links(tmp_path)
    assert len(broken) == 1
    assert "/static/css/missing.css" in broken[0]


def test_check_links_ignores_mailto_and_fragment_links(tmp_path):
    (tmp_path / "index.html").write_text(
        '<a href="mailto:test@example.com">Email</a><a href="#top">Top</a>', encoding="utf-8"
    )
    assert check_links(tmp_path) == []


def test_check_links_on_the_real_seed_data_build(tmp_path):
    output_dir = tmp_path / "_site"
    build(output_dir=output_dir)
    assert check_links(output_dir) == []


def test_main_returns_zero_when_no_broken_links(tmp_path, capsys):
    (tmp_path / "index.html").write_text("<p>Home</p>", encoding="utf-8")
    assert main(tmp_path) == 0
    assert "No broken internal links found." in capsys.readouterr().out


def test_main_returns_one_when_links_are_broken(tmp_path, capsys):
    (tmp_path / "index.html").write_text('<a href="/missing/">Missing</a>', encoding="utf-8")
    assert main(tmp_path) == 1
    assert "broken link" in capsys.readouterr().err
