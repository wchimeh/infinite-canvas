import assert from 'node:assert/strict';
import test from 'node:test';

import { collectShotReferenceIds } from './shotReferences.ts';

test('按人物与场景顺序收集现存参考图并稳定去重', () => {
  const characters = [
    { id: 'alice', assetId: 'alice-main', referenceIds: ['shared', 'alice-extra', 'deleted'] },
    { id: 'bob', assetId: 'shared', referenceIds: ['bob-extra', 'alice-main'] },
  ];
  const locations = [
    { id: 'room', assetId: 'room-main', referenceIds: ['shared', 'room-extra', 'deleted'] },
  ];

  const result = collectShotReferenceIds({
    characterRefs: [
      { id: 'alice', revisionId: 'alice-main' },
      { id: 'bob', revisionId: 'shared' },
    ],
    locationRef: { id: 'room', revisionId: 'room-main' },
    characters,
    locations,
    availableAssetIds: new Set([
      'alice-main', 'shared', 'alice-extra', 'bob-extra', 'room-main', 'room-extra',
    ]),
  });

  assert.deepEqual(result, [
    'alice-main', 'shared', 'alice-extra', 'bob-extra', 'room-main', 'room-extra',
  ]);
});

test('缺失人物或场景档案时仍保留分镜显式引用', () => {
  const result = collectShotReferenceIds({
    characterRefs: [{ id: 'removed-character', revisionId: 'kept-character-image' }],
    locationRef: { id: 'removed-location', revisionId: 'kept-location-image' },
    characters: [],
    locations: [],
    availableAssetIds: new Set(['kept-character-image', 'kept-location-image']),
  });

  assert.deepEqual(result, ['kept-character-image', 'kept-location-image']);
});
