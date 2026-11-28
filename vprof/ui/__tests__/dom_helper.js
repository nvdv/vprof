'use strict';

class FakeElement {
  constructor(tag, parent = null, datum = undefined) {
    this.tag = tag;
    this.parent = parent;
    this.datum = datum;
    this.attrs = {};
    this.styles = {};
    this.classes = new Set();
    this.children = [];
    this.handlers = {};
    this.htmlContent = '';
    this.textContent = '';
    this.scrollWidth = 1200;
    this.scrollHeight = 800;
  }

  get previousElementSibling() {
    if (!this.parent) {
      return null;
    }
    let idx = this.parent.children.indexOf(this);
    return idx > 0 ? this.parent.children[idx - 1] : null;
  }

  getAttribute(name) {
    return this.attrs[name] !== undefined ? this.attrs[name] : null;
  }

  setAttr(name, value) {
    this.attrs[name] = value;
    if (name === 'class') {
      this.classes = new Set(String(value).split(/\s+/).filter(Boolean));
    }
  }

  matchesSimple(selector) {
    if (selector === '*') {
      return true;
    }
    if (selector.startsWith('#')) {
      return this.attrs.id === selector.slice(1);
    }
    if (selector.startsWith('.')) {
      return this.classes.has(selector.slice(1));
    }
    return this.tag === selector;
  }

  queryAll(selector) {
    let parts = selector.trim().split(/\s+/);
    let results = [];
    let walk = (node, ancestors) => {
      for (let child of node.children) {
        let chain = ancestors.concat([child]);
        if (child.matchesSimple(parts[parts.length - 1])) {
          let ok = true;
          let pos = chain.length - 2;
          for (let p = parts.length - 2; p >= 0; p--) {
            let found = false;
            while (pos >= 0) {
              if (chain[pos].matchesSimple(parts[p])) {
                found = true;
                pos--;
                break;
              }
              pos--;
            }
            if (!found) {
              ok = false;
              break;
            }
          }
          if (ok) {
            results.push(child);
          }
        }
        walk(child, chain);
      }
    };
    walk(this, []);
    return results;
  }

  trigger(eventName) {
    let fn = this.handlers[eventName];
    if (fn) {
      let siblings = this.parent ? this.parent.children : [this];
      let idx = siblings.indexOf(this);
      fn(this.datum, idx >= 0 ? idx : 0, siblings);
    }
  }
}

class FakeSelection {
  constructor(elements) {
    this.elements_ = elements;
    /** @type {FakeElement[] | null} */
    this.parentElements_ = null;
  }

  node() {
    return this.elements_[0] || null;
  }

  nodes() {
    return this.elements_.slice();
  }

  append(tag) {
    let created = [];
    for (let el of this.elements_) {
      let child = new FakeElement(tag, el, el.datum);
      el.children.push(child);
      created.push(child);
    }
    return new FakeSelection(created);
  }

  attr(name, value) {
    if (value === undefined) {
      let first = this.node();
      return first ? first.getAttribute(name) : null;
    }
    for (let i = 0; i < this.elements_.length; i++) {
      let el = this.elements_[i];
      let v = typeof value === 'function'
        ? value(el.datum, i, this.elements_)
        : value;
      el.setAttr(name, v);
    }
    return this;
  }

  style(name, value) {
    for (let i = 0; i < this.elements_.length; i++) {
      let el = this.elements_[i];
      let v = typeof value === 'function'
        ? value(el.datum, i, this.elements_)
        : value;
      el.styles[name] = v;
    }
    return this;
  }

  classed(classNames, value) {
    let names = String(classNames).split(/\s+/).filter(Boolean);
    if (value === undefined) {
      let first = this.node();
      return first ? names.every((c) => first.classes.has(c)) : false;
    }
    for (let el of this.elements_) {
      for (let c of names) {
        if (value) {
          el.classes.add(c);
        } else {
          el.classes.delete(c);
        }
      }
      el.attrs['class'] = Array.from(el.classes).join(' ');
    }
    return this;
  }

