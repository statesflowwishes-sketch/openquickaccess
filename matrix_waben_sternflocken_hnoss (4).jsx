import React, { useEffect, useRef } from 'react';

// React/JSX Single-File Component (kein TS, kein <!DOCTYPE html>)
// Features: Matrix (multi-layer), Waben & Kristalle, Nodes+Links, Keyboard-Welle,
//           "Hnoss" zentral mit goldenem Leuchtkegel, leichte Self-Tests.
// Fixes gegenüber deiner Fassung:
// - Entfernt: eingebettetes reines HTML-Dokument und doppelte Komponentendefinition
// - Entfernt: TypeScript-"as const" (reines JS)
// - Hinzugefügt: window.addEventListener('resize', onResize) + Clean-up im Return
// - Einmalige rafId-Definition beibehalten.

export default function MatrixWabenSternflockenHnoss(){
  // --- Refs ---
  const stageRef = useRef(null);
  const matrixRef = useRef(null);
  const fxRef = useRef(null);
  const shapesRef = useRef(null);
  const nodesRef = useRef(null);
  const keyboardRef = useRef(null);
  const hnossRef = useRef(null);
  const selftestRef = useRef(null);

  useEffect(()=>{
    const stage = stageRef.current;
    const canvas = matrixRef.current;
    const fx = fxRef.current;
    const shapes = shapesRef.current;
    const nodesSvg = nodesRef.current;
    const kbSvg = keyboardRef.current;
    const hnoss = hnossRef.current;
    const selftest = selftestRef.current;
    if(!stage || !canvas || !fx || !shapes || !nodesSvg || !kbSvg || !hnoss || !selftest) return;

    const mctx = canvas.getContext('2d');
    const fctx = fx.getContext('2d');

    // --- Config ---
    const BPM = 96;
    const SUBDIV = 4; // 16tel
    const BEAT_MS = 60000 / BPM;
    const DPR = Math.max(1, Math.min(2.5, window.devicePixelRatio || 1));
    const COLOR_PALETTE = ['#62ff62','#62c9ff','#ff62f5','#ffb762']; // grün, cyan, magenta, amber

    const HEX_COUNT = 20;
    const CRYSTAL_COUNT = 30;

    const NODE_TYPES = [
      { key:'API',      color:'#62ff62' },
      { key:'TOOL',     color:'#62c9ff' },
      { key:'PROGRAM',  color:'#ff62f5' },
      { key:'MCP',      color:'#ffb762' },
    ];

    const KEY_ROWS = 4, KEY_COLS = 12;
    const KEY_ENERGY_DECAY_MS = 900; // Nachglühen der Wellen

    // stärkere, klarere Matrix-Layer
    const layers = [
      { speed:1.10, alpha:0.23, color:'#62ff62', fontScale:1.00, drops:[], columns:0 },
      { speed:1.65, alpha:0.20, color:'#62c9ff', fontScale:0.90, drops:[], columns:0 },
      { speed:0.85, alpha:0.18, color:'#ff62f5', fontScale:1.25, drops:[], columns:0 },
      { speed:1.35, alpha:0.17, color:'#ffb762', fontScale:0.75, drops:[], columns:0 },
    ];

    // --- State ---
    const animators = [];
    let keys = [];
    let nodes = [];
    let baseFontSize = 14;
    let beatPhase = 0, subIndex = 0;
    let last = performance.now();
    let frameCount = 0;
    let rafId = 0; // ensure declared ONCE in this scope

    // --- Utils ---
    function clamp01(x){ return x < 0 ? 0 : (x > 1 ? 1 : x); }
    function hexToRgba(hex,a){
      const m=/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex||'');
      if(!m){ const r=98,g=255,b=98; return `rgba(${r},${g},${b},${clamp01(a)})`; }
      const r=parseInt(m[1],16), g=parseInt(m[2],16), b=parseInt(m[3],16);
      return `rgba(${r},${g},${b},${clamp01(a)})`;
    }
    function svgEl(tag, attrs){ const el = document.createElementNS('http://www.w3.org/2000/svg', tag); for(const k in attrs) el.setAttribute(k, String(attrs[k])); return el; }

    // --- Resize/Setup ---
    function onResize(){
      const W = stage.clientWidth | 0;
      const H = stage.clientHeight | 0;
      canvas.width = (W * DPR) | 0; canvas.height = (H * DPR) | 0; canvas.style.width = W+'px'; canvas.style.height = H+'px';
      mctx.setTransform(DPR,0,0,DPR,0,0);
      fx.width = (W * DPR) | 0; fx.height = (H * DPR) | 0; fx.style.width = W+'px'; fx.style.height = H+'px';
      fctx.setTransform(DPR,0,0,DPR,0,0);
      [nodesSvg, kbSvg].forEach(svg=>{ svg.setAttribute('viewBox',`0 0 ${W} ${H}`); svg.setAttribute('width', String(W)); svg.setAttribute('height', String(H)); });
      setupMatrix(); seedShapes(); seedNodes(); seedKeyboard();
    }

    function setupMatrix(){
      baseFontSize = Math.max(12, Math.round(stage.clientWidth / 120));
      for(const L of layers){
        const fsize = Math.round(baseFontSize * L.fontScale);
        L.columns = Math.max(1, Math.floor(stage.clientWidth / fsize));
        L.drops = Array(L.columns).fill(1);
        L.fontSize = fsize;
      }
    }

    // --- Matrix ---
    function drawMatrix(now){
      // Trail für mehr Präsenz
      mctx.fillStyle = 'rgba(0,0,0,0.08)';
      mctx.fillRect(0,0,canvas.width,canvas.height);
      // Bloom/Glow additiv
      mctx.save(); mctx.globalCompositeOperation = 'lighter';
      const timeBeat = now / BEAT_MS;
      for (let idx=0; idx<layers.length; idx++){
        const L = layers[idx];
        mctx.font = `${L.fontSize}px "JetBrains Mono", ui-monospace, monospace`;
        mctx.shadowColor = hexToRgba(L.color, 0.85);
        mctx.shadowBlur = 8;
        mctx.fillStyle = hexToRgba(L.color, clamp01(L.alpha + 0.08*Math.sin(timeBeat*2 + idx)));
        for (let i=0; i<L.drops.length; i++){
          const ch = String.fromCharCode(0x30A0 + (Math.random()*96|0));
          const x = i * L.fontSize; const y = L.drops[i] * L.fontSize;
          mctx.fillText(ch, x, y);
          // Head-Highlight
          if ((y / L.fontSize) % 7 < 1.2){ mctx.save(); mctx.shadowBlur = 16; mctx.fillStyle = hexToRgba(L.color, 0.9); mctx.fillText(ch, x, y); mctx.restore(); }
          if (y > canvas.height && Math.random() > 0.975) L.drops[i] = 0;
          L.drops[i] += L.speed;
        }
      }
      mctx.restore();
    }

    // --- Waben & Kristalle ---
    function createHexPoints(size){
      const pts=[]; const ang = Math.PI*2/6; for(let i=0;i<6;i++) pts.push([ size + size*Math.cos(ang*i), size + size*Math.sin(ang*i) ]);
      return pts.map(p=>p.join(',')).join(' ');
    }
    function addHexagon(x,y,size){
      const svg = svgEl('svg', { width:size*2, height:size*2, viewBox:`0 0 ${size*2} ${size*2}` });
      svg.style.position='absolute'; svg.style.left=(x-size)+'px'; svg.style.top=(y-size)+'px';
      const poly = svgEl('polygon', { points:createHexPoints(size), fill:'none', stroke:'#0ff', 'stroke-width':2 });
      svg.appendChild(poly); shapes.appendChild(svg);
      let rot = Math.random()*360; const speed=(0.25+Math.random()*0.5)*(Math.random()<0.5?-1:1);
      animators.push((dt)=>{ rot += speed*dt*0.06; svg.style.transform = `rotate(${rot}deg)`; });
    }
    function addCrystal(x,y,size){
      const svg = svgEl('svg', { width:size*2, height:size*2, viewBox:`0 0 ${size*2} ${size*2}` });
      svg.style.position='absolute'; svg.style.left=(x-size)+'px'; svg.style.top=(y-size)+'px';
      const rect = svgEl('rect', { x:0, y:0, width:size*2, height:size*2, stroke:'#9ff', fill:'none', 'stroke-width':1.5 });
      const l1 = svgEl('line', { x1:0, y1:0, x2:size*2, y2:size*2, stroke:'#9ff', 'stroke-width':1.5 });
      const l2 = svgEl('line', { x1:size*2, y1:0, x2:0, y2:size*2, stroke:'#9ff', 'stroke-width':1.5 });
      svg.append(rect,l1,l2); shapes.appendChild(svg);
      let pulse = Math.random()*Math.PI*2; const speed=0.8+Math.random()*0.8;
      animators.push((dt)=>{ pulse += speed*dt*0.003; const o=0.28+0.6*Math.abs(Math.sin(pulse)); svg.style.opacity = o.toFixed(3); });
    }
    function seedShapes(){
      shapes.innerHTML=''; animators.length=0;
      const W = stage.clientWidth, H = stage.clientHeight;
      for(let i=0;i<HEX_COUNT;i++) addHexagon(Math.random()*W, Math.random()*H, 22 + Math.random()*44);
      for(let i=0;i<CRYSTAL_COUNT;i++) addCrystal(Math.random()*W, Math.random()*H, 10 + Math.random()*16);
    }

    // --- Nodes Ring + Verbindungen ---
    function seedNodes(){
      nodesSvg.innerHTML=''; nodes=[];
      const W=stage.clientWidth, H=stage.clientHeight; const cx=W*0.5, cy=H*0.5, r0=Math.min(W,H)*0.33;
      const total=16;
      for(let i=0;i<total;i++){
        const t = i/total * Math.PI*2; const r = r0*(0.85 + 0.15*Math.sin(i));
        const x = cx + Math.cos(t)*r, y = cy + Math.sin(t)*r;
        const type = NODE_TYPES[i % NODE_TYPES.length];
        const g = svgEl('g', { 'data-type':type.key });
        const rect = svgEl('rect', { x:x-2, y:y-2, width:4, height:4, fill:type.color, opacity:0.8, rx:1, ry:1 });
        const label = svgEl('text', { x:x+6, y:y-4, fill:type.color, 'font-size':10, 'font-family':'monospace', opacity:0.9 }); label.textContent=type.key;
        const halo = svgEl('circle', { cx:x, cy:y, r:10, fill:'none', stroke:type.color, 'stroke-opacity':0.0, 'stroke-width':1 });
        g.append(halo,rect,label); nodesSvg.appendChild(g); nodes.push({ x,y,type,rect,label,halo });
      }
      // Links
      for(let i=0;i<nodes.length;i++){
        const a=nodes[i], b=nodes[(i+4)%nodes.length];
        const line = svgEl('line', { x1:a.x, y1:a.y, x2:b.x, y2:b.y, stroke:a.type.color, 'stroke-opacity':0.16 });
        nodesSvg.insertBefore(line, nodesSvg.firstChild); a.link=line;
      }
    }

    // --- Keyboard Grid (Energie-Welle) ---
    function seedKeyboard(){
      kbSvg.innerHTML=''; keys=[];
      const W=stage.clientWidth, H=stage.clientHeight; const left=W*0.1, right=W*0.9, top=H*0.72, bottom=H*0.92;
      const cellW=(right-left)/KEY_COLS, cellH=(bottom-top)/KEY_ROWS;
      for(let r=0;r<KEY_ROWS;r++) for(let c=0;c<KEY_COLS;c++){
        const x=left+c*cellW, y=top+r*cellH; const type=NODE_TYPES[(c+r)%NODE_TYPES.length];
        const rect = svgEl('rect', { x:x+2, y:y+2, width:Math.max(2,cellW-4), height:Math.max(2,cellH-4), fill:type.color, opacity:0.25, rx:2, ry:2 });
        kbSvg.appendChild(rect); keys.push({ r,c,rect,type, baseOpacity:0.25, energy:0 });
      }
    }

    // --- Rhythmik ---
    function pulseNodes(typeKey){
      nodes.forEach(n=>{ const hit = n.type.key===typeKey; n.rect.setAttribute('opacity', hit?1.0:0.7); n.label.setAttribute('opacity', hit?1:0.55); n.halo.setAttribute('stroke-opacity', hit?0.95:0.0); n.halo.setAttribute('r', hit?16:10); });
    }
    function pulseKeyboard(si){
      const waveCol = si % KEY_COLS; // ensure KEY_COLS (not KEY_COL)
      const decayCols = 3;
      keys.forEach(k=>{ const dRaw=Math.abs(k.c - waveCol); const d=Math.min(dRaw, KEY_COLS - dRaw); const w=Math.max(0, 1 - d/decayCols); k.energy = Math.min(1, k.energy + 0.9*w); });
    }
    function tickRhythm(dt){
      beatPhase += dt; const subDur = BEAT_MS / SUBDIV;
      while(beatPhase >= subDur){ beatPhase -= subDur; subIndex++; const type = NODE_TYPES[subIndex % NODE_TYPES.length]; pulseNodes(type.key); pulseKeyboard(subIndex); }
    }

    // --- Hnoss Flug + Goldkegel + Sparkles ---
    let t = 0, prevX = null, prevY = null; const sparkles = [];
    function addSparkle(x,y){ sparkles.push({ x, y, life:1.0, r:1+Math.random()*2 }); }
    function drawSparkles(dt){ for(let i=sparkles.length-1;i>=0;i--){ const s=sparkles[i]; s.life -= dt*0.0015; if(s.life<=0){ sparkles.splice(i,1); continue; } fctx.beginPath(); fctx.fillStyle = `rgba(255,240,180,${(0.7*s.life).toFixed(3)})`; fctx.arc(s.x,s.y,s.r,0,Math.PI*2); fctx.fill(); } }
    function moveHnoss(dt){
      t += dt*0.00025;
      const W=stage.clientWidth, H=stage.clientHeight;
      const ax=0.5 + 0.45*Math.sin(t*2.0), ay=0.3 + 0.6*Math.sin(t*1.3 + Math.PI/3);
      const x=ax*W, y=ay*H; hnoss.style.left=x+'px'; hnoss.style.top=y+'px';
      // Hinweis: clearRect in CSS-Pixeln (Transform ist gesetzt)
      fctx.clearRect(0,0,W,H); fctx.save(); fctx.globalCompositeOperation='lighter';
      let dx=1, dy=0; if(prevX!==null && prevY!==null){ dx=x-prevX; dy=y-prevY; const len=Math.hypot(dx,dy)||1; dx/=len; dy/=len; }
      prevX=x; prevY=y;
      const baseAngle=Math.atan2(dy,dx), halfCone=35*Math.PI/180, lenCone=Math.min(W,H)*0.42;
      const rGlow=120; const radial=fctx.createRadialGradient(x,y,0, x,y,rGlow); radial.addColorStop(0,'rgba(255,215,0,0.38)'); radial.addColorStop(0.55,'rgba(255,180,0,0.20)'); radial.addColorStop(1,'rgba(0,0,0,0)'); fctx.fillStyle=radial; fctx.beginPath(); fctx.arc(x,y,rGlow,0,Math.PI*2); fctx.fill();
      const tipX=x+Math.cos(baseAngle)*lenCone, tipY=y+Math.sin(baseAngle)*lenCone,
            leftX=x+Math.cos(baseAngle-halfCone)*lenCone*0.9, leftY=y+Math.sin(baseAngle-halfCone)*lenCone*0.9,
            rightX=x+Math.cos(baseAngle+halfCone)*lenCone*0.9, rightY=y+Math.sin(baseAngle+halfCone)*lenCone*0.9;
      const lg=fctx.createLinearGradient(x,y, tipX,tipY); lg.addColorStop(0,'rgba(255,215,0,0.32)'); lg.addColorStop(0.5,'rgba(255,170,0,0.16)'); lg.addColorStop(1,'rgba(255,140,0,0.00)');
      fctx.fillStyle=lg; fctx.shadowColor='rgba(255,200,0,0.55)'; fctx.shadowBlur=40; fctx.beginPath(); fctx.moveTo(x,y); fctx.lineTo(leftX,leftY); fctx.lineTo(tipX,tipY); fctx.lineTo(rightX,rightY); fctx.closePath(); fctx.fill();
      addSparkle(x - dx*10, y - dy*10); drawSparkles(dt); fctx.restore();
    }

    // --- Main Loop ---
    function loop(now){
      const dt = now - last; last = now; frameCount++;
      tickRhythm(dt); drawMatrix(now); animators.forEach(a=>a(dt)); moveHnoss(dt);
      // Keyboard-Decay/Visuals
      const decay = Math.exp(-dt / KEY_ENERGY_DECAY_MS);
      keys.forEach(k=>{ k.energy *= decay; const bright = k.baseOpacity + 0.65*k.energy; const scale = 1 + 0.30*k.energy; k.rect.setAttribute('opacity', bright.toFixed(3)); k.rect.setAttribute('transform', `translate(${-(scale-1)*2},${-(scale-1)*2}) scale(${scale})`); });
      // Node-Link shimmer
      nodes.forEach((n,i)=>{ if(n.link){ const a=0.08 + 0.10*Math.abs(Math.sin((subIndex+i)/8)); n.link.setAttribute('stroke-opacity', a.toFixed(3)); } });
      rafId = requestAnimationFrame(loop); // assign to existing rafId (keine Neu-Deklaration)
    }

    // --- Self-Tests (non-invasive) ---
    function assert(cond,msg){ if(!cond) throw new Error(msg); }
    function report(results){ const ok = results.every(r=>r.ok); const lines = results.map(r=>`${r.ok?'✅':'❌'} ${r.name}${r.ok?'':' — '+r.msg}`); selftest.innerHTML = (ok? 'Self-test: OK' : 'Self-test: Fehler') + '<ul><li>' + lines.join('</li><li>') + '</li></ul>'; selftest.style.display='block'; selftest.classList.toggle('error', !ok); }
    function runSelfTests(){
      const results=[]; const test=(name,fn)=>{ try{ fn(); results.push({ok:true,name}); }catch(e){ results.push({ok:false,name,msg:e.message}); } };
      test('Canvas & FX Context', ()=>{ assert(!!mctx && !!fctx, '2D contexts missing'); });
      test('Matrix Layers init', ()=>{ assert(layers.length>=3 && layers.every(L=>L.drops.length>0), 'drops not seeded'); });
      test('Resize sync', ()=>{ onResize(); assert(canvas.width>0 && fx.width>0, 'canvas size 0'); });
      test('Legend colors', ()=>{ assert(COLOR_PALETTE.length===4, 'palette size'); });
      test('KEY_COLS used', ()=>{ const fn= pulseKeyboard.toString(); assert(/KEY_COLS/.test(fn) && !/KEY_COL\b/.test(fn), 'wrong KEY_COL usage'); });
      test('RAF scheduled', ()=>{ assert(Number.isFinite(rafId) && rafId>=0, 'rafId invalid'); });
      const subStart=subIndex, framesStart=frameCount;
      const hnRect1 = hnoss.getBoundingClientRect();
      setTimeout(()=>{
        try{
          assert(frameCount>framesStart+5,'frames not advancing');
          assert(subIndex!==subStart,'rhythm not ticking');
          const hnRect2 = hnoss.getBoundingClientRect();
          assert(Math.abs(hnRect2.left-hnRect1.left)+Math.abs(hnRect2.top-hnRect1.top)>4,'Hnoss not moving');
          const anyKey = kbSvg.querySelector('rect'); const op1 = parseFloat(anyKey?.getAttribute('opacity')||'0');
          setTimeout(()=>{
            try{
              const op2 = parseFloat(anyKey?.getAttribute('opacity')||'0');
              assert(Math.abs(op2-op1)>0.02,'keyboard wave not affecting opacity');
              results.push({ok:true,name:'Frames/Bewegung/Rhythmus/Keyboard/Nodes'});
            }catch(e){ results.push({ok:false,name:'Frames/Bewegung/Rhythmus/Keyboard/Nodes',msg:e.message}); }
            report(results);
          }, 400);
        }catch(e){ results.push({ok:false,name:'Frames/Bewegung/Rhythmus/Keyboard/Nodes',msg:e.message}); report(results); }
      }, 600);
      report(results);
    }

    // --- Boot ---
    onResize();
    window.addEventListener('resize', onResize, { passive: true });
    rafId = requestAnimationFrame(loop);
    setTimeout(runSelfTests, 250);

    return ()=>{ cancelAnimationFrame(rafId); window.removeEventListener('resize', onResize); };
  }, []);

  // --- Styles (Inline, kein TS "as const") ---
  const hnossStyle = {
    position:'absolute', left:'50%', top:'50%', transform:'translate(-50%,-50%)',
    font:'800 68px/1.05 "JetBrains Mono", ui-monospace, monospace', color:'#ff4fb0',
    textShadow:'0 0 10px rgba(255,77,166,.9), 0 0 22px rgba(255,215,0,.75), 0 0 48px rgba(255,160,0,.55), 0 0 80px rgba(255,215,0,.35)',
    letterSpacing:'.04em', mixBlendMode:'screen', pointerEvents:'none', zIndex:4
  };

  return (
    <div className="w-screen h-screen bg-black overflow-hidden">
      <div ref={stageRef} className="relative w-full h-full bg-black" aria-label="Matrix Szene">
        <canvas ref={matrixRef} className="absolute inset-0 block" />
        <canvas ref={fxRef} className="absolute inset-0 block pointer-events-none" />
        <div ref={shapesRef} className="absolute inset-0" />
        <svg ref={nodesRef} className="absolute inset-0 pointer-events-none" />
        <svg ref={keyboardRef} className="absolute inset-0 pointer-events-none" />
        <div ref={hnossRef} style={hnossStyle}>Hnoss</div>
      </div>
      <div className="fixed left-2 top-2 z-[6] text-[12px] leading-tight text-green-200 bg-black/45 px-2.5 py-2 rounded-md border border-green-300/20">
        <div><span className="inline-block w-[10px] h-[10px] mr-1.5 align-[-.1rem] rounded-[2px]" style={{background:'#62ff62'}}></span>API</div>
        <div><span className="inline-block w-[10px] h-[10px] mr-1.5 align-[-.1rem] rounded-[2px]" style={{background:'#62c9ff'}}></span>Tool</div>
        <div><span className="inline-block w-[10px] h-[10px] mr-1.5 align-[-.1rem] rounded-[2px]" style={{background:'#ff62f5'}}></span>Programm</div>
        <div><span className="inline-block w-[10px] h-[10px] mr-1.5 align-[-.1rem] rounded-[2px]" style={{background:'#ffb762'}}></span>MCP Server</div>
      </div>
      <div ref={selftestRef} className="fixed right-2 bottom-2 z-[9] hidden text-[12px] leading-snug font-mono text-emerald-300 bg-emerald-950/70 px-2.5 py-2 rounded-md max-w-[60vw]" aria-live="polite" />
    </div>
  );
}
