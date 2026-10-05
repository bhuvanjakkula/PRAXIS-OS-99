import pytest
from pydantic import ValidationError
from praxis.services.fiscal_design import FiscalDesign, analyze_fiscal_design
from praxis.services.transfer_equity import TransferEquity, analyze_transfers


def fiscal_payload():
    return dict(years=2, opening_gdp=1000, opening_debt=100, opening_reserve=15,
                nominal_growth=0, adverse_nominal_growth=-.1, tax_base_share=.5,
                effective_tax_rate=.2, collection_efficiency=1, adverse_collection_drop=.2,
                non_tax_revenue=0, capital_spending=30, service_spending=60,
                social_spending=20, spending_growth=0, interest_rate=.1,
                adverse_interest_increase=.05, evidence='Synthetic accounting example')


def equity_payload():
    return dict(groups=[dict(name='Lower', population=100, income=10, tax=0,
                            transfer=20, coverage=.5),
                        dict(name='Higher', population=100, income=30, tax=5,
                             transfer=0, coverage=0)], leakage=.25,
                poverty_line=20, evidence='Synthetic distribution')


def test_fiscal_reserve_depletion_and_accounting_identity():
    normal, adverse = analyze_fiscal_design(FiscalDesign(**fiscal_payload()))['scenarios']
    first, second = normal['years']
    assert first['overall_balance'] == -20
    assert first['reserve_draw'] == 15
    assert first['new_borrowing'] == 5
    assert second['closing_debt'] == 125.5
    assert normal['reserve_exhaustion_year'] == 1
    assert adverse['years'][0]['tax_revenue'] == pytest.approx(72)
    for scenario in (normal, adverse):
        for row in scenario['years']:
            assert row['closing_debt']-row['closing_reserve'] == pytest.approx(
                row['opening_debt']-row['opening_reserve']-row['overall_balance'])


def test_surplus_repays_debt_then_replenishes_reserves_and_validates_share():
    inputs = fiscal_payload() | dict(non_tax_revenue=200)
    first = analyze_fiscal_design(FiscalDesign(**inputs))['scenarios'][0]['years'][0]
    assert first['closing_debt'] == 0
    assert first['closing_reserve'] == 95
    with pytest.raises(ValidationError):
        FiscalDesign(**(inputs | dict(social_spending_review_floor=101)))


def test_transfer_coverage_leakage_and_weighted_gini():
    result = analyze_transfers(TransferEquity(**equity_payload()))
    assert result['before']['grouped_gini'] == pytest.approx(.25)
    assert result['after']['mean_income'] == pytest.approx(21.25)
    assert result['after']['grouped_gini'] == pytest.approx(0.13235294117647056)
    assert result['after']['poverty_headcount_share'] == .25
    assert result['allocated_transfers'] == 1000
    assert result['delivered_transfers'] == 750
    assert result['tax_total'] == 500


def test_zero_income_and_invalid_group_inputs():
    inputs = equity_payload()
    for group in inputs['groups']:
        group.update(income=0, tax=0, transfer=0)
    result = analyze_transfers(TransferEquity(**inputs))
    assert result['after']['grouped_gini'] is None
    inputs['groups'][0]['tax'] = 1
    with pytest.raises(ValidationError):
        TransferEquity(**inputs)
    inputs = equity_payload()
    inputs['groups'][1]['name'] = ' LOWER '
    with pytest.raises(ValidationError):
        TransferEquity(**inputs)
