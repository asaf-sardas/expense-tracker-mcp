from mcp_server.expenses_tracker.parser import to_agorot, to_shekels


def test_to_agorot_converts_shekels_to_integer_agorot():
    assert to_agorot(45.5) == 4550
    assert to_agorot(12.9) == 1290
    assert to_agorot(0.01) == 1


def test_to_agorot_rounds_float_noise():
    # 19.99 * 100 == 1998.9999999999998 as a float
    assert to_agorot(19.99) == 1999


def test_round_trip_is_exact():
    assert to_shekels(to_agorot(0.1) + to_agorot(0.2)) == 0.3


def test_format_money_uses_currency_symbol_and_thousands():
    from mcp_server.expenses_tracker.parser import format_money

    assert format_money(1250.5) == "₪1,250.50"
    assert format_money(-5) == "-₪5.00"
