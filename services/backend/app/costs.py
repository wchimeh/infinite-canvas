"""按用户配置估价和原子预算预留；预留永远不伪装为服务商结算。"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import time

from app.store import encode
from app.generation_profiles import TEXT_KINDS


def money(value):
    return str(Decimal(str(value)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))


def quote_snapshot(snapshot, prices):
    kind, config = snapshot['kind'], snapshot.get('config', {})
    provider = config.get('provider', 'text' if kind in TEXT_KINDS else 'runninghub')
    local = kind in ('story.prompt', 'shots.select', 'text.concat', 'frame.extract', 'audio.extract', 'audio.trim', 'video.trim') or kind.startswith('asset.') or kind.endswith('.reference') or snapshot.get('adopted') or provider == 'comfyui'
    if kind in TEXT_KINDS:
        model = snapshot.get('textModel') or ''
    elif kind == 'video.image_to_video':
        model = config.get('model', 'ltx23')
    elif kind == 'video.combat':
        model = 'minimax_h3_combat'
    elif kind == 'video.sound_effects':
        model = 'mmaudio'
    elif kind == 'audio.tts':
        has_audio = any(ref.get('mime', '').startswith('audio/') for ref in snapshot.get('references', [])) or any(
            link.get('port') == 'audio' for link in snapshot.get('links', []))
        model = 'voxcpm2' if has_audio else 'qwen'
    else:
        model = 'image2'
    workflow = snapshot.get('cloudWorkflow')
    if workflow:
        model = workflow.get('builtin') or workflow['id']
    service_id = snapshot.get('textServiceId')
    price_key = 'workflow/' + workflow['id'] if workflow else 'text/' + service_id + '/' + model if service_id and service_id != 'legacy' else None
    quote = {'provider': provider, 'model': model, 'known': False, 'amount': None, 'currency': None, 'basis': 'unknown'}
    if local:
        return {**quote, 'known': True, 'amount': '0.000000', 'basis': 'local'}
    quote['priceKey'] = price_key or provider + '/' + model
    rule = prices.get(price_key) if price_key else prices.get(provider + '/' + model) or prices.get(kind) or prices.get(model)
    if rule is None:
        return quote
    try:
        amount = Decimal(str(rule['amount']))
        if rule['unit'] == 'second':
            seconds = Decimal(str(config.get('seconds', 8 if kind == 'video.combat' else 5)))
            if not seconds.is_finite() or seconds <= 0:
                raise ValueError('生成时长无效')
            amount *= seconds
        elif rule['unit'] != 'task':
            raise ValueError('价格计量单位无效')
        if not amount.is_finite() or amount < 0 or rule['currency'] not in ('CNY', 'USD'):
            raise ValueError('价格或币种无效')
        return {**quote, 'known': True, 'amount': money(amount), 'currency': rule['currency'], 'basis': 'user-configured'}
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ValueError('价格规则无效') from exc


def summarize_quotes(quotes):
    totals = {}
    for quote in quotes:
        if quote.get('known') and quote.get('currency'):
            currency = quote['currency']
            totals[currency] = money(Decimal(totals.get(currency, '0')) + Decimal(quote['amount']))
    return {'totals': totals, 'unknownCount': sum(not q['known'] for q in quotes), 'quotes': quotes, 'actual': None}


class BudgetLedger:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def ensure(con):
        con.execute('CREATE TABLE IF NOT EXISTS cost_reservations (task_id TEXT PRIMARY KEY, quote TEXT NOT NULL, status TEXT NOT NULL, reason TEXT, updated_at REAL NOT NULL)')

    def reserve(self, pid, tid, quote):
        with self.store.db(pid) as con:
            con.execute('BEGIN IMMEDIATE')
            self.ensure(con)
            old = con.execute('SELECT quote,status FROM cost_reservations WHERE task_id=?', (tid,)).fetchone()
            if old and old['status'] == 'reserved':
                if json.loads(old['quote']) != quote:
                    raise ValueError('已预留任务的价格快照不能改变')
                return
            project = json.loads(con.execute("SELECT body FROM documents WHERE key='project'").fetchone()[0])
            budget = project.get('settings', {}).get('budget')
            if budget and budget.get('limit') is not None:
                try:
                    limit = Decimal(str(budget['limit']))
                    if not limit.is_finite() or limit < 0:
                        raise ValueError('项目预算无效')
                except InvalidOperation as exc:
                    raise ValueError('项目预算无效') from exc
                if not quote.get('known'):
                    raise ValueError('费用未知：请先配置该模型价格，再使用项目预算')
                if Decimal(str(quote.get('amount', 0))) > 0:
                    if quote.get('currency') != budget.get('currency', 'CNY'):
                        raise ValueError('估算币种与项目预算币种不一致')
                    rows = [json.loads(row[0]) for row in con.execute("SELECT quote FROM cost_reservations WHERE status='reserved'")]
                    if any(not row.get('known') for row in rows):
                        raise ValueError('项目已有未知费用预留，请先核查服务商账单')
                    used = sum((Decimal(q['amount']) for q in rows if q.get('currency') == quote['currency']), Decimal(0))
                    if used + Decimal(quote['amount']) > limit:
                        raise ValueError('项目预算不足，任务尚未提交服务商')
            con.execute('INSERT OR REPLACE INTO cost_reservations VALUES (?,?,?,?,?)', (tid, encode(quote), 'reserved', None, time.time()))

    def release(self, pid, tid, reason):
        with self.store.db(pid) as con:
            self.ensure(con)
            con.execute("UPDATE cost_reservations SET status='released', reason=?, updated_at=? WHERE task_id=? AND status='reserved'", (reason, time.time(), tid))

    def summary(self, pid):
        with self.store.db(pid) as con:
            self.ensure(con)
            rows = [dict(row) for row in con.execute('SELECT * FROM cost_reservations ORDER BY updated_at DESC')]
        reserved = [json.loads(row['quote']) for row in rows if row['status'] == 'reserved']
        summary = summarize_quotes(reserved)
        return {'estimatedUsed': summary['totals'], 'unknownCount': summary['unknownCount'], 'actual': None,
                'reservations': [{**row, 'quote': json.loads(row['quote'])} for row in rows]}