  text(value) {
    for (let i = 0; i < this.elements_.length; i++) {
      let el = this.elements_[i];
      let v = typeof value === 'function'
        ? value(el.datum, i, this.elements_)
        : value;
      el.textContent = String(v);
    }
    return this;
  }

  html(value) {
    for (let i = 0; i < this.elements_.length; i++) {
      let el = this.elements_[i];
      let v = typeof value === 'function'
        ? value(el.datum, i, this.elements_)
        : value;
      el.htmlContent = String(v);
    }
    return this;
  }

  on(eventName, handler) {
    for (let el of this.elements_) {
      el.handlers[eventName] = handler;
    }
    return this;
  }

  selectAll(selector) {
    let found = [];
    for (let el of this.elements_) {
      found.push(...el.queryAll(selector));
    }
    let sel = new FakeSelection(found);
    sel.parentElements_ = this.elements_;
    return sel;
  }

  select(selector) {
    let all = this.selectAll(selector).nodes();
    return new FakeSelection(all.length ? [all[0]] : []);
  }

  data(items) {
    let parents = this.parentElements_ || this.elements_;
    return {
      enter: () => ({
        append: (tag) => {
          let created = [];
          let parent = parents[0];
          if (parent) {
            for (let item of items) {
              let child = new FakeElement(tag, parent, item);
              parent.children.push(child);
              created.push(child);
            }
          }
          return new FakeSelection(created);
        }
      })
    };
  }

  each(fn) {
    for (let i = 0; i < this.elements_.length; i++) {
      fn(this.elements_[i].datum, i, this.elements_);
    }
    return this;
  }

  call(fn) {
    if (typeof fn === 'function') {
      fn(this);
    }
    return this;
  }

  remove() {
    for (let el of this.elements_) {
      if (el.parent) {
        let idx = el.parent.children.indexOf(el);
        if (idx >= 0) {
          el.parent.children.splice(idx, 1);
        }
      }
    }
    return this;
  }
}

function installFakeDom(d3) {
  let body = new FakeElement('body');
  let docListeners = {};
  let origSelect = d3.select;
  let origSelectAll = d3.selectAll;
  let origAxisBottom = d3.axisBottom;
  let origAxisLeft = d3.axisLeft;
  let origZoom = d3.zoom;
  let origEventDesc = Object.getOwnPropertyDescriptor(d3, 'event');
  let origDocument = global.document;

  d3.select = (target) => {
    if (target === 'body') {
      return new FakeSelection([body]);
    }
    if (typeof target === 'string') {
      let matches = body.queryAll(target);
      return new FakeSelection(matches.length ? [matches[0]] : []);
    }
    return new FakeSelection(target ? [target] : []);
  };

  d3.selectAll = (selector) => new FakeSelection(body.queryAll(selector));

  let makeAxis = () => {
    let axis = () => {};
    axis.scale = () => axis;
    axis.ticks = () => axis;
    axis.tickFormat = () => axis;
    axis.tickValues = () => axis;
    return axis;
  };
  d3.axisBottom = makeAxis;
  d3.axisLeft = makeAxis;

  d3.zoom = () => {
    let z = () => {};
    z.scaleExtent = () => z;
    z.translateExtent = () => z;
    z.on = () => z;
    return z;
  };

  Object.defineProperty(d3, 'event', {
    configurable: true,
    get: () => ({pageX: 10, pageY: 20}),
  });

  global.document = {
    addEventListener: (eventName, fn) => {
      docListeners[eventName] = fn;
    },
  };

  return {
    body,
    dispatchDocumentClick: (target) => {
      if (docListeners.click) {
        docListeners.click({target});
      }
    },
    restore: () => {
      d3.select = origSelect;
      d3.selectAll = origSelectAll;
      d3.axisBottom = origAxisBottom;
      d3.axisLeft = origAxisLeft;
      d3.zoom = origZoom;
      if (origEventDesc) {
        Object.defineProperty(d3, 'event', origEventDesc);
      }
      global.document = origDocument;
    },
  };
}

module.exports = {
  FakeElement,
  FakeSelection,
  installFakeDom,
};
