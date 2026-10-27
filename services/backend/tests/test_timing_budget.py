import pytest

from app.shot_nodes import validate_timing_budget


def test_long_japanese_dialogue_exceeds_short_shot():
    text = '[Shot 1] At 00:00.000, arrival.\n[Shot 2] At 00:08.500, <d>[Japanese] 膝から血が出てるよ。まずはそっちをどうにかしなさい。</d>'
    with pytest.raises(ValueError, match='对白'):
        validate_timing_budget(text, 12)


def test_short_dialogue_and_silent_action_are_allowed():
    validate_timing_budget('[Shot 1] At 00:00.000, <d>[Japanese] ありがとう。</d>', 8)
    validate_timing_budget('A door opens after the hand pushes it.', 5)


def test_timestamp_after_end_is_rejected():
    with pytest.raises(ValueError, match='时间'):
        validate_timing_budget('[Shot 1] At 00:00.000, wait. [Shot 2] At 00:14.000, reply.', 12)


def test_dialogue_without_timestamps_checks_whole_duration():
    with pytest.raises(ValueError, match='对白'):
        validate_timing_budget('<d>[Chinese] ' + '这是很长的一段话' * 12 + '</d>', 5)


def test_legacy_first_shot_without_timestamp_keeps_later_intervals():
    text = '[Shot 1] An accident. [Shot 2] At 00:04.500, <d>[Japanese] ' + 'ごめんなさい' * 5 + '</d> [Shot 3] At 00:08.500, reaction.'
    with pytest.raises(ValueError, match='第2段对白'):
        validate_timing_budget(text, 12)


@pytest.mark.parametrize('prompt', [
    '<d>[Chinese] ' + '这段对白太长无法自然说完' * 10 + '</d>',
    '[Shot 1] At 00:00.000, wait. [Shot 2] At 00:04.000, <d>[Chinese] 这段台词会超过剩余时间。</d>',
], ids=['long-dialogue', 'short-shot-interval'])
def test_video_submits_without_dialogue_budget_check(tmp_path, monkeypatch, prompt):
    from app.credentials import Settings
    from app.store import Store
    from app.worker import Worker
    store = Store(tmp_path / 'data')
    project = store.create_project('timing')
    audio = store.add_asset(project['id'], b'qa-audio', 'reference.wav')
    worker = Worker(store, mock=True, settings=Settings(tmp_path / 'settings'))
    canvas = store.canvas(project['id'])
    canvas['nodes'] = [{'id': 'video', 'position': {'x': 0, 'y': 0}, 'data': {'kind': 'video.image_to_video', 'config': {
        'prompt': prompt, 'seconds': 5, 'referenceIds': [audio['id']]}}}]
    store.save_canvas(project['id'], canvas, canvas['version'])
    submitted = []
    def submit(kind, config, inputs):
        submitted.append((kind, config, inputs))
        return 'qa-video-task'
    monkeypatch.setattr(worker.provider, 'submit', submit)
    run = worker.submit(project['id'])
    worker.tick()
    task = store.run(run['id'])['tasks'][0]
    assert task['status'] != 'failed', task.get('error')
    assert task['external_id'] == 'qa-video-task'
    assert len(submitted) == 1
    assert submitted[0][1]['prompt'] == prompt
    assert submitted[0][1]['seconds'] == 5
