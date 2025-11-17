// ==UserScript==
// @name         ORE.supply Smart Auto++ v3.0 (Enhanced & Fixed)
// @namespace    ore-auto-smart-plus-enhanced
// @version      3.0
// @description  Fixed bugs, added performance tracking, improved parsing, better risk management
// @match        https://ore.supply/*
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  /* ================= USER CONFIG ================= */
  const CFG = {
    // Core bankroll knobs
    basePerTileSOL: 0.0008,
    kStart: 2,
    maxRounds: 200,
    roundBudgetCapSOL: 0.010,

    // Access & timing
    gateTotalDeployed: 20.0,
    snipeAtSec: 5,
    minMsBetweenClicks: 120,
    clearSelectedBeforePick: true,

    // Emptiness learning (bandit)
    eps: 0.10,
    ewmaAlpha: 0.25,
    emptinessGateXAvg: 0.90,

    // Low-crowd preference
    preferLowCrowd: true,
    minersWeight: 0.45,
    minersGateMax: 9999,

    // Late-surge shield
    surgeLookbackSec: 6,
    surgeMinDeltaSOL: 2.0,

    // Motherlode mode
    motherlodeBoostOn: true,
    motherlodeThresholdORE: 50,
    mlSizeMultiplier: 1.15,  // REDUCED from 1.20 (less aggressive)
    mlAddTiles: 1,
    perTileMaxSOL: 0.0020,

    // Per-round size scaling (MORE CONSERVATIVE)
    sizeScaleGamma: 1.15,     // REDUCED from 1.30
    sizeScaleMin: 0.80,       // INCREASED from 0.75
    sizeScaleMax: 1.35,       // REDUCED from 1.60

    // Autos
    adaptKByEmptiness: true,

    // Wallet-safe / UI-only modes
    walletSafeMode: true,
    highlightOnly: false,
    simMode: false,

    // Optional: Auto-claim SOL only
    autoClaim: false,
    claimEveryXRounds: 40,
    minClaimSol: 0.05,
    claimCooldownMs: 60_000,
    avoidClaimInsideSnipe: true,

    // Safety & logging
    coolDownAfterSkips: true,
    skipStrikeLimit: 2,
    coolDownMs: 6000,
    log: true,
    logVerbose: false  // NEW: detailed per-round EV logging
  };

  /* ================= PERSISTENT BANDIT ================= */
  const STORE_KEY = 'ORE_SMART_PLUS_BANDIT_V30';
  const STATS_KEY = 'ORE_SMART_PLUS_STATS_V30';
  let bandit = loadBandit();
  let stats = loadStats();

  function loadBandit() {
    try {
      const j = localStorage.getItem(STORE_KEY);
      if (j) return JSON.parse(j);
    } catch (e) { }
    const arms = {};
    for (let i = 1; i <= 25; i++) {
      arms[i] = { ewmaW: 0.6, seen: 0, lastSeenRound: 0 };
    }
    return { arms, rounds: 0 };
  }

  function saveBandit() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(bandit));
    } catch (e) {
      log('Failed to save bandit', e);
    }
  }

  function loadStats() {
    try {
      const j = localStorage.getItem(STATS_KEY);
      if (j) return JSON.parse(j);
    } catch (e) { }
    return {
      sessions: [],
      currentSession: null,
      lifetime: { rounds: 0, deployed: 0, claimed: 0, netROI: 0 }
    };
  }

  function saveStats() {
    try {
      localStorage.setItem(STATS_KEY, JSON.stringify(stats));
    } catch (e) {
      log('Failed to save stats', e);
    }
  }

  function startSession() {
    stats.currentSession = {
      startTime: now(),
      rounds: 0,
      deployed: 0,
      claimed: 0,
      skipped: 0,
      errors: 0,
      roundDetails: []
    };
  }

  function endSession() {
    if (!stats.currentSession) return;
    stats.currentSession.endTime = now();
    stats.currentSession.durationMin = (stats.currentSession.endTime - stats.currentSession.startTime) / 60000;
    stats.sessions.push(stats.currentSession);

    // Update lifetime
    stats.lifetime.rounds += stats.currentSession.rounds;
    stats.lifetime.deployed += stats.currentSession.deployed;
    stats.lifetime.claimed += stats.currentSession.claimed;
    stats.lifetime.netROI = stats.lifetime.deployed > 0
      ? ((stats.lifetime.claimed - stats.lifetime.deployed) / stats.lifetime.deployed * 100)
      : 0;

    stats.currentSession = null;
    saveStats();
  }

  function recordRound(amt, k, picked, outcome = 'deployed') {
    if (!stats.currentSession) return;
    const detail = {
      round: stats.currentSession.rounds + 1,
      timestamp: now(),
      amount: amt,
      k: k,
      tiles: picked,
      outcome: outcome
    };
    stats.currentSession.roundDetails.push(detail);

    if (outcome === 'deployed') {
      stats.currentSession.rounds += 1;
      stats.currentSession.deployed += amt * k;
    } else if (outcome === 'skipped') {
      stats.currentSession.skipped += 1;
    } else if (outcome === 'error') {
      stats.currentSession.errors += 1;
    }

    saveStats();
  }

  /* ================= HELPERS ================= */
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const log = (...a) => { if (CFG.log) console.log('[ORE++ v3.0]', ...a); };
  const logV = (...a) => { if (CFG.logVerbose) console.log('[ORE++ VERBOSE]', ...a); };
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const now = () => Date.now();

  /* ================= DOM SELECTORS ================= */
  const SEL = {
    tileCandidates: [
      'button[data-tile]', 'div[data-tile]', 'button[data-index]', 'div[data-index]',
      'button.tile', 'div.tile', 'button.block', 'div.block',
      'main button', 'main div[role="button"]'
    ],
    amountInputs: ['input[type="number"]', 'input[placeholder*="SOL"]', 'input[placeholder*="amount"]'],
    deployButtons: ['button', 'div[role="button"]'],
    totalDeployedScope: 'body',
    timerScope: 'body',
    motherlodeScope: 'body',
    rewardsScope: 'body'
  };

  function qsa(sel, root = document) {
    return Array.from(root.querySelectorAll(sel));
  }

  /* ================= PARSERS (IMPROVED) ================= */
  function getTiles() {
    const all = [];
    for (const s of SEL.tileCandidates) {
      for (const el of qsa(s)) {
        if (el instanceof HTMLElement) all.push(el);
      }
    }
    const uniq = [], seen = new Set();
    for (const el of all) {
      const idx = parseTileIndex(el);
      if (idx && idx >= 1 && idx <= 25 && !seen.has(el)) {
        uniq.push(el);
        seen.add(el);
      }
    }
    return uniq;
  }

  function parseTileIndex(el) {
    const t = (el.innerText || '').trim();
    // Try #N format
    const m1 = t.match(/#\s*(\d{1,2})\b/);
    if (m1) return parseInt(m1[1], 10);
    // Try standalone number
    const m2 = t.match(/^\s*(\d{1,2})\s*$/);
    if (m2) return parseInt(m2[1], 10);
    // Try data attributes
    const di = el.getAttribute('data-index') || el.getAttribute('data-tile');
    if (di && /^\d{1,2}$/.test(di)) return parseInt(di, 10);
    return null;
  }

  // IMPROVED: Better validation and multiple parsing strategies
  function parseTileStakeAndMiners(el) {
    const t = (el.innerText || '').replace(/,/g, ' ');

    // Strategy 1: Look for explicit "X SOL" and "Y miners" patterns
    const solMatch = t.match(/(\d+\.\d+)\s*SOL/i);
    const minersMatch = t.match(/(\d+)\s*miners?/i);

    if (solMatch && minersMatch) {
      return {
        W: parseFloat(solMatch[1]),
        miners: parseInt(minersMatch[1], 10)
      };
    }

    if (solMatch) {
      return {
        W: parseFloat(solMatch[1]),
        miners: null
      };
    }

    // Strategy 2: Fallback to heuristic (last decimal = stake, integer before = miners)
    const nums = (t.match(/(\d+\.\d+|\d+)/g) || [])
      .map(x => x.includes('.') ? parseFloat(x) : parseInt(x, 10));

    let W = Number.POSITIVE_INFINITY, miners = null;

    if (nums.length > 0) {
      // Find last number that looks like SOL amount (has decimal and reasonable range)
      for (let i = nums.length - 1; i >= 0; i--) {
        const n = nums[i];
        if (typeof n === 'number' && !isNaN(n) && n > 0 && n < 1000) {
          // If it's a decimal, likely the stake
          if (!Number.isInteger(n) && n < 100) {
            W = n;
            // Look for integer before it as miners
            if (i > 0 && Number.isInteger(nums[i - 1]) && nums[i - 1] < 10000) {
              miners = nums[i - 1];
            }
            break;
          }
        }
      }

      // If no decimal found, use last number as stake
      if (!Number.isFinite(W) && nums.length > 0) {
        const last = nums[nums.length - 1];
        if (Number.isFinite(last) && last > 0) {
          W = last;
        }
      }
    }

    // Validation
    if (!Number.isFinite(W) || W <= 0 || W > 1000) {
      W = Number.POSITIVE_INFINITY; // Mark as invalid
    }
    if (miners !== null && (miners < 0 || miners > 100000)) {
      miners = null; // Invalid miners count
    }

    return { W, miners };
  }

  function findAmountInput() {
    for (const s of SEL.amountInputs) {
      const els = qsa(s).filter(e => e.offsetParent !== null && !e.disabled);
      if (els[0]) return els[0];
    }
    return null;
  }

  function setAmount(val) {
    const inp = findAmountInput();
    if (!inp) {
      log('Amount input not found');
      return false;
    }
    inp.focus();
    inp.value = String(val);
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    inp.blur();
    return true;
  }

  function findDeployButton() {
    const cands = [];
    for (const s of SEL.deployButtons) cands.push(...qsa(s));
    const ok = cands.filter(el =>
      el.offsetParent !== null &&
      !el.disabled &&
      /deploy/i.test(el.innerText || '')
    );
    return ok[0] || null;
  }

  async function click(el) {
    if (!el) return false;
    el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    await sleep(50);
    if (!CFG.simMode) el.click();
    await sleep(CFG.minMsBetweenClicks);
    return true;
  }

  async function clearSelections(tiles) {
    const selected = tiles.filter(el => {
      const ap = el.getAttribute('aria-pressed');
      if (ap && ap.toString() === 'true') return true;
      const cls = (el.className || '').toString().toLowerCase();
      return /\bselected\b|\bactive\b/.test(cls);
    });
    for (const el of selected) await click(el);
  }

  function readTotalDeployed() {
    const txt = (document.querySelector(SEL.totalDeployedScope)?.innerText || '');
    const m = txt.match(/Total\s*deployed[^\d]*([\d]+\.?\d*|\d+)/i);
    const val = m ? parseFloat(m[1]) : null;
    return (val !== null && val >= 0 && val < 100000) ? val : null;
  }

  function readTimerSec() {
    const txt = (document.querySelector(SEL.timerScope)?.innerText || '');
    // Try MM:SS format
    const m1 = txt.match(/Time\s*remaining[\s\S]*?(\d{1,2})[:.]\s*(\d{2})/i);
    if (m1) {
      return parseInt(m1[1], 10) * 60 + parseInt(m1[2], 10);
    }
    // Try seconds only
    const m2 = txt.match(/Time\s*remaining[\s\S]*?(\d+)\s*s/i);
    if (m2) {
      return parseInt(m2[1], 10);
    }
    return null;
  }

  function readMotherlode() {
    const txt = (document.querySelector(SEL.motherlodeScope)?.innerText || '');
    const m = txt.match(/Motherlode[\s\S]*?([\d]+\.?\d*)/i);
    const val = m ? parseFloat(m[1]) : null;
    return (val !== null && val >= 0) ? val : null;
  }

  function readClaimableSol() {
    const txt = (document.querySelector(SEL.rewardsScope)?.innerText || '');
    const m = txt.match(/Rewards[\s\S]{0,400}?SOL[^\d]*([\d]+\.?\d*)/i);
    const val = m ? parseFloat(m[1]) : 0;
    return (val >= 0) ? val : 0;
  }

  /* ================= LEARNING (emptiness) ================= */
  function updateEWMA(idx, observedW) {
    if (!Number.isFinite(observedW) || observedW <= 0) return;

    const arm = bandit.arms[idx] || (bandit.arms[idx] = {
      ewmaW: observedW,
      seen: 0,
      lastSeenRound: bandit.rounds
    });

    arm.ewmaW = arm.seen
      ? (CFG.ewmaAlpha * observedW + (1 - CFG.ewmaAlpha) * arm.ewmaW)
      : observedW;
    arm.seen += 1;
    arm.lastSeenRound = bandit.rounds;
  }

  /* ================= PICK LOGIC (FIXED) ================= */
  function pickTilesSmart(tiles, D) {
    const avg = (D && D > 0) ? (D / 25) : 0.6;

    const rows = tiles.map(el => {
      const idx = parseTileIndex(el);
      const { W, miners } = parseTileStakeAndMiners(el);

      // Update learning
      if (Number.isFinite(W) && W > 0) updateEWMA(idx, W);

      const arm = bandit.arms[idx];
      const prior = arm?.ewmaW ?? 0.6;

      // FIX #1: Exploration - occasionally pick random tiles by giving them good (low) scores
      let emptinessScore;
      if (Math.random() < CFG.eps) {
        // Exploration: assign a random score in the lower range to encourage trying
        emptinessScore = Math.random() * avg * 0.5; // 0 to 50% of average
      } else {
        // Exploitation: use learned prior
        emptinessScore = prior;
      }

      // Crowd score: fewer miners = better (lower score)
      let crowdScore = 0.5;
      if (miners !== null && miners >= 0) {
        // Normalize: 0 miners = 0, 500+ miners = 1
        crowdScore = clamp(miners / 500, 0, 1);
      }

      // Combined score: lower is better
      const combined = (1 - CFG.minersWeight) * emptinessScore + CFG.minersWeight * crowdScore;

      return {
        el,
        idx,
        Wobs: W,
        miners,
        prior,
        emptinessScore,
        crowdScore,
        combined
      };
    }).filter(r => r.idx);

    // Sort: lower combined = better
    rows.sort((a, b) => {
      const cmp = a.combined - b.combined;
      if (cmp !== 0) return cmp;
      // Tiebreak: prefer observed lower W
      if (Number.isFinite(a.Wobs) && Number.isFinite(b.Wobs)) {
        return a.Wobs - b.Wobs;
      }
      return a.idx - b.idx;
    });

    // Adapt k by emptiness
    let kUse = CFG.kStart;
    if (CFG.adaptKByEmptiness && Number.isFinite(avg) && avg > 0) {
      const obs = rows
        .map(r => r.Wobs)
        .filter(w => Number.isFinite(w) && w > 0)
        .sort((a, b) => a - b);

      if (obs.length >= 5) {
        const med = obs[Math.floor(obs.length / 2)];
        // IMPROVED thresholds: more conservative
        if (med < 0.40 * avg) {
          kUse = 1; // Very empty board: focus on best tile
        } else if (med < 0.75 * avg) {
          kUse = 2; // Moderately empty: 2 tiles
        } else {
          kUse = 3; // Crowded: spread risk across 3 tiles
        }
      }
    }

    // Apply emptiness gate (soft filter)
    let filtered = rows;
    if (Number.isFinite(avg) && avg > 0) {
      const gateW = CFG.emptinessGateXAvg * avg;
      const soft = rows.filter(r => {
        const w = Number.isFinite(r.Wobs) ? r.Wobs : r.prior;
        return w < gateW;
      });
      if (soft.length >= kUse) {
        filtered = soft;
        logV(`Applied emptiness gate: ${soft.length}/${rows.length} tiles < ${gateW.toFixed(3)}`);
      }
    }

    // Apply hard crowd gate (optional)
    if (CFG.preferLowCrowd && CFG.minersGateMax < 9999) {
      const g = filtered.filter(r =>
        r.miners === null || r.miners <= CFG.minersGateMax
      );
      if (g.length >= kUse) {
        filtered = g;
        logV(`Applied crowd gate: ${g.length}/${filtered.length} tiles ≤ ${CFG.minersGateMax} miners`);
      }
    }

    const chosen = filtered.slice(0, kUse);

    logV(`Pick summary: ${chosen.length} tiles chosen from ${rows.length} total (avg W=${avg.toFixed(3)})`);
    chosen.forEach(r => {
      logV(`  Tile #${r.idx}: W=${Number.isFinite(r.Wobs) ? r.Wobs.toFixed(3) : 'n/a'}, miners=${r.miners ?? 'n/a'}, score=${r.combined.toFixed(4)}`);
    });

    return { chosen, kUse, avg };
  }

  /* ================= SIZE (MORE CONSERVATIVE) ================= */
  function computePerTileSize(chosen, avg) {
    let amt = CFG.basePerTileSOL;

    // FIX #3: More conservative size scaling
    if (chosen.length && Number.isFinite(avg) && avg > 0) {
      const Ws = chosen
        .map(r => Number.isFinite(r.Wobs) && r.Wobs > 0 ? r.Wobs : r.prior)
        .filter(w => w > 0)
        .sort((a, b) => a - b);

      if (Ws.length > 0) {
        const med = Ws[Math.floor(Ws.length / 2)];
        // Scale factor: if tiles are emptier, bet slightly more
        // But cap the scaling to avoid over-betting
        const ratio = clamp(avg / med, 0.5, 2.5);
        const scale = clamp(
          Math.pow(ratio, CFG.sizeScaleGamma),
          CFG.sizeScaleMin,
          CFG.sizeScaleMax
        );
        amt = clamp(amt * scale, CFG.basePerTileSOL * 0.5, CFG.perTileMaxSOL);

        logV(`Size scaling: med=${med.toFixed(3)}, avg=${avg.toFixed(3)}, ratio=${ratio.toFixed(2)}, scale=${scale.toFixed(2)}, amt=${amt.toFixed(6)}`);
      }
    }

    // Motherlode boost (modest)
    const ml = readMotherlode();
    if (CFG.motherlodeBoostOn && Number.isFinite(ml) && ml >= CFG.motherlodeThresholdORE) {
      const prevAmt = amt;
      amt = clamp(amt * CFG.mlSizeMultiplier, 0, CFG.perTileMaxSOL);
      logV(`ML boost: ${prevAmt.toFixed(6)} → ${amt.toFixed(6)} (ML=${ml.toFixed(2)} ORE)`);
    }

    return amt;
  }

  /* ================= SURGE SHIELD ================= */
  const surgeBuf = [];

  function trackD(D) {
    if (!Number.isFinite(D) || D < 0) return;
    const t = now();
    surgeBuf.push({ t, D });
    const cutoff = t - CFG.surgeLookbackSec * 1000;
    while (surgeBuf.length && surgeBuf[0].t < cutoff) {
      surgeBuf.shift();
    }
  }

  function surgeActive() {
    if (surgeBuf.length < 2) return false;
    const oldest = surgeBuf[0];
    const newest = surgeBuf[surgeBuf.length - 1];
    const delta = newest.D - oldest.D;
    const timeDiff = (newest.t - oldest.t) / 1000;

    if (delta >= CFG.surgeMinDeltaSOL) {
      logV(`Surge detected: +${delta.toFixed(2)} SOL in ${timeDiff.toFixed(1)}s`);
      return true;
    }
    return false;
  }

  /* ================= AUTO-CLAIM (SOL only) ================= */
  let lastClaimTs = 0;
  let deploysSinceClaim = 0;

  function findClaimSolOnlyButton() {
    const cands = qsa('button,div[role="button"],a').filter(el =>
      el.offsetParent !== null && !el.disabled
    );
    return cands.find(el => {
      const t = (el.innerText || '').trim();
      const hasClaim = /claim/i.test(t);
      const hasSOL = /\bsol\b/i.test(t);
      const hasORE = /\bore\b/i.test(t);
      const refine = /refine/i.test(t);
      return hasClaim && hasSOL && !hasORE && !refine;
    }) || null;
  }

  function findConfirmButton() {
    const cands = qsa('button,div[role="button"]');
    return cands.find(el =>
      el.offsetParent !== null &&
      !el.disabled &&
      /(confirm|approve|ok)/i.test(el.innerText || '')
    ) || null;
  }

  async function maybeAutoClaim(secs) {
    if (!CFG.autoClaim || CFG.walletSafeMode) return false;

    const tooSoon = (now() - lastClaimTs) < CFG.claimCooldownMs;
    if (tooSoon) return false;

    if (CFG.avoidClaimInsideSnipe && secs !== null && secs <= (CFG.snipeAtSec + 2)) {
      return false;
    }

    const claimable = readClaimableSol();
    const roundsTrigger = (CFG.claimEveryXRounds > 0) && (deploysSinceClaim >= CFG.claimEveryXRounds);
    const amountTrigger = (Number.isFinite(claimable) && claimable >= CFG.minClaimSol);

    if (!roundsTrigger && !amountTrigger) return false;

    const btn = findClaimSolOnlyButton();
    if (!btn) {
      logV('Auto-claim: SOL button not found');
      return false;
    }

    try {
      await click(btn);
      await sleep(200);
      const confirm = findConfirmButton();
      if (confirm) {
        await click(confirm);
      }

      lastClaimTs = now();
      deploysSinceClaim = 0;

      if (stats.currentSession) {
        stats.currentSession.claimed += claimable;
        saveStats();
      }

      log(`Auto-claimed ${claimable.toFixed(4)} SOL`);
      setStatus(`auto-claimed ${claimable.toFixed(4)} SOL`);
      return true;
    } catch (e) {
      log('Auto-claim error', e);
      return false;
    }
  }

  /* ================= HUD (ENHANCED) ================= */
  function makeHUD() {
    const box = document.createElement('div');
    box.id = 'ore-smart-auto-plus';
    box.style.cssText = `
      position:fixed;left:16px;bottom:16px;z-index:999999;width:380px;max-height:90vh;overflow-y:auto;
      background:rgba(9,13,20,.96);color:#e7ecf3;border:1px solid #223049;border-radius:14px;
      padding:14px;font:12px/1.5 system-ui,-apple-system,Segoe UI,Roboto;box-shadow:0 10px 40px rgba(0,0,0,.5);
    `;
    box.innerHTML = `
      <div style="font-weight:700;font-size:14px;margin-bottom:8px;color:#7ee7ff;">ORE Smart Auto++ v3.0</div>

      <div style="background:rgba(30,40,60,.4);padding:8px;border-radius:8px;margin-bottom:10px;font-size:11px;">
        <div style="color:#93a0b4;margin-bottom:4px;">Session Stats</div>
        <div id="p-session-stats" style="color:#cfe7ff;line-height:1.6;">
          Rounds: <span id="p-stat-rounds">0</span> |
          Deployed: <span id="p-stat-deployed">0</span> SOL<br>
          Claimed: <span id="p-stat-claimed">0</span> SOL |
          ROI: <span id="p-stat-roi">–</span>
        </div>
      </div>

      <details style="margin-bottom:8px;">
        <summary style="cursor:pointer;font-weight:600;padding:4px 0;color:#7ee7ff;">Core Settings</summary>
        <div style="padding:8px 0;">
          <label style="display:block;margin:6px 0;">Base per-tile (SOL)
            <input id="p-amt" type="number" step="0.000001" value="${CFG.basePerTileSOL}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
          <label style="display:block;margin:6px 0;">k start
            <select id="p-k" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
              <option ${CFG.kStart===1?'selected':''}>1</option>
              <option ${CFG.kStart===2?'selected':''}>2</option>
              <option ${CFG.kStart===3?'selected':''}>3</option>
            </select>
          </label>
          <label style="display:block;margin:6px 0;">Max rounds
            <input id="p-max" type="number" value="${CFG.maxRounds}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
          <label style="display:block;margin:6px 0;">Round cap (SOL)
            <input id="p-cap" type="number" step="0.001" value="${CFG.roundBudgetCapSOL}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
          <label style="display:block;margin:6px 0;">Gate D ≤ (0=off)
            <input id="p-gateD" type="number" step="0.1" value="${CFG.gateTotalDeployed}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
          <label style="display:block;margin:6px 0;">Snipe at ≤ sec
            <input id="p-snipe" type="number" value="${CFG.snipeAtSec}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
        </div>
      </details>

      <div style="display:flex;gap:8px;margin:8px 0;flex-wrap:wrap;">
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-adapt" type="checkbox" ${CFG.adaptKByEmptiness?'checked':''}> adapt k
        </label>
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-crowd" type="checkbox" ${CFG.preferLowCrowd?'checked':''}> low-crowd
        </label>
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-ml" type="checkbox" ${CFG.motherlodeBoostOn?'checked':''}> ML boost
        </label>
      </div>

      <hr style="border:none;border-top:1px solid rgba(34,48,73,.5);margin:10px 0;">

      <div style="display:flex;gap:8px;margin:8px 0;flex-wrap:wrap;">
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-safe" type="checkbox" ${CFG.walletSafeMode?'checked':''}> wallet-safe
        </label>
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-high" type="checkbox" ${CFG.highlightOnly?'checked':''}> highlight-only
        </label>
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-sim" type="checkbox" ${CFG.simMode?'checked':''}> simulate
        </label>
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
          <input id="p-verbose" type="checkbox" ${CFG.logVerbose?'checked':''}> verbose
        </label>
      </div>

      <details style="margin:8px 0;">
        <summary style="cursor:pointer;font-weight:600;padding:4px 0;color:#93a0b4;">Auto-Claim (SOL)</summary>
        <div style="padding:8px 0;">
          <div style="display:flex;gap:8px;margin:6px 0;flex-wrap:wrap;">
            <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
              <input id="p-autoclaim" type="checkbox" ${CFG.autoClaim?'checked':''}> enable
            </label>
            <label style="display:flex;align-items:center;gap:4px;font-size:11px;">
              <input id="p-avoid" type="checkbox" ${CFG.avoidClaimInsideSnipe?'checked':''}> avoid snipe
            </label>
          </div>
          <label style="display:block;margin:6px 0;font-size:11px;">Claim every X rounds
            <input id="p-claimX" type="number" value="${CFG.claimEveryXRounds}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
          <label style="display:block;margin:6px 0;font-size:11px;">Min claim SOL
            <input id="p-claimMin" type="number" step="0.001" value="${CFG.minClaimSol}" style="width:100%;margin:2px 0;padding:4px;background:#0e1523;border:1px solid #2b3b5a;color:#fff;border-radius:4px;">
          </label>
        </div>
      </details>

      <div id="p-status" style="color:#93a0b4;margin:10px 0;padding:8px;background:rgba(20,30,50,.4);border-radius:6px;font-size:11px;min-height:20px;">idle</div>

      <div style="display:flex;gap:8px;margin:8px 0;">
        <button id="p-start" style="flex:1;padding:8px;border:1px solid #2b5a7a;background:#0e2533;color:#7ee7ff;border-radius:8px;cursor:pointer;font-weight:600;font-size:12px;">
          Start
        </button>
        <button id="p-stop" style="flex:1;padding:8px;border:1px solid #5a3a3a;background:#2a1010;color:#ff9090;border-radius:8px;cursor:pointer;font-weight:600;font-size:12px;">
          Stop
        </button>
      </div>

      <div style="margin-top:8px;font-size:11px;color:#93a0b4;">
        Current picks: <span id="p-picked" style="color:#cfe7ff;font-weight:600;">–</span>
      </div>

      <details style="margin-top:10px;">
        <summary style="cursor:pointer;font-size:11px;color:#7a8a9a;padding:4px 0;">Advanced Actions</summary>
        <div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap;">
          <button id="p-export" style="flex:1;padding:6px;border:1px solid #2b3b5a;background:#0e1523;color:#93a0b4;border-radius:6px;cursor:pointer;font-size:10px;">
            Export Stats
          </button>
          <button id="p-reset" style="flex:1;padding:6px;border:1px solid #5a3a3a;background:#1a0e0e;color:#ffa0a0;border-radius:6px;cursor:pointer;font-size:10px;">
            Reset Learning
          </button>
        </div>
      </details>
    `;
    document.body.appendChild(box);

    const $ = id => document.getElementById(id);

    $('p-start').onclick = () => {
      CFG.basePerTileSOL = parseFloat($('p-amt').value) || CFG.basePerTileSOL;
      CFG.kStart = parseInt($('p-k').value, 10) || 2;
      CFG.maxRounds = parseInt($('p-max').value, 10) || 200;
      CFG.roundBudgetCapSOL = parseFloat($('p-cap').value) || CFG.roundBudgetCapSOL;
      CFG.gateTotalDeployed = parseFloat($('p-gateD').value) || 0;
      CFG.snipeAtSec = parseInt($('p-snipe').value, 10) || 5;

      CFG.adaptKByEmptiness = $('p-adapt').checked;
      CFG.preferLowCrowd = $('p-crowd').checked;
      CFG.motherlodeBoostOn = $('p-ml').checked;

      CFG.walletSafeMode = $('p-safe').checked;
      CFG.highlightOnly = $('p-high').checked;
      CFG.simMode = $('p-sim').checked;
      CFG.logVerbose = $('p-verbose').checked;

      CFG.autoClaim = $('p-autoclaim').checked;
      CFG.avoidClaimInsideSnipe = $('p-avoid').checked;
      CFG.claimEveryXRounds = parseInt($('p-claimX').value, 10) || 0;
      CFG.minClaimSol = parseFloat($('p-claimMin').value) || 0;

      start();
    };

    $('p-stop').onclick = stop;

    $('p-export').onclick = () => {
      const data = {
        bandit: bandit,
        stats: stats,
        exported: new Date().toISOString()
      };
      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ore-stats-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      log('Stats exported');
    };

    $('p-reset').onclick = () => {
      if (confirm('Reset all learning data? This cannot be undone.')) {
        localStorage.removeItem(STORE_KEY);
        localStorage.removeItem(STATS_KEY);
        bandit = loadBandit();
        stats = loadStats();
        log('Learning data reset');
        updateStatsDisplay();
      }
    };
  }

  function setStatus(t) {
    const el = document.getElementById('p-status');
    if (el) el.textContent = t;
  }

  function setPicked(a) {
    const el = document.getElementById('p-picked');
    if (el) el.textContent = (a && a.length) ? a.join(', ') : '–';
  }

  function updateStatsDisplay() {
    if (!stats.currentSession) return;

    const s = stats.currentSession;
    const $ = id => document.getElementById(id);

    if ($('p-stat-rounds')) $('p-stat-rounds').textContent = s.rounds;
    if ($('p-stat-deployed')) $('p-stat-deployed').textContent = s.deployed.toFixed(4);
    if ($('p-stat-claimed')) $('p-stat-claimed').textContent = s.claimed.toFixed(4);

    if ($('p-stat-roi') && s.deployed > 0) {
      const roi = ((s.claimed - s.deployed) / s.deployed * 100).toFixed(1);
      const roiEl = $('p-stat-roi');
      roiEl.textContent = roi + '%';
      roiEl.style.color = parseFloat(roi) >= 0 ? '#7ee7ff' : '#ff9090';
    }
  }

  /* ================= MAIN LOOP (ENHANCED) ================= */
  let running = false;
  let rounds = 0;
  let actedThisRound = false;
  let lastSecs = null;
  let skipStrikes = 0;
  let cooldownUntil = 0;

  async function loop() {
    while (running) {
      await sleep(200);

      const tiles = getTiles();
      if (tiles.length < 20) {
        setStatus('⚠ tiles not found (need ≥20); check page');
        await sleep(2000);
        continue;
      }

      const D = readTotalDeployed();
      trackD(D);
      const secs = readTimerSec();
      const ml = readMotherlode();

      // Reset flag when new round starts
      if (secs !== null && lastSecs !== null && secs > lastSecs) {
        actedThisRound = false;
      }
      if (secs !== null) lastSecs = secs;

      // Cooldown check
      if (CFG.coolDownAfterSkips && now() < cooldownUntil) {
        const remain = Math.ceil((cooldownUntil - now()) / 1000);
        setStatus(`⏸ cooldown: ${remain}s remaining`);
        continue;
      }

      // Auto-claim attempt
      await maybeAutoClaim(secs);

      // Deployment gate
      if (CFG.gateTotalDeployed > 0 && Number.isFinite(D) && D > CFG.gateTotalDeployed) {
        setStatus(`⏳ waiting: D=${D.toFixed(2)} > gate ${CFG.gateTotalDeployed.toFixed(1)}`);
        continue;
      }

      if (actedThisRound) {
        updateStatsDisplay();
        continue;
      }

      // Pick tiles
      const pick = pickTilesSmart(tiles, D || 25);
      let { chosen, kUse, avg } = pick;

      // Motherlode tile boost
      if (CFG.motherlodeBoostOn && Number.isFinite(ml) && ml >= CFG.motherlodeThresholdORE) {
        const prevK = kUse;
        kUse = Math.min(3, kUse + CFG.mlAddTiles);
        if (kUse !== prevK) {
          logV(`ML active: boosting k from ${prevK} to ${kUse}`);
        }
      }

      // Ensure we have enough chosen tiles
      if (chosen.length > kUse) {
        chosen = chosen.slice(0, kUse);
      }

      const chosenIdx = chosen.map(r => r.idx);
      setPicked(chosenIdx);

      // Compute amount
      let perTileAmt = computePerTileSize(chosen, avg);
      const totalThisRound = perTileAmt * Math.max(1, chosen.length);

      // Apply round cap
      if (totalThisRound > CFG.roundBudgetCapSOL) {
        perTileAmt = CFG.roundBudgetCapSOL / Math.max(1, chosen.length);
        logV(`Round cap applied: ${totalThisRound.toFixed(6)} > ${CFG.roundBudgetCapSOL}, reduced to ${perTileAmt.toFixed(6)} per tile`);
      }
      perTileAmt = clamp(perTileAmt, 0, CFG.perTileMaxSOL);

      // Wait for snipe window
      if (secs !== null && secs > CFG.snipeAtSec) {
        const mlStr = Number.isFinite(ml) ? ml.toFixed(1) : '–';
        const avgStr = Number.isFinite(avg) ? avg.toFixed(3) : '–';
        setStatus(`🎯 armed @${secs}s | snipe ≤${CFG.snipeAtSec}s | avg≈${avgStr} | ML=${mlStr}`);
        continue;
      }

      // Surge shield
      if (surgeActive()) {
        log('Surge detected, skipping round');
        setStatus('🛡 late surge detected — skipping');
        skipStrikes += 1;

        recordRound(perTileAmt, chosen.length, chosenIdx, 'skipped');
        actedThisRound = true;

        if (CFG.coolDownAfterSkips && skipStrikes >= CFG.skipStrikeLimit) {
          cooldownUntil = now() + CFG.coolDownMs;
          skipStrikes = 0;
        }
        continue;
      }

      // === ACTION ===
      try {
        // Highlight-only mode
        if (CFG.highlightOnly) {
          chosen.forEach(r => {
            r.el.style.outline = '3px solid #7ee7ff';
            r.el.style.outlineOffset = '2px';
            setTimeout(() => {
              r.el.style.outline = '';
              r.el.style.outlineOffset = '';
            }, 1200);
          });

          actedThisRound = true;
          rounds += 1;
          bandit.rounds += 1;
          saveBandit();

          recordRound(perTileAmt, chosen.length, chosenIdx, 'highlighted');
          setStatus(`✨ highlighted #${rounds} | k=${chosen.length}`);
          continue;
        }

        // Clear previous selections
        const tileEls = tiles.map(x => x);
        if (CFG.clearSelectedBeforePick) {
          await clearSelections(tileEls);
        }

        // Set amount
        const amtSet = setAmount(perTileAmt);
        if (!amtSet) {
          log('Failed to set amount');
          setStatus('⚠ amount input not found');
          skipStrikes += 1;
          continue;
        }

        // Micro-jitter to avoid collisions
        await sleep(Math.floor(Math.random() * 250) + 80);

        // Select tiles
        for (const r of chosen) {
          if (!CFG.simMode) {
            await click(r.el);
          } else {
            // Simulate: just highlight
            r.el.style.outline = '2px solid #7ee7ff';
            setTimeout(() => { r.el.style.outline = ''; }, 800);
          }
        }

        const deploy = findDeployButton();

        // Wallet-safe or sim mode: stop before Deploy
        if (CFG.walletSafeMode || CFG.simMode) {
          setStatus(`✅ selected tiles ${chosenIdx.join(', ')} | ${perTileAmt.toFixed(6)} SOL | waiting for Auto`);
          actedThisRound = true;
          rounds += 1;
          bandit.rounds += 1;
          saveBandit();

          recordRound(perTileAmt, chosen.length, chosenIdx, 'wallet-safe');
          skipStrikes = 0;
          deploysSinceClaim += 1;

          if (rounds >= CFG.maxRounds) {
            setStatus(`✅ completed ${CFG.maxRounds} rounds`);
            stop();
            break;
          }
          continue;
        }

        // Actually deploy (not wallet-safe)
        if (!deploy) {
          log('Deploy button not found');
          setStatus('⚠ deploy button not found');
          actedThisRound = true;
          rounds += 1;
          bandit.rounds += 1;
          saveBandit();
          skipStrikes += 1;
          continue;
        }

        await click(deploy);

        actedThisRound = true;
        rounds += 1;
        bandit.rounds += 1;
        saveBandit();
        deploysSinceClaim += 1;

        recordRound(perTileAmt, chosen.length, chosenIdx, 'deployed');

        const totalDeployed = perTileAmt * chosen.length;
        log(`Deployed round #${rounds}: k=${chosen.length}, amt=${perTileAmt.toFixed(6)}, total=${totalDeployed.toFixed(6)}, tiles=${chosenIdx.join(',')}`);
        setStatus(`✅ deployed #${rounds} | k=${chosen.length} | ${perTileAmt.toFixed(6)} SOL/tile`);

        skipStrikes = 0;

        if (rounds >= CFG.maxRounds) {
          setStatus(`✅ completed ${CFG.maxRounds} rounds`);
          stop();
          break;
        }
      } catch (e) {
        log('Action error:', e);
        setStatus('❌ error (see console)');

        recordRound(0, 0, [], 'error');
        skipStrikes += 1;

        if (CFG.coolDownAfterSkips && skipStrikes >= CFG.skipStrikeLimit) {
          cooldownUntil = now() + CFG.coolDownMs;
          skipStrikes = 0;
        }
      }

      updateStatsDisplay();
    }
  }

  function start() {
    if (running) return;
    running = true;
    rounds = 0;
    actedThisRound = false;
    skipStrikes = 0;
    cooldownUntil = 0;
    lastSecs = null;
    deploysSinceClaim = 0;

    startSession();
    setStatus('🚀 running...');
    updateStatsDisplay();
    log('Started');

    loop();
  }

  function stop() {
    running = false;
    endSession();
    setStatus('⏹ stopped');
    log('Stopped');
  }

  // Initialize HUD when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', makeHUD);
  } else {
    makeHUD();
  }
})();
