// ==UserScript==
// @name         ORE.supply Smart Auto++ v2.2 (Wallet-Safe Assist)
// @namespace    ore-auto-smart-plus
// @version      2.2
// @description  Emptiest-tile edge + low-crowd + surge shield + Motherlode mode + size scaling + (optional) auto-claim SOL; wallet-safe & highlight-only modes
// @match        https://ore.supply/*
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  /* ================= USER CONFIG (editable in HUD) ================= */

  const CFG = {
    // Core bankroll knobs
    basePerTileSOL: 0.0008,   // starting amount per tile (auto-scales per round)
    kStart: 2,                 // default tiles per round (1–3; autoscaled by emptiness)
    maxRounds: 200,
    roundBudgetCapSOL: 0.010,  // cap total per round (k * perTile)

    // Access & timing
    gateTotalDeployed: 20.0,   // only act if Total Deployed D ≤ this (0 = off)
    snipeAtSec: 5,             // act when timer ≤ this (late-snipe)
    minMsBetweenClicks: 120,
    clearSelectedBeforePick: true,

    // Emptiness learning (bandit)
    eps: 0.10,                 // exploration fraction
    ewmaAlpha: 0.25,           // learning speed
    emptinessGateXAvg: 0.90,   // prefer W < X * (D/25)

    // Low-crowd preference
    preferLowCrowd: true,
    minersWeight: 0.45,        // weight for crowd score vs emptiness (0..1)
    minersGateMax: 9999,       // optional hard cap on miners per tile

    // Late-surge shield (avoid last-second dilution)
    surgeLookbackSec: 6,
    surgeMinDeltaSOL: 2.0,

    // Motherlode mode
    motherlodeBoostOn: true,
    motherlodeThresholdORE: 50,
    mlSizeMultiplier: 1.20,    // bump perTile when ML big
    mlAddTiles: 1,             // add +tiles (capped at 3)
    perTileMaxSOL: 0.0020,     // hard per-tile cap

    // Per-round size scaling (uniform per tile)
    sizeScaleGamma: 1.30,
    sizeScaleMin: 0.75,
    sizeScaleMax: 1.60,

    // Autos
    adaptKByEmptiness: true,

    // Wallet-safe / UI-only modes
    walletSafeMode: true,      // DO NOT click Deploy/Claim; just assist the UI
    highlightOnly: false,      // if true: do not click tiles either — highlight picks only
    simMode: false,            // global dry-run (no clicks anywhere)

    // Optional: Auto-claim SOL only (disabled by default; wallet popup needed)
    autoClaim: false,
    claimEveryXRounds: 40,
    minClaimSol: 0.05,
    claimCooldownMs: 60_000,
    avoidClaimInsideSnipe: true,

    // Safety & logging
    coolDownAfterSkips: true,
    skipStrikeLimit: 2,
    coolDownMs: 6000,
    log: true
  };

  /* ================= PERSISTENT BANDIT ================= */
  const STORE_KEY = 'ORE_SMART_PLUS_BANDIT_V22';
  let bandit = loadBandit();

  function loadBandit() {
    try { const j = localStorage.getItem(STORE_KEY); if (j) return JSON.parse(j); } catch(e){}
    const arms = {}; for (let i=1;i<=25;i++) arms[i] = { ewmaW: 0.6, seen: 0, lastSeenRound: 0 };
    return { arms, rounds: 0 };
  }
  function saveBandit(){ localStorage.setItem(STORE_KEY, JSON.stringify(bandit)); }

  /* ================= HELPERS ================= */
  const sleep = (ms)=>new Promise(r=>setTimeout(r,ms));
  const log = (...a)=>{ if (CFG.log) console.log('[ORE++ v2.2]', ...a); };
  const clamp = (x,a,b)=>Math.min(b,Math.max(a,x));
  const now = ()=>Date.now();

  /* ================= DOM SELECTORS ================= */
  const SEL = {
    tileCandidates: [
      'button[data-tile]','div[data-tile]','button[data-index]','div[data-index]',
      'button.tile','div.tile','button.block','div.block',
      'main button','main div[role="button"]'
    ],
    amountInputs: ['input[type="number"]','input[placeholder*="SOL"]'],
    deployButtons: ['button','div[role="button"]'],
    totalDeployedScope: 'body',
    timerScope: 'body',
    motherlodeScope: 'body',
    rewardsScope: 'body'
  };
  function qsa(sel,root=document){ return Array.from(root.querySelectorAll(sel)); }

  /* ================= PARSERS ================= */
  function getTiles(){
    const all=[]; for (const s of SEL.tileCandidates) for (const el of qsa(s)) if (el instanceof HTMLElement) all.push(el);
    const uniq=[], seen=new Set();
    for (const el of all){
      const idx=parseTileIndex(el); if (idx && idx>=1 && idx<=25 && !seen.has(el)){ uniq.push(el); seen.add(el); }
    }
    return uniq;
  }
  function parseTileIndex(el){
    const t=(el.innerText||'').trim();
    const m1=t.match(/#\s*(\d{1,2})\b/); if (m1) return parseInt(m1[1],10);
    const m2=t.match(/^\s*(\d{1,2})\s*$/); if (m2) return parseInt(m2[1],10);
    const di=el.getAttribute('data-index')||el.getAttribute('data-tile');
    if (di && /^\d{1,2}$/.test(di)) return parseInt(di,10);
    return null;
  }
  // Heuristic: last decimal in tile text = stake W; an integer before it may be "miners" count
  function parseTileStakeAndMiners(el){
    const t=(el.innerText||'').replace(/,/g,' ');
    const nums=(t.match(/(\d+\.\d+|\d+)/g)||[]).map(x=>x.includes('.')?parseFloat(x):parseInt(x,10));
    let W=Number.POSITIVE_INFINITY, N=null;
    if (nums.length){
      const last=nums[nums.length-1];
      if (Number.isFinite(last)) W = parseFloat(last);
      if (nums.length>=2){
        const prev=nums[nums.length-2];
        if (Number.isInteger(prev) && prev>=0 && prev<100000) N = prev;
      }
    }
    return {W, miners:N};
  }
  function findAmountInput(){
    for (const s of SEL.amountInputs){
      const els = qsa(s).filter(e=>e.offsetParent!==null);
      if (els[0]) return els[0];
    } return null;
  }
  function setAmount(val){
    const inp=findAmountInput(); if (!inp){ log('Amount input not found'); return false; }
    inp.focus(); inp.value=String(val);
    inp.dispatchEvent(new Event('input',{bubbles:true})); inp.dispatchEvent(new Event('change',{bubbles:true}));
    return true;
  }
  function findDeployButton(){
    const cands=[]; for (const s of SEL.deployButtons) cands.push(...qsa(s));
    const ok=cands.filter(el=>el.offsetParent!==null && /deploy/i.test(el.innerText||'')); return ok[0]||null;
  }
  async function click(el){ if(!el) return false; el.scrollIntoView({block:'center'}); if(!CFG.simMode) el.click(); await sleep(CFG.minMsBetweenClicks); return true; }
  async function clearSelections(tiles){
    const selected=tiles.filter(el=>{
      const ap=el.getAttribute('aria-pressed'); if(ap && ap.toString()==='true') return true;
      const cls=(el.className||'').toString().toLowerCase(); return /\bselected\b/.test(cls);
    });
    for(const el of selected) await click(el);
  }
  function readTotalDeployed(){
    const txt=(document.querySelector(SEL.totalDeployedScope)?.innerText||'');
    const m=txt.match(/Total\s*deployed[^\d]*([\d]+\.\d+|\d+)/i);
    return m?parseFloat(m[1]):null;
  }
  function readTimerSec(){
    const txt=(document.querySelector(SEL.timerScope)?.innerText||'');
    const m=txt.match(/Time\s*remaining[\s\S]*?(\d{1,2})\s*[:.]\s*(\d{2})/i);
    if (m){ return parseInt(m[1],10)*60 + parseInt(m[2],10); } return null;
  }
  function readMotherlode(){
    const txt=(document.querySelector(SEL.motherlodeScope)?.innerText||'');
    const m=txt.match(/Motherlode[\s\S]*?(\d+(?:\.\d+)?)/i);
    return m?parseFloat(m[1]):null;
  }
  function readClaimableSol(){
    const txt=(document.querySelector(SEL.rewardsScope)?.innerText||'');
    const m = txt.match(/Rewards[\s\S]{0,400}?SOL[^\d]*([\d]+\.\d+|\d+)/i);
    return m?parseFloat(m[1]):0;
  }

  /* ================= LEARNING (emptiness) ================= */
  function updateEWMA(idx, observedW){
    const arm = bandit.arms[idx] || (bandit.arms[idx]={ ewmaW: observedW, seen:0, lastSeenRound: bandit.rounds });
    arm.ewmaW = arm.seen ? (CFG.ewmaAlpha*observedW + (1-CFG.ewmaAlpha)*arm.ewmaW) : observedW;
    arm.seen += 1; arm.lastSeenRound = bandit.rounds;
  }

  /* ================= PICK LOGIC (emptiness + low-crowd) ================= */
  function pickTilesSmart(tiles, D){
    const avg = (D && D>0)? (D/25) : 0.6;
    const rows = tiles.map(el=>{
      const idx = parseTileIndex(el);
      const {W, miners} = parseTileStakeAndMiners(el);
      if (Number.isFinite(W)) updateEWMA(idx, W);
      const prior = bandit.arms[idx]?.ewmaW ?? 0.6;
      const emptinessScore = (Math.random()<CFG.eps) ? (Math.random()*10) : prior;
      let crowdScore = 0.5;
      if (miners !== null){
        const c = clamp(miners,0,500)/500; // lower miners better
        crowdScore = c;
      }
      const combined = (1-CFG.minersWeight)*emptinessScore + CFG.minersWeight*crowdScore;
      return { el, idx, Wobs: W, miners, prior, emptinessScore, crowdScore, combined };
    }).filter(r=>r.idx);

    rows.sort((a,b)=> (a.combined - b.combined) || (a.Wobs - b.Wobs) || (a.idx - b.idx));

    // adapt k by emptiness
    let kUse = CFG.kStart;
    if (CFG.adaptKByEmptiness && Number.isFinite(avg)){
      const obs = rows.map(r=>r.Wobs).filter(Number.isFinite).sort((a,b)=>a-b);
      const med = obs.length ? obs[Math.floor(obs.length/2)] : avg;
      if (med < 0.50*avg) kUse = 1;
      else if (med < 0.90*avg) kUse = 2;
      else kUse = 3;
    }

    // EV-style softness
    const gateW = CFG.emptinessGateXAvg * avg;
    let filtered = rows;
    if (Number.isFinite(avg) && Number.isFinite(gateW)){
      const soft = rows.filter(r => (Number.isFinite(r.Wobs) && r.Wobs < gateW) || (r.prior < gateW));
      if (soft.length >= kUse) filtered = soft;
    }
    // optional hard crowd gate
    if (CFG.preferLowCrowd && CFG.minersGateMax < 9999){
      const g = filtered.filter(r => (r.miners===null) || (r.miners <= CFG.minersGateMax));
      if (g.length >= kUse) filtered = g;
    }

    const chosen = filtered.slice(0, kUse);
    return { chosen, kUse, avg };
  }

  /* ================= SIZE ================= */
  function computePerTileSize(chosen, avg){
    let amt = CFG.basePerTileSOL;
    if (chosen.length && Number.isFinite(avg) && avg>0){
      const Ws = chosen.map(r=> Number.isFinite(r.Wobs)? r.Wobs : r.prior).sort((a,b)=>a-b);
      const med = Ws[Math.floor(Ws.length/2)] || avg;
      const scale = clamp(Math.pow(clamp(avg/med, 0.4, 2.5), CFG.sizeScaleGamma), CFG.sizeScaleMin, CFG.sizeScaleMax);
      amt = clamp(amt * scale, 0, CFG.perTileMaxSOL);
    }
    const ml = readMotherlode();
    if (CFG.motherlodeBoostOn && Number.isFinite(ml) && ml >= CFG.motherlodeThresholdORE){
      amt = clamp(amt * CFG.mlSizeMultiplier, 0, CFG.perTileMaxSOL);
    }
    return amt;
  }

  /* ================= SURGE SHIELD ================= */
  const surgeBuf = [];
  function trackD(D){
    if (!Number.isFinite(D)) return;
    const t = now();
    surgeBuf.push({t, D});
    const cutoff = t - CFG.surgeLookbackSec*1000;
    while (surgeBuf.length && surgeBuf[0].t < cutoff) surgeBuf.shift();
  }
  function surgeActive(){
    if (surgeBuf.length < 2) return false;
    const d = surgeBuf[surgeBuf.length-1].D - surgeBuf[0].D;
    return d >= CFG.surgeMinDeltaSOL;
  }

  /* ================= AUTO-CLAIM (SOL only, optional) ================= */
  let lastClaimTs = 0;
  let deploysSinceClaim = 0;

  function findClaimSolOnlyButton(){
    const cands = qsa('button,div[role="button"],a').filter(el => el.offsetParent !== null);
    return cands.find(el=>{
      const t = (el.innerText||'').trim();
      const hasClaim = /claim/i.test(t);
      const hasSOL = /\bsol\b/i.test(t);
      const hasORE = /\bore\b/i.test(t);
      const refine = /refine/i.test(t);
      return hasClaim && hasSOL && !hasORE && !refine;
    }) || null;
  }
  function findConfirmButton(){
    const cands = qsa('button,div[role="button"]');
    return cands.find(el=> el.offsetParent!==null && /(confirm|approve|ok)/i.test(el.innerText||'')) || null;
  }
  async function maybeAutoClaim(secs){
    if (!CFG.autoClaim || CFG.walletSafeMode) return false; // wallet-safe blocks claims
    const tooSoon = (now() - lastClaimTs) < CFG.claimCooldownMs;
    if (tooSoon) return false;
    if (CFG.avoidClaimInsideSnipe && secs !== null && secs <= (CFG.snipeAtSec + 1)) return false;

    const claimable = readClaimableSol();
    const roundsTrigger = (CFG.claimEveryXRounds > 0) && (deploysSinceClaim >= CFG.claimEveryXRounds);
    const amountTrigger  = (Number.isFinite(claimable) && claimable >= CFG.minClaimSol);
    if (!roundsTrigger && !amountTrigger) return false;

    const btn = findClaimSolOnlyButton();
    if (!btn) { log('Auto-claim: SOL button not found'); return false; }

    try{
      await click(btn);
      await sleep(150);
      const confirm = findConfirmButton();
      if (confirm) await click(confirm);

      lastClaimTs = now();
      deploysSinceClaim = 0;
      log(`Auto-claimed SOL (≈ ${claimable?.toFixed?.(4) ?? 'n/a'})`);
      setStatus('auto-claimed SOL');
      return true;
    } catch(e){
      log('Auto-claim error', e);
      return false;
    }
  }

  /* ================= HUD ================= */
  function makeHUD(){
    const box=document.createElement('div');
    box.id='ore-smart-auto-plus';
    box.style.cssText=`
      position:fixed;left:16px;bottom:16px;z-index:999999;width:360px;
      background:rgba(9,13,20,.94);color:#e7ecf3;border:1px solid #223049;border-radius:14px;
      padding:12px;font:12px/1.4 system-ui,-apple-system,Segoe UI,Roboto;box-shadow:0 10px 30px rgba(0,0,0,.35)`;
    box.innerHTML=`
      <div style="font-weight:700;margin-bottom:6px;">ORE Smart Auto++ v2.2</div>

      <label>Base per-tile (SOL)
        <input id="p-amt" type="number" step="0.000001" value="${CFG.basePerTileSOL}" style="width:100%;margin:4px 0;">
      </label>
      <label>k start
        <select id="p-k" style="width:100%;margin:4px 0;"><option>1</option><option ${CFG.kStart===2?'selected':''}>2</option><option ${CFG.kStart===3?'selected':''}>3</option></select>
      </label>
      <label>Max rounds
        <input id="p-max" type="number" value="${CFG.maxRounds}" style="width:100%;margin:4px 0;">
      </label>
      <label>Round budget cap (SOL)
        <input id="p-cap" type="number" step="0.001" value="${CFG.roundBudgetCapSOL}" style="width:100%;margin:4px 0;">
      </label>
      <label>Gate D ≤ (0=off)
        <input id="p-gateD" type="number" step="0.1" value="${CFG.gateTotalDeployed}" style="width:100%;margin:4px 0;">
      </label>
      <label>Snipe at ≤ sec
        <input id="p-snipe" type="number" value="${CFG.snipeAtSec}" style="width:100%;margin:4px 0;">
      </label>

      <div style="display:flex;gap:8px;margin:6px 0;flex-wrap:wrap">
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-adapt" type="checkbox" ${CFG.adaptKByEmptiness?'checked':''}> adapt k</label>
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-crowd" type="checkbox" ${CFG.preferLowCrowd?'checked':''}> low-crowd</label>
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-ml" type="checkbox" ${CFG.motherlodeBoostOn?'checked':''}> ML mode</label>
      </div>

      <hr style="border-color:#223049;opacity:.5;margin:8px 0">

      <div style="display:flex;gap:8px;margin:6px 0;flex-wrap:wrap">
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-safe" type="checkbox" ${CFG.walletSafeMode?'checked':''}> wallet-safe</label>
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-high" type="checkbox" ${CFG.highlightOnly?'checked':''}> highlight-only</label>
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-sim" type="checkbox" ${CFG.simMode?'checked':''}> simulate</label>
      </div>

      <div style="font-weight:700;margin:6px 0 2px;">Auto-Claim (SOL only)</div>
      <div style="display:flex;gap:8px;margin:6px 0;flex-wrap:wrap">
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-autoclaim" type="checkbox" ${CFG.autoClaim?'checked':''}> enable</label>
        <label style="display:flex;align-items:center;gap:6px;"><input id="p-avoid" type="checkbox" ${CFG.avoidClaimInsideSnipe?'checked':''}> avoid snipe</label>
      </div>
      <label>Claim every X rounds
        <input id="p-claimX" type="number" value="${CFG.claimEveryXRounds}" style="width:100%;margin:4px 0;">
      </label>
      <label>Min claim SOL
        <input id="p-claimMin" type="number" step="0.001" value="${CFG.minClaimSol}" style="width:100%;margin:4px 0;">
      </label>

      <div id="p-status" style="color:#93a0b4;margin:6px 0 8px;">idle</div>
      <div style="display:flex;gap:8px;">
        <button id="p-start" style="flex:1;padding:6px;border:1px solid #2b3b5a;background:#0e1523;color:#cfe7ff;border-radius:8px;cursor:pointer;">Start</button>
        <button id="p-stop"  style="flex:1;padding:6px;border:1px solid #503a3a;background:#1a0e0e;color:#ffd0d0;border-radius:8px;cursor:pointer;">Stop</button>
      </div>
      <div style="margin-top:8px;color:#93a0b4;">Picked: <span id="p-picked">–</span></div>
    `;
    document.body.appendChild(box);

    const $=id=>document.getElementById(id);
    $('p-start').onclick=()=>{
      CFG.basePerTileSOL   = parseFloat($('p-amt').value)||CFG.basePerTileSOL;
      CFG.kStart           = parseInt($('p-k').value,10)||2;
      CFG.maxRounds        = parseInt($('p-max').value,10)||200;
      CFG.roundBudgetCapSOL= parseFloat($('p-cap').value)||CFG.roundBudgetCapSOL;
      CFG.gateTotalDeployed= parseFloat($('p-gateD').value)||0;
      CFG.snipeAtSec       = parseInt($('p-snipe').value,10)||5;

      CFG.adaptKByEmptiness= $('p-adapt').checked;
      CFG.preferLowCrowd   = $('p-crowd').checked;
      CFG.motherlodeBoostOn= $('p-ml').checked;

      CFG.walletSafeMode   = $('p-safe').checked;
      CFG.highlightOnly    = $('p-high').checked;
      CFG.simMode          = $('p-sim').checked;

      CFG.autoClaim        = $('p-autoclaim').checked;
      CFG.avoidClaimInsideSnipe = $('p-avoid').checked;
      CFG.claimEveryXRounds= parseInt($('p-claimX').value,10)||0;
      CFG.minClaimSol      = parseFloat($('p-claimMin').value)||0;

      start();
    };
    $('p-stop').onclick=stop;
  }
  function setStatus(t){ const el=document.getElementById('p-status'); if(el) el.textContent=t; }
  function setPicked(a){ const el=document.getElementById('p-picked'); if(el) el.textContent=(a&&a.length)?a.join(', '):'–'; }

  /* ================= MAIN LOOP ================= */
  let running=false, rounds=0, actedThisRound=false, lastSecs=null, skipStrikes=0, cooldownUntil=0;

  async function loop(){
    while (running){
      await sleep(200);
      const tiles = getTiles();
      if (tiles.length < 20){ setStatus('tiles not found; adjust selectors'); continue; }

      const D = readTotalDeployed(); trackD(D);
      const secs = readTimerSec();
      const ml = readMotherlode();

      if (secs!==null && lastSecs!==null && secs > lastSecs){ actedThisRound=false; }
      if (secs!==null) lastSecs=secs;

      if (CFG.coolDownAfterSkips && now() < cooldownUntil){
        setStatus(`cooldown… ${Math.ceil((cooldownUntil-now())/1000)}s`);
        continue;
      }

      // Try auto-claim (if enabled and not wallet-safe)
      await maybeAutoClaim(secs);

      // Deployed gate
      if (CFG.gateTotalDeployed && Number.isFinite(D) && D > CFG.gateTotalDeployed){
        setStatus(`waiting: D=${D.toFixed(2)} > gate ${CFG.gateTotalDeployed}`);
        continue;
      }

      if (actedThisRound) continue;

      const pick = pickTilesSmart(tiles, D||25);
      let { chosen, kUse, avg } = pick;

      // ML boost may add tiles
      if (CFG.motherlodeBoostOn && Number.isFinite(ml) && ml >= CFG.motherlodeThresholdORE){
        kUse = Math.min(3, kUse + CFG.mlAddTiles);
        if (chosen.length > kUse) chosen = chosen.slice(0, kUse);
      }

      const chosenIdx = chosen.map(r=>r.idx);
      setPicked(chosenIdx);

      let perTileAmt = computePerTileSize(chosen, avg);
      const totalThisRound = perTileAmt * Math.max(1, chosen.length);
      if (totalThisRound > CFG.roundBudgetCapSOL){
        perTileAmt = CFG.roundBudgetCapSOL / Math.max(1, chosen.length);
      }
      perTileAmt = clamp(perTileAmt, 0, CFG.perTileMaxSOL);

      // Wait for snipe window
      if (secs!==null && secs > CFG.snipeAtSec){
        setStatus(`armed @${secs}s; snipe ≤ ${CFG.snipeAtSec}s (avg≈${Number.isFinite(avg)?avg.toFixed(3):'–'} | ML=${Number.isFinite(ml)?ml.toFixed(2):'–'})`);
        continue;
      }
      // Surge shield
      if (surgeActive()){
        setStatus('late surge detected — skipping round');
        skipStrikes += 1;
        if (CFG.coolDownAfterSkips && skipStrikes >= CFG.skipStrikeLimit){
          cooldownUntil = now() + CFG.coolDownMs; skipStrikes=0;
        }
        continue;
      }

      // ACTION
      try{
        // Highlight-only mode: just paint picks, never click
        if (CFG.highlightOnly){
          chosen.forEach(r => { r.el.style.outline='2px solid #7ee7ff'; r.el.style.outlineOffset='2px'; setTimeout(()=>{ r.el.style.outline=''; r.el.style.outlineOffset=''; },800); });
          actedThisRound = true; rounds += 1; bandit.rounds += 1; saveBandit();
          setStatus(`highlighted #${rounds} | k=${chosen.length}`);
          continue;
        }

        const tileEls = tiles.map(x=>x);
        if (CFG.clearSelectedBeforePick) await clearSelections(tileEls);

        // set amount regardless of mode
        setAmount(perTileAmt);
        await sleep(Math.floor(Math.random()*250)+80); // micro-jitter

        // Preselect tiles (unless simMode)
        for (const r of chosen){
          if (!CFG.simMode) await click(r.el);
          else { r.el.style.outline='2px solid #7ee7ff'; setTimeout(()=>{ r.el.style.outline=''; },800); }
        }

        const deploy = findDeployButton(); // may be null depending on UI state
        if (!deploy){ setStatus('Deploy not found'); actedThisRound = true; rounds += 1; bandit.rounds += 1; saveBandit(); continue; }

        // Wallet-safe: DO NOT click Deploy
        if (CFG.walletSafeMode || CFG.simMode){
          setStatus(`selected tiles: ${chosenIdx.join(', ')} | waiting for Auto / you`);
        } else {
          await click(deploy);
          setStatus(`deployed #${rounds+1} | k=${chosen.length} | amt=${perTileAmt.toFixed(6)} SOL`);
        }

        actedThisRound = true; rounds += 1; bandit.rounds += 1; saveBandit();
        deploysSinceClaim += 1;
        skipStrikes = 0;

        if (rounds >= CFG.maxRounds){ setStatus(`done (max ${CFG.maxRounds})`); stop(); break; }
      } catch(e){
        log('action error', e); setStatus('error; see console');
        skipStrikes += 1;
        if (CFG.coolDownAfterSkips && skipStrikes >= CFG.skipStrikeLimit){
          cooldownUntil = now() + CFG.coolDownMs; skipStrikes=0;
        }
      }
    }
  }

  function start(){ if (running) return; running=true; rounds=0; actedThisRound=false; setStatus('running…'); loop(); }
  function stop(){ running=false; setStatus('stopped'); }

  (document.readyState==='loading')?document.addEventListener('DOMContentLoaded',makeHUD):makeHUD();
})();
