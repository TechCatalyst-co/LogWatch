const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '../frontend/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

function dashboard(history = false) {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, {
      innerHTML: '', textContent: '', children: [], addEventListener() {}, classList: {remove() {}},
    });
    return elements.get(id);
  };
  const context = vm.createContext({
    document: { getElementById: get }, window: {},
    setInterval() {}, addEventListener() {}, URLSearchParams,
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
    mergeHistory(S.events);
    renderAll();
  `, context);
  if (!history) vm.runInContext('resetHistory = () => { H.events=S.events.filter(passes); renderAll(); };', context);
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
  assert.doesNotMatch(d.get('feedNote').textContent, /Booth router/);
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
    assert.doesNotMatch(d.get('feedNote').textContent, /Booth router/);
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

test('source filters remain available for history outside the live snapshot', () => {
  const d = dashboard();
  d.click('filters', 'button', { f: 'router' });
  d.run('S.events=S.events.filter(e => e.source === "linux"); renderAll()');
  assert.match(d.get('feed').innerHTML, /data-id="router"/);
  assert.match(d.get('filters').innerHTML, /data-f="router" aria-pressed="true"/);
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
  d.run('S.events=[]; H.events=[]; renderAll()');
  assert.match(d.get('feed').innerHTML, /Waiting for logs/);
});


test('device history requests stored logs outside the latest global snapshot', async () => {
  const d = dashboard(true);
  d.run(`api = async path => {
    if(!path.includes('device=Older+device')) throw new Error('missing device');
    return {events:[{id:'old',device:'Older device',source:'linux',rx:0}],next:[0,'old']};
  }; selectDevice('Older device');`);
  await d.run('Promise.resolve()');
  assert.match(d.get('feed').innerHTML, /data-id="old"/);
  assert.match(d.get('feed').innerHTML, /Load older logs/);
});

test('pagination keeps earlier rows and deduplicates overlapping live arrivals', async () => {
  const d = dashboard(true);
  d.run(`H.next=[1,'linux']; api = async path => {
    if(!path.includes('before=')) throw new Error('missing cursor');
    return {events:[{id:'linux',source:'linux',rx:1},{id:'older',source:'linux',rx:0}],next:null};
  };`);
  await d.run('loadHistory()');
  assert.equal((d.get('feed').innerHTML.match(/data-id="linux"/g)||[]).length, 1);
  assert.match(d.get('feed').innerHTML, /data-id="older"/);
  assert.match(d.get('feed').innerHTML, /data-id="router"/);
  assert.doesNotMatch(d.get('feed').innerHTML, /Load older logs/);
});

test('late responses from a previous device selection are ignored', async () => {
  const d = dashboard(true);
  d.run(`var finishOld; api = () => new Promise(resolve => {finishOld=resolve}); selectDevice('Old');`);
  d.run(`api = async () => ({events:[{id:'new',device:'New',rx:1}],next:null}); selectDevice('New');`);
  await d.run('Promise.resolve()');
  d.run(`finishOld({events:[{id:'stale',device:'Old',rx:0}],next:null})`);
  await d.run('Promise.resolve()');
  assert.match(d.get('feed').innerHTML, /data-id="new"/);
  assert.doesNotMatch(d.get('feed').innerHTML, /stale/);
});

test('failed history requests display retry and retain loaded rows', async () => {
  const d = dashboard(true);
  d.run('api = async () => {throw new Error("offline")}');
  await d.run('loadHistory()');
  assert.match(d.get('feed').innerHTML, /Couldn't load log history/);
  assert.match(d.get('feed').innerHTML, /data-id="linux"/);
  d.run('api = async () => ({events:[],next:null})');
  await d.click('feed', '[data-history]');
  assert.doesNotMatch(d.get('feed').innerHTML, /Couldn't load log history/);
});


test('KPI totals use database counts rather than the 400-row snapshot', () => {
  const d = dashboard();
  d.run(`applySnapshot({events:S.events,devices:[],total:2758,counts:{0:2000,1:100,2:600,3:58}}); renderKPIs()`);
  assert.match(d.get('kpis').innerHTML, /2,758/);
  assert.match(d.get('kpis').innerHTML, /73% everyday housekeeping/);
  assert.match(d.get('kpis').innerHTML, />600</);
  assert.match(d.get('kpis').innerHTML, />58</);
});

test('live arrivals use authoritative counts, including delayed events outside the snapshot', async () => {
  const d = dashboard();
  d.run(`applySnapshot({events:[],devices:[],total:1000,counts:{0:1000}});
    api = async () => ({events:[],devices:[{name:'RHEL',count:1000}],total:1000,counts:{0:1000}});
    pending=[{id:'already-counted',device:'RHEL',source:'linux',level:0,rx:1}]; flush();`);
  await d.run('Promise.resolve()');
  assert.equal(d.run('S.total'), 1000);
  assert.equal(d.run("S.devices.RHEL.count"), 1000);
  d.run(`api = async () => ({events:[],devices:[],total:1405,counts:{0:1000,3:405}})`);
  await d.run('refreshState()');
  assert.equal(d.run('S.total'), 1405);
  assert.equal(d.run('S.counts[3]'), 405);
});

test('refresh reconciles expiration and serializes concurrent requests', async () => {
  const d = dashboard();
  d.run(`applySnapshot({events:[],devices:[],total:1000,counts:{0:1000}});
    var calls=0, finish;
    api = () => {calls++; return new Promise(resolve => finish=resolve)};`);
  const first = d.run('refreshState()');
  await d.run('refreshState()');
  assert.equal(d.run('calls'), 1);
  d.run('finish({events:[],devices:[],total:0,counts:{}})');
  await first;
  assert.equal(d.run('S.total'), 0);
  assert.equal(d.run('Object.keys(S.devices).length'), 0);
});

test('a response started before reset cannot restore old counts', async () => {
  const d = dashboard();
  d.run('var finish; api = () => new Promise(resolve => finish=resolve)');
  const request = d.run('refreshState()');
  d.run(`stateGeneration++; S.total=0;
    finish({events:[],devices:[],total:999,counts:{0:999}})`);
  await request;
  assert.equal(d.run('S.total'), 0);
});
