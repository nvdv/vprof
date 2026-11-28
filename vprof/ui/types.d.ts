declare var require: (id: string) => any;
declare var module: { exports: any };

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
