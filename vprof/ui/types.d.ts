declare var require: (id: string) => any;
declare var module: { exports: any };
declare var global: any;

declare module 'd3' {
  const d3: any;
  export = d3;
}

declare module 'highlight.js/lib/core' {
  const hljs: {
    registerLanguage(name: string, language: any): void;
    highlight(code: string, options: { language: string }): { value: string };
  };
  export = hljs;
}

declare module 'highlight.js/lib/languages/python' {
  const python: any;
  export = python;
}

declare module 'node:assert/strict' {
  const assert: any;
  export = assert;
}

declare module 'node:test' {
  export function describe(name: string, fn: () => void): void;
  export function it(name: string, fn: () => void): void;
}

interface FlameGraphNode {
  stack: [string, string, number];
  sampleCount: number;
  samplePercentage: number;
  colorHash: number;
  children: FlameGraphNode[];
}

interface FlameGraphStats {
  objectName: string;
  sampleInterval: number;
  runTime: number;
  callStats: FlameGraphNode | Record<string, never>;
  totalSamples: number;
  timestamp: number;
}

type SourceLineEntry = ['line', number, string] | ['skip', number];

interface HeatmapEntry {
  name: string;
  runTime: number;
  srcCode: SourceLineEntry[];
  heatmap: Record<string, number>;
  executionCount: Record<string, number>;
}

interface CodeHeatmapStats {
  objectName: string;
  runTime: number;
  heatmaps: HeatmapEntry[];
}

type MemoryEvent = [number, number, number, string, string];

interface MemoryStats {
  objectName: string;
  totalEvents: number;
  codeEvents: MemoryEvent[];
  objectsCount: [string, number][];
  timestamp: number;
}

type ProfilerRecord = [
  string, number, string, number, number,
  number, number, number, number, number
];

interface ProfilerStats {
  objectName: string;
  totalTime: number;
  primitiveCalls: number;
  totalCalls: number;
  callStats: ProfilerRecord[];
  timestamp: number;
}

interface VprofProfilePayload {
  c?: FlameGraphStats;
  h?: CodeHeatmapStats;
  m?: MemoryStats;
  p?: ProfilerStats;
  version?: string;
}
