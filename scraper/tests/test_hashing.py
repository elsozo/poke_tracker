from poketracker.diffing.hashing import content_hash, normalize_url, product_key


def test_normalize_url_strips_tracking_params():
    dirty = "https://example.com/product?utm_source=newsletter&id=42&gclid=xyz"
    clean = "https://example.com/product?id=42"
    assert normalize_url(dirty) == clean


def test_normalize_url_strips_trailing_slash():
    assert normalize_url("https://example.com/product/") == normalize_url("https://example.com/product")


def test_product_key_stable_for_same_inputs():
    a = product_key("ludifolie", "30th-etb", "https://example.com/etb?utm_source=x")
    b = product_key("ludifolie", "30th-etb", "https://example.com/etb")
    assert a == b


def test_product_key_differs_across_sites():
    a = product_key("ludifolie", "30th-etb", "https://example.com/etb")
    b = product_key("variantes", "30th-etb", "https://example.com/etb")
    assert a != b


def test_content_hash_changes_when_price_changes():
    h1 = content_hash(49.99, True, False, None)
    h2 = content_hash(39.99, True, False, None)
    assert h1 != h2


def test_content_hash_stable_for_identical_state():
    h1 = content_hash(49.99, True, False, "SellerA")
    h2 = content_hash(49.99, True, False, "SellerA")
    assert h1 == h2
