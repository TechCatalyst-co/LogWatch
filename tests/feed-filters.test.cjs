const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '../frontend/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

function dashboard() {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: '', textContent: '', addEventListener() {},
    });
    return elements.get(id);
  };
  const context = vm.createContext({
    document: { getElementById: get }, window: {},
    setInterval() {}, addEventListener() {},
  });
  // Run the actual dashboard script without starting network connections/timers.
  vm.runInContext(script.replace(/\nboot\(\);/, '\n'), context);
  vm.runInContext(`
    renderAll = () => { renderFilters(); renderFeed(); };
    S.events = [
      {id:'router', device:'Booth router', source:'router', level:0, ts:1},
      {id:'linux', device:'RHEL', source:'linux', level:3, ts:2},
    ];
    rowHTML = e => '<div data-id="' + e.id + '"></div>';
    renderAll();
  `, context);
  return {
    get,
    run: code => vm.runInContext(code, context),
    click: (id, selector, dataset = {}) => get(id).onclick({
      target: { closest: query => query === selector ? { dataset } : null },
    }),
  };
}

test('All clears a selected device and shows logs from every source', () => {
  const d = dashboard();
  d.click('devices', '.dev', { dev: 'Booth router' });
  assert.doesNotMatch(d.get('feed').innerHTML, /data-id="linux"/);
  assert.match(d.get('filters').innerHTML, /data-f="all" aria-pressed="false"/);
  d.click('filters', 'button', { f: 'all' });
  assert.match(d.get('feed').innerHTML, /data-id="linux"/);
  assert.match(d.get('feed').innerHTML, /data-id="router"/);
  assert.equal(d.get('feedNote').textContent, '');
});

test('selecting a device clears an incompatible source or severity filter', () => {
  for (const filter of ['linux', 'alerts']) {
    const d = dashboard();
    d.click('filters', 'button', { f: filter });
    d.click('devices', '.dev', { dev: 'Booth router' });
    assert.match(d.get('feed').innerHTML, /data-id="router"/);
    assert.doesNotMatch(d.get('feed').innerHTML, /data-id="linux"/);
  }
});

test('source and severity buttons apply globally after selecting a device', () => {
  for (const filter of ['linux', 'alerts']) {
    const d = dashboard();
    d.click('devices', '.dev', { dev: 'Booth router' });
    d.click('filters', 'button', { f: filter });
    assert.match(d.get('feed').innerHTML, /data-id="linux"/);
    assert.equal(d.get('feedNote').textContent, '');
  }
});

test('a filtered empty feed explains the filter and offers a working recovery', () => {
  const d = dashboard();
  d.run('S.events.forEach(e => e.level=0)');
  d.click('filters', 'button', { f: 'alerts' });
  assert.match(d.get('feed').innerHTML, /No matching logs/);
  assert.doesNotMatch(d.get('feed').innerHTML, /Waiting for logs/);
  d.click('feed', '[data-clear-filters]');
  assert.match(d.get('feed').innerHTML, /data-id="router"/);
});

test('source filters that disappear cannot remain invisibly active', () => {
  const d = dashboard();
  d.click('filters', 'button', { f: 'router' });
  d.run('S.events=S.events.filter(e => e.source === "linux"); renderAll()');
  assert.match(d.get('feed').innerHTML, /data-id="linux"/);
  assert.match(d.get('filters').innerHTML, /data-f="all" aria-pressed="true"/);
});

test('device toggle and clear chip both restore the full feed', () => {
  for (const clear of [false, true]) {
    const d = dashboard();
    d.click('devices', '.dev', { dev: 'Booth router' });
    if (clear) d.click('filters', 'button', { clear: '1' });
    else d.click('devices', '.dev', { dev: 'Booth router' });
    assert.match(d.get('feed').innerHTML, /data-id="linux"/);
    assert.match(d.get('feed').innerHTML, /data-id="router"/);
  }
});

test('an unfiltered empty feed retains its waiting state', () => {
  const d = dashboard();
  d.run('S.events=[]; renderAll()');
  assert.match(d.get('feed').innerHTML, /Waiting for logs/);
});
