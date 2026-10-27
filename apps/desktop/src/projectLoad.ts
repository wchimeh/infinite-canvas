export interface ProjectLoadGate {
  begin(): number;
  snapshot(): number;
  isLatest(request: number): boolean;
}

export function createProjectLoadGate(): ProjectLoadGate {
  let latest = 0;
  return {
    begin: () => ++latest,
    snapshot: () => latest,
    isLatest: request => request === latest,
  };
}
