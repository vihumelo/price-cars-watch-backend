from services.vehicles.src.providers.webmotors.webmotors_listing_url_builder import build_listing_url


def test_build_listing_url_matches_webmotors_card_url_for_same_years():
    record = {
        "UniqueId": 81422733,
        "Specification": {
            "Make": {"Value": "HONDA"},
            "Model": {"Value": "HR-V"},
            "Version": {"Value": "1.8 16V FLEX LX 4P AUTOMÁTICO"},
            "NumberPorts": "4",
            "YearFabrication": "2017",
            "YearModel": "2017.0",
        },
    }

    assert build_listing_url(record) == (
        "https://www.webmotors.com.br/comprar/honda/hr-v/"
        "18-16v-flex-lx-4p-automatico/4-portas/2017/81422733"
    )


def test_build_listing_url_uses_both_years_when_they_differ():
    record = {
        "UniqueId": "81422733",
        "Specification": {
            "Make": {"Value": "Honda"},
            "Model": {"Value": "HR-V"},
            "Version": {"Value": "EX"},
            "NumberPorts": 4,
            "YearFabrication": 2016,
            "YearModel": 2017.0,
        },
    }

    assert build_listing_url(record) == (
        "https://www.webmotors.com.br/comprar/honda/hr-v/ex/"
        "4-portas/2016-2017/81422733"
    )


def test_build_listing_url_returns_none_when_a_required_field_is_missing():
    record = {
        "UniqueId": 81422733,
        "Specification": {
            "Make": {"Value": "HONDA"},
            "Model": {"Value": "HR-V"},
            "Version": {"Value": "EX"},
            "YearFabrication": 2017,
            "YearModel": 2017,
        },
    }

    assert build_listing_url(record) is None
