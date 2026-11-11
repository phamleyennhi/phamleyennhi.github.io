/* TrackTok project page: the paper's plots, drawn as inline SVG in the page's own fonts.
 *
 * Usage: <div class="chart" data-chart="ucf-gfvd"></div>. Each chart gets an HTML legend, the
 * SVG plot (re-laid-out whenever its width changes), a hover / keyboard read-out, and a
 * collapsed data table, so no value depends on colour or hover alone.
 *
 * All numbers are the paper's: Table 1 / Fig. 1 (UCF-101 gFVD), Fig. 3 (Kinetics-600 frame
 * prediction), Fig. 4 left (UCF-101 rFVD) and Table A2 / Fig. 4 right (H100 latency).
 * "LARP" is LARP retrained with the paper's setup (LARP-dagger), as in the paper's figures.
 */
(function () {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';
  var COLOR = {
    tracktok: 'var(--c-tracktok)', larp: 'var(--c-larp)', adaptok: 'var(--c-adaptok)', other: 'var(--c-other)'
  };

  var CHARTS = {
    'ucf-gfvd': {
      kind: 'tokens',
      yLabel: 'gFVD ↓ (log scale)',
      xTicks: [32, 64, 128, 256, 512, 1024, 2048, 4096],
      yTicks: [100, 150, 200, 300, 500, 700, 1000, 1500],
      yDomain: [88, 1750],
      series: [
        { name: 'AdapTok', color: 'adaptok', label: { at: 0, dx: 10, dy: 4 },
          points: [[32, 1525], [64, 823], [128, 460], [256, 241], [512, 109]] },
        { name: 'LARP', color: 'larp', label: { at: 0, dx: 10, dy: -7 },
          points: [[32, 672], [64, 486], [128, 347], [256, 218], [512, 153], [1024, 102]] },
        { name: 'TrackTok', color: 'tracktok', label: { at: 0, dx: 0, dy: 26, anchor: 'middle' },
          points: [[32, 201], [64, 152], [128, 126], [256, 129], [512, 116], [1024, 117]] }
      ],
      others: [
        { name: 'Cosmos-S', x: 512, y: 191, dx: 9, dy: -8 },
        { name: 'MAGVIT-AR', x: 1024, y: 265, dx: -9, dy: -8, anchor: 'end' },
        { name: 'MAGVIT-v2-AR', x: 1280, y: 109, dx: 9, dy: 4 },
        { name: 'OmniTok', x: 4096, y: 191, dx: -9, dy: 4, anchor: 'end' },
        { name: 'CV-VAE', x: 4096, y: 262, dx: -9, dy: 4, anchor: 'end' }
      ],
      notes: [
        { type: 'gap', x: 32, y1: 672, y2: 201, text: '3.3× better', pos: 0.36 },
        { type: 'span', y: 201, x1: 256, x2: 32, text: '8× fewer tokens', atStart: true }
      ]
    },

    'k600-fp': {
      kind: 'tokens',
      yLabel: 'gFVD ↓ (log scale)',
      xTicks: [32, 64, 128, 256, 512, 1024, 2048, 4096],
      yTicks: [30, 50, 70, 100, 200, 300, 500, 700],
      yDomain: [21, 900],
      band: { x1: 32, x2: 256, text: 'Low-token regime' },
      series: [
        { name: 'AdapTok', color: 'adaptok', label: { at: 0, dx: 10, dy: 4 },
          points: [[32, 741.8], [128, 178.2], [256, 68.4]] },
        { name: 'LARP', color: 'larp', label: { at: 0, dx: 10, dy: -7 },
          points: [[32, 335.5], [128, 132.0], [256, 52.1]] },
        { name: 'TrackTok', color: 'tracktok', label: { at: 0, dx: 0, dy: 26, anchor: 'middle' },
          points: [[32, 68.5], [128, 40.7], [256, 43.6]] }
      ],
      others: [
        { name: 'CogVideo', x: 2065, y: 109.2, dx: -9, dy: 4, anchor: 'end' },
        { name: 'OmniTok', x: 4096, y: 32.9, dx: -9, dy: -9, anchor: 'end' }
      ],
      notes: [
        { type: 'gap', x: 32, y1: 335.5, y2: 68.5, text: '4.9× better' },
        { type: 'span', y: 32.9, x1: 4096, x2: 128, text: '32× fewer tokens than OmniTok', below: true }
      ]
    },

    'ucf-rfvd': {
      kind: 'tokens',
      yLabel: 'rFVD ↓ (log scale)',
      xTicks: [64, 128, 256, 512, 1024],
      yTicks: [20, 50, 100, 200, 500, 1000],
      yDomain: [20, 1400],
      series: [
        { name: 'AdapTok', color: 'adaptok', label: { at: 0, dx: 10, dy: 4 },
          points: [[64, 1122.22], [128, 581.1], [256, 285.3], [512, 60], [1024, 36]] },
        { name: 'LARP', color: 'larp', label: { at: 0, dx: 10, dy: -7 },
          points: [[64, 456.11], [128, 320.11], [256, 165.99], [512, 105.09], [1024, 53.94]] },
        { name: 'TrackTok', color: 'tracktok', label: { at: 0, dx: 0, dy: 26, anchor: 'middle' },
          points: [[64, 87.16], [128, 66.04], [256, 64.16], [512, 62.59], [1024, 62.79]] }
      ],
      others: [
        { name: 'Cosmos-S', x: 512, y: 104.5, dx: 0, dy: -30, anchor: 'middle', leader: true },
        { name: 'TATS', x: 1024, y: 162, dx: -9, dy: 4, anchor: 'end' },
        { name: 'MAGVIT-AR', x: 1024, y: 25, dx: -9, dy: 4, anchor: 'end' }
      ],
      notes: [
        { type: 'gap', x: 64, y1: 456.11, y2: 87.16, text: '5.2× better' }
      ]
    },

    'latency': {
      kind: 'bubble',
      xLabel: 'Generator latency per sample (ms, one H100)',
      yLabel: 'gFVD ↓',
      xTicks: [0, 250, 500, 750, 1000, 1250],
      yTicks: [50, 100, 150, 200, 250, 300, 350],
      xDomain: [0, 1330],
      yDomain: [40, 365],
      points: [
        { name: 'TrackTok', color: 'tracktok', tokens: 128, x: 66.8, y: 126, dx: 8, dy: 20 },
        { name: 'Cosmos-S', color: 'other', tokens: 512, x: 267.8, y: 191, dx: 0, dy: -20, anchor: 'middle' },
        { name: 'LARP', color: 'larp', tokens: 1024, x: 560.1, y: 102, dx: 0, dy: 32, anchor: 'middle' },
        { name: 'TATS', color: 'other', tokens: 1024, x: 634.3, y: 332, dx: 0, dy: -24, anchor: 'middle' },
        { name: 'MAGVIT-AR', color: 'other', tokens: 1024, x: 634.3, y: 265, dx: 22, dy: 4 },
        { name: 'AdapTok', color: 'adaptok', tokens: 1024, x: 1223.4, y: 67, dx: 0, dy: -24, anchor: 'middle' }
      ],
      notes: [
        { type: 'span', y: 126, x1: 560.1, x2: 66.8, text: '8× faster' }
      ]
    }
  };

  /* ------------------------------------------------------------------ helpers */
  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) if (attrs[k] !== undefined) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function text(parent, x, y, str, cls, anchor) {
    var t = el('text', { x: x, y: y, 'class': cls, 'text-anchor': anchor || 'start' }, parent);
    t.textContent = str;
    return t;
  }
  function html(tag, cls, parent, str) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (str !== undefined) n.textContent = str;
    if (parent) parent.appendChild(n);
    return n;
  }
  function fmt(v) { return v >= 100 ? String(Math.round(v)) : (Math.round(v * 10) / 10).toFixed(1); }
  function tokensLabel(t) { return String(t); }
  function arrowHead(g, x, y, dir) {          // small filled triangle whose tip is (x, y), pointing along dir
    var a = 7, s = 0.42;
    var p = [x - a * Math.cos(dir - s), y - a * Math.sin(dir - s), x, y,
             x - a * Math.cos(dir + s), y - a * Math.sin(dir + s)];
    el('polygon', { points: p.join(' '), 'class': 'note-head' }, g);
  }

  /* ------------------------------------------------------------------ token-budget charts */
  function drawTokens(svg, spec, W, H, M) {
    var compact = W < 380;                     // phones: drop notes and other-method names (still in tooltip + table)
    var lx = function (t) { return Math.log2(t); };
    var x0 = lx(spec.xTicks[0]) - 0.55, x1 = lx(spec.xTicks[spec.xTicks.length - 1]) + 0.35;
    var ly0 = Math.log10(spec.yDomain[0]), ly1 = Math.log10(spec.yDomain[1]);
    var X = function (t) { return M.l + (lx(t) - x0) / (x1 - x0) * (W - M.l - M.r); };
    var Y = function (v) { return M.t + (1 - (Math.log10(v) - ly0) / (ly1 - ly0)) * (H - M.t - M.b); };
    var g = el('g', {}, svg);

    if (spec.band) {
      var bx0 = M.l, bx1 = (X(spec.band.x2) + X(spec.band.x2 * 2)) / 2;
      el('rect', { x: bx0, y: M.t, width: bx1 - bx0, height: H - M.t - M.b, 'class': 'band' }, g);
      text(g, bx0 + 6, H - M.b - 7, spec.band.text, 'band-label', 'start');
    }
    spec.yTicks.forEach(function (v) {
      el('line', { x1: M.l, x2: W - M.r, y1: Y(v), y2: Y(v), 'class': 'grid' }, g);
      text(g, M.l - 8, Y(v) + 4, String(v), 'tick', 'end');
    });
    el('line', { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b, 'class': 'axis' }, g);
    spec.xTicks.forEach(function (t) { text(g, X(t), H - M.b + 18, tokensLabel(t), 'tick', 'middle'); });
    text(g, (M.l + W - M.r) / 2, H - 6, 'Number of tokens', 'axis-title', 'middle');
    var yl = text(g, 0, 0, spec.yLabel, 'axis-title', 'middle');
    yl.setAttribute('transform', 'translate(12,' + ((M.t + H - M.b) / 2) + ') rotate(-90)');

    (compact ? [] : spec.notes || []).forEach(function (n) {
      var ng = el('g', { 'class': 'note' }, g);
      if (n.type === 'gap') {                   // vertical arrow from the baseline's dot down to TrackTok's
        var nx = X(n.x), tip = Y(n.y2) - 9;
        el('line', { x1: nx, x2: nx, y1: Y(n.y1) + 8, y2: tip - 5, 'class': 'note-line' }, ng);
        arrowHead(ng, nx, tip, Math.PI / 2);
        text(ng, nx + 7, Y(n.y2) - (n.pos || 0.3) * (Y(n.y2) - Y(n.y1)) + 4, n.text, 'note-text', 'start');
      } else if (n.type === 'span') {
        var sy = Y(n.y), sx1 = X(n.x1), sx2 = X(n.x2);
        var dir = sx2 < sx1 ? Math.PI : 0, pad = 9;
        el('line', { x1: sx1 + (dir ? -pad : pad), x2: sx2 + (dir ? pad + 5 : -pad - 5), y1: sy, y2: sy, 'class': 'note-line' }, ng);
        arrowHead(ng, sx2 + (dir ? pad : -pad), sy, dir);
        if (n.atStart) {                         // text over the arrow's tail, clear of other notes
          text(ng, sx1 + (dir ? -pad : pad), sy - 7, n.text, 'note-text', dir ? 'end' : 'start');
        } else {
          text(ng, (sx1 + sx2) / 2, sy + (n.below ? 15 : -7), n.text, 'note-text', 'middle');
        }
      }
    });

    spec.others.forEach(function (o) {
      el('circle', { cx: X(o.x), cy: Y(o.y), r: 4.5, fill: COLOR.other, 'class': 'dot' }, g);
      if (compact) return;
      if (o.leader) el('line', { x1: X(o.x), x2: X(o.x) + o.dx, y1: Y(o.y) - 6, y2: Y(o.y) + o.dy + 4, 'class': 'leader' }, g);
      text(g, X(o.x) + o.dx, Y(o.y) + o.dy, o.name, 'other-label', o.anchor);
    });
    spec.series.forEach(function (s) {
      var d = s.points.map(function (p, i) { return (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ',' + Y(p[1]).toFixed(1); }).join('');
      el('path', { d: d, stroke: COLOR[s.color], 'class': 'line' }, g);
    });
    spec.series.forEach(function (s) {
      s.points.forEach(function (p) {
        el('circle', { cx: X(p[0]), cy: Y(p[1]), r: s.color === 'tracktok' ? 5.5 : 4.5, fill: COLOR[s.color], 'class': 'dot' }, g);
      });
      var lp = s.points[s.label.at];
      text(g, X(lp[0]) + s.label.dx, Y(lp[1]) + s.label.dy, s.name,
        'series-label' + (s.color === 'tracktok' ? ' ours' : ''), s.label.anchor);
    });

    // hover / keyboard read-out: snap to the nearest token budget that has data
    var xs = [];
    spec.series.forEach(function (s) { s.points.forEach(function (p) { if (xs.indexOf(p[0]) < 0) xs.push(p[0]); }); });
    spec.others.forEach(function (o) { if (xs.indexOf(o.x) < 0) xs.push(o.x); });
    xs.sort(function (a, b) { return a - b; });
    return {
      targets: xs.map(function (t) {
        var rows = [];
        spec.series.forEach(function (s) {
          s.points.forEach(function (p) { if (p[0] === t) rows.push({ name: s.name, color: s.color, v: p[1], key: 'line' }); });
        });
        spec.others.forEach(function (o) { if (o.x === t) rows.push({ name: o.name, color: 'other', v: o.y, key: 'dot' }); });
        rows.sort(function (a, b) { return a.v - b.v; });
        return { px: X(t), title: t + ' tokens', rows: rows };
      }),
      crosshair: true
    };
  }

  /* ------------------------------------------------------------------ latency bubble chart */
  function drawBubble(svg, spec, W, H, M) {
    var compact = W < 380;
    var X = function (v) { return M.l + (v - spec.xDomain[0]) / (spec.xDomain[1] - spec.xDomain[0]) * (W - M.l - M.r); };
    var Y = function (v) { return M.t + (1 - (v - spec.yDomain[0]) / (spec.yDomain[1] - spec.yDomain[0])) * (H - M.t - M.b); };
    var R = function (tokens) { return Math.max(5.5, 0.5 * Math.sqrt(tokens)); };   // area proportional to tokens
    var g = el('g', {}, svg);
    spec.yTicks.forEach(function (v) {
      el('line', { x1: M.l, x2: W - M.r, y1: Y(v), y2: Y(v), 'class': 'grid' }, g);
      text(g, M.l - 8, Y(v) + 4, String(v), 'tick', 'end');
    });
    el('line', { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b, 'class': 'axis' }, g);
    spec.xTicks.forEach(function (v) { text(g, X(v), H - M.b + 18, String(v), 'tick', 'middle'); });
    text(g, (M.l + W - M.r) / 2, H - 6, spec.xLabel, 'axis-title', 'middle');
    var yl = text(g, 0, 0, spec.yLabel, 'axis-title', 'middle');
    yl.setAttribute('transform', 'translate(12,' + ((M.t + H - M.b) / 2) + ') rotate(-90)');

    (compact ? [] : spec.notes || []).forEach(function (n) {
      var ng = el('g', { 'class': 'note' }, g);
      var sy = Y(n.y), sx1 = X(n.x1) - 4, sx2 = X(n.x2) + R(128) + 6;
      el('line', { x1: sx1, x2: sx2 + 5, y1: sy, y2: sy, 'class': 'note-line' }, ng);
      arrowHead(ng, sx2, sy, Math.PI);
      text(ng, (sx1 + sx2) / 2, sy - 7, n.text, 'note-text', 'middle');
    });

    // size key (top right)
    var kx = W - M.r - 6, ky = M.t + 6;
    text(g, kx, ky + 4, 'Tokens', 'tick', 'end');
    [1024, 512, 128].forEach(function (t, i) {
      var cy = ky + 30 + i * 32;
      el('circle', { cx: kx - 50, cy: cy, r: R(t), 'class': 'size-key' }, g);
      text(g, kx, cy + 4, String(t), 'tick', 'end');
    });

    var pts = spec.points.slice().sort(function (a, b) { return b.tokens - a.tokens; });   // big ones first
    pts.forEach(function (p) {
      el('circle', { cx: X(p.x), cy: Y(p.y), r: R(p.tokens), fill: COLOR[p.color], 'class': 'bubble' }, g);
    });
    spec.points.forEach(function (p) {
      if (compact && p.color === 'other') return;
      text(g, X(p.x) + p.dx, Y(p.y) + p.dy, p.name, p.color === 'other' ? 'other-label' : 'series-label' +
        (p.color === 'tracktok' ? ' ours' : ''), p.anchor);
    });
    return {
      targets: spec.points.map(function (p) {
        return { px: X(p.x), py: Y(p.y), r: Math.max(R(p.tokens) + 4, 12), title: p.name,
          rows: [{ name: 'gFVD', color: p.color, v: p.y, key: 'dot' },
                 { name: 'ms per sample', color: null, v: p.x },
                 { name: 'tokens', color: null, v: p.tokens }] };
      }),
      crosshair: false
    };
  }

  /* ------------------------------------------------------------------ legend, table, tooltip */
  function legend(root, spec) {
    var lg = html('div', 'chart-legend', root);
    var items = spec.kind === 'bubble'
      ? [['TrackTok', 'tracktok', 'dot'], ['LARP', 'larp', 'dot'], ['AdapTok', 'adaptok', 'dot'], ['Other methods', 'other', 'dot']]
      : spec.series.map(function (s) { return [s.name, s.color, 'line']; }).concat([['Other methods', 'other', 'dot']]);
    items.forEach(function (it) {
      var span = html('span', 'legend-item', lg);
      var key = html('span', 'key key-' + it[2], span);
      key.style.background = COLOR[it[1]];
      span.appendChild(document.createTextNode(it[0]));
    });
  }

  function table(root, spec) {
    var det = html('details', 'chart-data', root);
    html('summary', null, det, 'Show the numbers');
    var wrap = html('div', 'table-container', det);
    var tb = html('table', 'table is-narrow results-table', wrap);
    var head = html('tr', null, html('thead', null, tb));
    var body = html('tbody', null, tb);
    if (spec.kind === 'bubble') {
      ['Method', 'Tokens', 'gFVD', 'Latency (ms)'].forEach(function (h) { html('th', null, head, h); });
      spec.points.forEach(function (p) {
        var tr = html('tr', p.color === 'tracktok' ? 'ours' : null, body);
        [p.name, p.tokens, fmt(p.y), p.x.toFixed(1)].forEach(function (v) { html('td', null, tr, String(v)); });
      });
      return;
    }
    var xs = [];
    spec.series.concat(spec.others.map(function (o) { return { name: o.name, points: [[o.x, o.y]] }; }))
      .forEach(function (s) { s.points.forEach(function (p) { if (xs.indexOf(p[0]) < 0) xs.push(p[0]); }); });
    xs.sort(function (a, b) { return a - b; });
    html('th', null, head, 'Tokens');
    xs.forEach(function (t) { html('th', null, head, String(t)); });
    spec.series.concat(spec.others.map(function (o) { return { name: o.name, points: [[o.x, o.y]] }; }))
      .forEach(function (s) {
        var tr = html('tr', s.color === 'tracktok' ? 'ours' : null, body);
        html('td', null, tr, s.name);
        xs.forEach(function (t) {
          var p = s.points.filter(function (q) { return q[0] === t; })[0];
          html('td', null, tr, p ? fmt(p[1]) : '–');
        });
      });
  }

  function showTip(tip, target, plot, svgBox) {
    tip.textContent = '';
    html('div', 'tip-title', tip, target.title);
    target.rows.forEach(function (r) {
      var row = html('div', 'tip-row', tip);
      var key = html('span', 'key key-' + (r.key || 'none'), row);
      if (r.color) key.style.background = COLOR[r.color];
      html('strong', null, row, fmt(r.v));
      row.appendChild(document.createTextNode(' ' + r.name));
    });
    tip.hidden = false;
    var x = target.px + 14, y = (target.py !== undefined ? target.py : svgBox.height * 0.25) - 10;
    if (x + tip.offsetWidth > svgBox.width - 4) x = target.px - 14 - tip.offsetWidth;
    tip.style.left = Math.max(0, x) + 'px';
    tip.style.top = Math.max(0, Math.min(y, svgBox.height - tip.offsetHeight)) + 'px';
  }

  /* ------------------------------------------------------------------ render */
  function render(root) {
    var spec = CHARTS[root.getAttribute('data-chart')];
    if (!spec) return;
    var plot = root.querySelector('.chart-plot');
    var W = Math.round(plot.clientWidth);
    if (!W || W === root._w) return;
    root._w = W;
    var H = Math.round(Math.max(240, Math.min(380, W * (spec.kind === 'bubble' ? 0.66 : 0.62))));
    var M = { t: 12, r: 14, b: 44, l: 60 };
    plot.textContent = '';
    var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, role: 'img',
      'aria-label': root.getAttribute('aria-label') || '' }, plot);
    var info = spec.kind === 'bubble' ? drawBubble(svg, spec, W, H, M) : drawTokens(svg, spec, W, H, M);

    var cross = el('line', { y1: M.t, y2: H - M.b, 'class': 'crosshair', visibility: 'hidden' }, svg);
    var tip = html('div', 'chart-tip', plot);
    tip.hidden = true;
    var box = { width: W, height: H };
    var current = -1;
    function pick(i) {
      if (i < 0) { tip.hidden = true; cross.setAttribute('visibility', 'hidden'); current = -1; return; }
      current = i;
      var t = info.targets[i];
      if (info.crosshair) {
        cross.setAttribute('x1', t.px); cross.setAttribute('x2', t.px);
        cross.setAttribute('visibility', 'visible');
      }
      showTip(tip, t, plot, box);
    }
    var hit = el('rect', { x: 0, y: 0, width: W, height: H, fill: 'transparent' }, svg);
    hit.addEventListener('pointermove', function (e) {
      var r = svg.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top, best = -1, bd = Infinity;
      info.targets.forEach(function (t, i) {
        var d = info.crosshair ? Math.abs(t.px - px) : Math.hypot(t.px - px, t.py - py) - t.r;
        if (d < bd) { bd = d; best = i; }
      });
      pick(info.crosshair || bd <= 0 ? best : -1);
    });
    hit.addEventListener('pointerleave', function () { pick(-1); });
    svg.setAttribute('tabindex', '0');
    svg.addEventListener('focus', function () { pick(current < 0 ? 0 : current); });
    svg.addEventListener('blur', function () { pick(-1); });
    svg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        var n = info.targets.length;
        pick(((current < 0 ? 0 : current) + (e.key === 'ArrowRight' ? 1 : n - 1)) % n);
      } else if (e.key === 'Escape') { pick(-1); }
    });
  }

  function init() {
    document.querySelectorAll('.chart[data-chart]').forEach(function (root) {
      var spec = CHARTS[root.getAttribute('data-chart')];
      if (!spec) return;
      root.textContent = '';
      legend(root, spec);
      html('div', 'chart-plot', root);
      table(root, spec);
      render(root);
      if (window.ResizeObserver) new ResizeObserver(function () { render(root); }).observe(root);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
