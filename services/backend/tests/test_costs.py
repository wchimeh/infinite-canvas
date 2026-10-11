from concurrent.futures import ThreadPoolExecutor

import pytest

from app.costs import BudgetLedger, quote_snapshot
from app.store import Store


def project(store, limit='1.00'):
    value = store.create_project('Budget QA')
    value['settings']['budget'] = {'limit': limit, 'currency': 'CNY'}
    store.put_document(value['id'], 'project', value)
    return value['id']


def test_decimal_second_quote_and_unknown_price():
    rules = {'runninghub/ltx23': {'amount': '0.125', 'unit': 'second', 'currency': 'CNY'}}
    quote = quote_snapshot({'kind': 'video.image_to_video', 'config': {'model': 'ltx23', 'seconds': 5}}, rules)
    assert quote['amount'] == '0.625000'
    assert quote['known']
    assert not quote_snapshot({'kind': 'image.generate', 'config': {}}, rules)['known']
    assert quote_snapshot({'kind': 'image.generate', 'config': {'provider': 'comfyui'}}, {})['amount'] == '0.000000'


def test_unknown_price_is_blocked_by_budget(tmp_path):
    store = Store(tmp_path)
    pid = project(store)
    with pytest.raises(ValueError, match='未知|unknown'):
        BudgetLedger(store).reserve(pid, pid + '_task', {'known': False, 'amount': None, 'currency': None})


def test_concurrent_reservations_never_exceed_limit(tmp_path):
    store = Store(tmp_path)
    pid = project(store)
    ledger = BudgetLedger(store)
    quote = {'known': True, 'amount': '0.60', 'currency': 'CNY', 'model': 'test'}
    def reserve(i):
        try:
            ledger.reserve(pid, pid + '_' + str(i), quote)
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(reserve, range(4))) == 1
    assert ledger.summary(pid)['estimatedUsed']['CNY'] == '0.600000'
    assert ledger.summary(pid)['actual'] is None


def test_reservation_is_idempotent_and_releasable(tmp_path):
    store = Store(tmp_path)
    pid = project(store)
    ledger = BudgetLedger(store)
    quote = {'known': True, 'amount': '0.75', 'currency': 'CNY'}
    tid = pid + '_task'
    ledger.reserve(pid, tid, quote)
    ledger.reserve(pid, tid, quote)
    assert ledger.summary(pid)['estimatedUsed']['CNY'] == '0.750000'
    ledger.release(pid, tid, 'never submitted')
    assert ledger.summary(pid)['estimatedUsed'].get('CNY', '0.000000') == '0.000000'
    ledger.reserve(pid, tid, quote)
    assert ledger.summary(pid)['estimatedUsed']['CNY'] == '0.750000'


def test_budget_does_not_convert_currencies_silently(tmp_path):
    store = Store(tmp_path)
    pid = project(store)
    with pytest.raises(ValueError, match='币种|currency'):
        BudgetLedger(store).reserve(pid, pid + '_task', {'known': True, 'amount': '0.10', 'currency': 'USD'})


def test_unknown_is_recorded_without_budget_and_cannot_replace_reserved_quote(tmp_path):
    store = Store(tmp_path)
    pid = store.create_project('No limit')['id']
    ledger = BudgetLedger(store)
    tid = pid + '_task'
    ledger.reserve(pid, tid, {'known': False, 'amount': None, 'currency': None})
    assert ledger.summary(pid)['unknownCount'] == 1
    with pytest.raises(ValueError):
        ledger.reserve(pid, tid, {'known': True, 'amount': '100', 'currency': 'CNY'})
