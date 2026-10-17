from conftest import write_pdf

from hub.slides import copy_slides, render_slides


def test_render_slides_writes_one_image_per_page(tmp_path):
    pdf = tmp_path / "bk-s1-e2-tokens-v1.pdf"
    write_pdf(pdf, pages=3)

    images = render_slides(pdf, tmp_path / "cache")

    assert [image.name for image in images] == ["01.webp", "02.webp", "03.webp"]
    assert all(image.stat().st_size > 0 for image in images)


def test_render_slides_reuses_the_cache_for_the_same_deck(tmp_path):
    pdf = tmp_path / "bk-s1-e2-tokens-v1.pdf"
    write_pdf(pdf, pages=2)
    cache = tmp_path / "cache"
    first = render_slides(pdf, cache)
    stamps = [image.stat().st_mtime_ns for image in first]

    second = render_slides(pdf, cache)

    assert [image.stat().st_mtime_ns for image in second] == stamps


def test_render_slides_rerenders_an_interrupted_cache(tmp_path):
    pdf = tmp_path / "bk-s1-e2-tokens-v1.pdf"
    write_pdf(pdf, pages=2)
    cache = tmp_path / "cache"
    partial = cache / pdf.stem
    partial.mkdir(parents=True)
    (partial / "01.webp").write_bytes(b"half written")

    images = render_slides(pdf, cache)

    assert len(images) == 2
    assert (partial / "01.webp").read_bytes() != b"half written"


def test_copy_slides_places_images_in_the_site(tmp_path):
    pdf = tmp_path / "bk-s1-e2-tokens-v1.pdf"
    write_pdf(pdf, pages=2)
    images = render_slides(pdf, tmp_path / "cache")
    target = tmp_path / "_site" / "static" / "episodes" / "s1-e2-tokens" / "slides"

    copy_slides(images, target)

    assert sorted(path.name for path in target.iterdir()) == ["01.webp", "02.webp"]
