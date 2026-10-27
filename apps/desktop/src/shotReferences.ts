import type { Profile, Shot } from './types';

type ShotReferenceInput = {
  characterRefs?: Shot['characterRefs'];
  locationRef?: Shot['locationRef'];
  characters: Profile[];
  locations: Profile[];
  availableAssetIds: ReadonlySet<string>;
};

export function collectShotReferenceIds(input: ShotReferenceInput): string[] {
  const ordered: string[] = [];
  const seen = new Set<string>();
  const append = (assetId?: string) => {
    if (!assetId || seen.has(assetId) || !input.availableAssetIds.has(assetId)) return;
    seen.add(assetId);
    ordered.push(assetId);
  };
  const appendProfile = (profile?: Profile) => {
    append(profile?.assetId);
    profile?.referenceIds?.forEach(append);
  };

  input.characterRefs?.forEach(reference => {
    append(reference.revisionId);
    appendProfile(input.characters.find(profile => profile.id === reference.id));
  });
  if (input.locationRef) {
    append(input.locationRef.revisionId);
    appendProfile(input.locations.find(profile => profile.id === input.locationRef?.id));
  }

  return ordered;
}
