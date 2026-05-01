import re

NEW_STORY = r"""// ── STORY CANVAS — Illustrated Student Scene ─────────────────────────
(function(){
  const canvas=document.getElementById('storyCanvas');
  if(!canvas)return;
  const ctx=canvas.getContext('2d');
  let W,H,phase=0,animT=0,phaseT=0;

  const CONCEPTS=[
    {label:'Arrays',    cx:0.62,cy:0.18,tx:0.60,ty:0.22,weak:false,color:'#6366f1'},
    {label:'Pointers',  cx:0.90,cy:0.30,tx:0.75,ty:0.38,weak:true, color:'#ef4444'},
    {label:'LinkedList',cx:0.55,cy:0.50,tx:0.60,ty:0.54,weak:false,color:'#6366f1'},
    {label:'Recursion', cx:0.85,cy:0.60,tx:0.75,ty:0.54,weak:false,color:'#6366f1'},
    {label:'Trees',     cx:0.68,cy:0.72,tx:0.60,ty:0.70,weak:true, color:'#ef4444'},
    {label:'BST Ops',   cx:0.92,cy:0.78,tx:0.75,ty:0.70,weak:true, color:'#ef4444'},
    {label:'Graphs',    cx:0.58,cy:0.85,tx:0.60,ty:0.86,weak:false,color:'#10b981'},
    {label:'Sorting',   cx:0.80,cy:0.88,tx:0.75,ty:0.86,weak:false,color:'#10b981'},
  ];
  const EDGES=[[0,2],[2,4],[4,6],[6,7],[1,2],[3,4],[5,4],[2,3]];

  const QMARKS=Array.from({length:10},(_,i)=>({
    x:0.08+Math.random()*0.32,y:0.08+Math.random()*0.58,
    char:['?','?','!','??','!?','?!'][i%6],
    speed:0.00035+Math.random()*0.0005,
    size:9+Math.random()*8,phase:Math.random()*Math.PI*2,
    alpha:0.25+Math.random()*0.35,
  }));

  function resize(){
    const dpr=Math.min(window.devicePixelRatio,2);
    const rect=canvas.parentElement.getBoundingClientRect();
    W=canvas.width=rect.width*dpr;
    H=canvas.height=Math.round(420*dpr);
    canvas.style.width=rect.width+'px';canvas.style.height='420px';
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  const lerp=(a,b,t)=>a+(b-a)*Math.min(1,Math.max(0,t));
  const easeOut=(t)=>1-(1-t)*(1-t);

  function drawStudent(w,h,t){
    const deskY=h*0.85,deskX=w*0.03,deskW=w*0.40,deskH=12;
    // Desk
    const dg=ctx.createLinearGradient(deskX,deskY,deskX,deskY+deskH*3);
    dg.addColorStop(0,'rgba(51,65,85,0.95)');dg.addColorStop(1,'rgba(30,41,59,0.7)');
    ctx.fillStyle=dg;ctx.beginPath();ctx.roundRect(deskX,deskY,deskW,deskH*3,4);ctx.fill();
    ctx.beginPath();ctx.moveTo(deskX,deskY);ctx.lineTo(deskX+deskW,deskY);
    ctx.strokeStyle='rgba(99,102,241,0.4)';ctx.lineWidth=1.5;ctx.stroke();

    // Laptop
    const lapX=deskX+deskW*0.55,lapY=deskY-62,lapW=66,lapH=42;
    const ga=phase>=2?0.40:0.08+0.05*Math.sin(t*1.5);
    const sg=ctx.createRadialGradient(lapX,lapY+lapH/2,2,lapX,lapY+lapH/2,lapW);
    sg.addColorStop(0,`rgba(99,102,241,${ga})`);sg.addColorStop(1,'transparent');
    ctx.fillStyle=sg;ctx.fillRect(lapX-lapW,lapY-12,lapW*2,lapH*1.8);
    ctx.beginPath();ctx.roundRect(lapX-lapW/2,lapY,lapW,lapH,4);
    ctx.fillStyle='rgba(15,23,42,0.97)';ctx.fill();
    ctx.strokeStyle=phase>=2?'rgba(16,185,129,0.55)':'rgba(99,102,241,0.3)';
    ctx.lineWidth=1.5;ctx.stroke();
    const lc=phase>=2?'rgba(16,185,129,0.55)':'rgba(99,102,241,0.3)';
    [0.3,0.52,0.72].forEach((f,i)=>{
      ctx.beginPath();ctx.moveTo(lapX-lapW/2+8,lapY+lapH*f);
      ctx.lineTo(lapX-lapW/2+8+(lapW-16)*(0.35+0.55*Math.sin(t*0.8+i)),lapY+lapH*f);
      ctx.strokeStyle=lc;ctx.lineWidth=1.5;ctx.stroke();
    });
    ctx.beginPath();ctx.moveTo(lapX-lapW/2-4,deskY);ctx.lineTo(lapX+lapW/2+4,deskY);
    ctx.strokeStyle='rgba(51,65,85,0.9)';ctx.lineWidth=7;ctx.stroke();

    // Student figure
    const stuX=w*0.18,sShY=deskY-32;
    const hunch=phase>=2?0:14;
    // Torso
    ctx.beginPath();ctx.moveTo(stuX-17,deskY+2);
    ctx.bezierCurveTo(stuX-17,sShY+hunch,stuX+17,sShY+hunch,stuX+17,deskY+2);
    ctx.fillStyle='rgba(67,56,202,0.75)';ctx.fill();
    ctx.strokeStyle='rgba(99,102,241,0.3)';ctx.lineWidth=1;ctx.stroke();
    // Arms
    ctx.beginPath();ctx.moveTo(stuX-17,sShY+hunch+10);
    ctx.bezierCurveTo(stuX-20,deskY-4,lapX-42,deskY-3,lapX-28,deskY-3);
    ctx.strokeStyle='rgba(67,56,202,0.7)';ctx.lineWidth=9;ctx.lineCap='round';ctx.stroke();
    ctx.lineCap='butt';
    // Head
    const hdY=sShY-20+hunch;
    const haloC=phase===0?`rgba(239,68,68,${0.14+0.06*Math.sin(t*2)})`:phase===1?`rgba(245,158,11,${0.13+0.05*Math.sin(t*2)})`:`rgba(16,185,129,${0.14+0.05*Math.sin(t)})`;
    ctx.beginPath();ctx.arc(stuX,hdY,21,0,Math.PI*2);ctx.fillStyle=haloC;ctx.fill();
    ctx.beginPath();ctx.arc(stuX,hdY,15,0,Math.PI*2);
    ctx.fillStyle='rgba(30,41,59,0.97)';ctx.fill();
    ctx.strokeStyle=phase>=2?'rgba(16,185,129,0.5)':phase===1?'rgba(245,158,11,0.4)':'rgba(99,102,241,0.4)';
    ctx.lineWidth=1.5;ctx.stroke();
    // Face expressions
    if(phase===0){
      ctx.fillStyle='rgba(239,68,68,0.85)';
      [stuX-5,stuX+5].forEach(ex=>{ctx.beginPath();ctx.arc(ex,hdY-3,1.8,0,Math.PI*2);ctx.fill();});
      ctx.beginPath();ctx.moveTo(stuX-4,hdY+6);ctx.bezierCurveTo(stuX-1,hdY+4,stuX+2,hdY+8,stuX+5,hdY+6);
      ctx.strokeStyle='rgba(239,68,68,0.7)';ctx.lineWidth=1.5;ctx.stroke();
    } else if(phase===1){
      ctx.fillStyle='rgba(245,158,11,0.9)';
      [stuX-5,stuX+5].forEach(ex=>{ctx.beginPath();ctx.arc(ex,hdY-3,2.2,0,Math.PI*2);ctx.fill();});
      ctx.beginPath();ctx.moveTo(stuX-4,hdY+5);ctx.lineTo(stuX+4,hdY+5);
      ctx.strokeStyle='rgba(245,158,11,0.7)';ctx.lineWidth=1.5;ctx.stroke();
    } else {
      ctx.fillStyle='rgba(16,185,129,0.9)';
      [stuX-5,stuX+5].forEach(ex=>{ctx.beginPath();ctx.arc(ex,hdY-3,1.8,0,Math.PI*2);ctx.fill();});
      ctx.beginPath();ctx.arc(stuX,hdY+3,5,0.1,Math.PI-0.1);
      ctx.strokeStyle='rgba(16,185,129,0.8)';ctx.lineWidth=1.5;ctx.stroke();
    }
    // Thought bubble dots (phase 0 only)
    if(phase===0){
      [[stuX+w*0.04,hdY-30],[stuX+w*0.07,hdY-45],[stuX+w*0.11,hdY-56]].forEach(([bx,by],i)=>{
        const br=2.5+i*1.8;
        ctx.beginPath();ctx.arc(bx,by,br*(0.7+0.3*Math.sin(t*2+i)),0,Math.PI*2);
        ctx.fillStyle=`rgba(99,102,241,${0.22+0.08*Math.sin(t*1.5+i)})`;ctx.fill();
      });
    }
  }

  function drawThoughtCloud(w,h,t){
    if(phase>=2)return;
    const cx=w*0.36,cy=h*0.28,cw=w*0.10,ch=h*0.08;
    const a=phase===1?0.25:0.18+0.05*Math.sin(t*1.2);
    ctx.beginPath();
    for(let ang=0;ang<Math.PI*2;ang+=0.12){
      const bump=0.82+0.18*Math.sin(ang*5+t*0.4);
      const rx=(ang<Math.PI?cw*1.4:cw)*bump,ry=ch*bump;
      const x=cx+rx*Math.cos(ang),y=cy+ry*Math.sin(ang);
      ang<0.15?ctx.moveTo(x,y):ctx.lineTo(x,y);
    }
    ctx.closePath();
    ctx.fillStyle=`rgba(30,27,75,${a+0.12})`;ctx.fill();
    ctx.strokeStyle=`rgba(99,102,241,${a})`;ctx.lineWidth=1;ctx.stroke();
    ctx.fillStyle=`rgba(148,163,184,${a*2.5})`;
    ctx.font='700 9px Inter,sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText('???',cx,cy);
  }

  function drawConfusion(w,h,t){
    if(phase>=2)return;
    const fade=phase===1?0.3:1;
    QMARKS.forEach(q=>{
      const x=q.x*w,y=(q.y-(t*q.speed*800%0.45))*h;
      ctx.fillStyle=`rgba(239,68,68,${q.alpha*fade*Math.abs(Math.sin(t*1.5+q.phase))})`;
      ctx.font=`700 ${q.size}px Inter,sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(q.char,x,y);
    });
  }

  function drawConcepts(w,h,t){
    const p=easeOut(Math.min(1,phaseT/1.4));
    if(phase>=1){
      EDGES.forEach(([a,b])=>{
        const na=CONCEPTS[a],nb=CONCEPTS[b];
        const ax=lerp(na.cx,na.tx,p)*w,ay=lerp(na.cy,na.ty,p)*h;
        const bx=lerp(nb.cx,nb.tx,p)*w,by=lerp(nb.cy,nb.ty,p)*h;
        const ea=Math.min(1,phaseT*0.85);
        const weak=na.weak||nb.weak;
        ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(bx,by);
        if(weak&&phase===1){ctx.strokeStyle=`rgba(239,68,68,${ea*0.55})`;ctx.setLineDash([4,4]);}
        else{ctx.strokeStyle=phase>=2?`rgba(16,185,129,${ea*0.65})`:`rgba(99,102,241,${ea*0.45})`;ctx.setLineDash([]);}
        ctx.lineWidth=1.5;ctx.stroke();ctx.setLineDash([]);
      });
    }
    CONCEPTS.forEach((n,i)=>{
      const x=lerp(n.cx,n.tx,p)*w;
      const chaos=(phase===0?1:1-p)*5;
      const fx=x+Math.sin(t*0.75+i*1.4)*chaos;
      const fy=(lerp(n.cy,n.ty,p)*h)+Math.cos(t*0.65+i)*chaos;
      const isWeak=n.weak&&phase>=1,isRes=n.weak&&phase>=2,r=13;
      const col=isRes?'#10b981':isWeak?'#ef4444':n.color;
      if(isWeak&&!isRes){
        const gg=ctx.createRadialGradient(fx,fy,0,fx,fy,r*2.4);
        gg.addColorStop(0,`rgba(239,68,68,${0.28+0.12*Math.sin(t*3+i)})`);gg.addColorStop(1,'transparent');
        ctx.beginPath();ctx.arc(fx,fy,r*2.4,0,Math.PI*2);ctx.fillStyle=gg;ctx.fill();
      } else if(isRes){
        const gg=ctx.createRadialGradient(fx,fy,0,fx,fy,r*2);
        gg.addColorStop(0,'rgba(16,185,129,0.22)');gg.addColorStop(1,'transparent');
        ctx.beginPath();ctx.arc(fx,fy,r*2,0,Math.PI*2);ctx.fillStyle=gg;ctx.fill();
      }
      ctx.beginPath();ctx.arc(fx,fy,r,0,Math.PI*2);
      ctx.fillStyle=col;ctx.fill();
      ctx.strokeStyle='rgba(255,255,255,0.12)';ctx.lineWidth=1.2;ctx.stroke();
      ctx.fillStyle='rgba(255,255,255,0.88)';
      ctx.font='500 8px Inter,sans-serif';ctx.textAlign='center';ctx.textBaseline='top';
      ctx.fillText(n.label,fx,fy+r+3);
    });
  }

  function drawStatus(w,h){
    const msgs=[
      '\u{1F615}  Student struggling \u2014 knowledge graph is broken & disconnected',
      '\u{1F534}  GCN scanning topology \u2014 weak prerequisite gaps detected',
      '\u2705  Personalized path activated \u2014 gaps resolved, graph structured'
    ];
    const cols=['rgba(239,68,68,0.75)','rgba(245,158,11,0.85)','rgba(16,185,129,0.85)'];
    ctx.fillStyle=cols[phase];ctx.font='500 11px Inter,sans-serif';
    ctx.textAlign='center';ctx.textBaseline='bottom';
    ctx.fillText(msgs[phase],w/2,h-8);
  }

  function drawScene(){
    const w=W/Math.min(window.devicePixelRatio,2),h=H/Math.min(window.devicePixelRatio,2);
    ctx.clearRect(0,0,w,h);
    // Subtle right-panel grid
    ctx.strokeStyle='rgba(99,102,241,0.04)';ctx.lineWidth=1;
    for(let gx=w*0.46;gx<w;gx+=30){ctx.beginPath();ctx.moveTo(gx,0);ctx.lineTo(gx,h);ctx.stroke();}
    for(let gy=0;gy<h;gy+=30){ctx.beginPath();ctx.moveTo(w*0.46,gy);ctx.lineTo(w,gy);ctx.stroke();}
    ctx.beginPath();ctx.moveTo(w*0.46,h*0.04);ctx.lineTo(w*0.46,h*0.91);
    ctx.strokeStyle='rgba(99,102,241,0.1)';ctx.lineWidth=1;ctx.stroke();
    ctx.fillStyle='rgba(100,116,139,0.45)';ctx.font='500 9px Inter,sans-serif';ctx.textAlign='center';ctx.textBaseline='top';
    ctx.fillText('STUDENT',w*0.23,6);ctx.fillText('KNOWLEDGE GRAPH',w*0.73,6);
    drawStudent(w,h,animT);
    drawThoughtCloud(w,h,animT);
    drawConfusion(w,h,animT);
    drawConcepts(w,h,animT);
    drawStatus(w,h);
  }

  function loop(){animT+=0.012;phaseT+=0.022;drawScene();requestAnimationFrame(loop);}
  resize();loop();
  window.addEventListener('resize',resize);

  document.querySelectorAll('.story-phase-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const np=parseInt(btn.dataset.phase);
      if(np===phase)return;
      phase=np;phaseT=0;
      document.querySelectorAll('.story-phase-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Auto-advance on scroll into view
  let ran=false;
  new IntersectionObserver(entries=>{
    if(entries[0].isIntersecting&&!ran){
      ran=true;
      const btns=document.querySelectorAll('.story-phase-btn');
      setTimeout(()=>{phase=1;phaseT=0;btns.forEach(b=>b.classList.remove('active'));btns[1]?.classList.add('active');},2000);
      setTimeout(()=>{phase=2;phaseT=0;btns.forEach(b=>b.classList.remove('active'));btns[2]?.classList.add('active');},4500);
    }
  },{threshold:0.45}).observe(canvas);
})();
"""

with open('/Users/karthiks/Desktop/test/GraphEdu explanation/index.html','r') as f:
    content = f.read()

OLD_START = '// ── STORY CANVAS — Illustrated Student Scene ─────────────────────────'
OLD_START2 = '// ── STORY CANVAS ─────────────────────────────────────────────────────'
AFTER_MARKER = '// ── GCN NEURAL NETWORK CANVAS'

# Try new marker first, then old
start_marker = OLD_START if OLD_START in content else OLD_START2
if start_marker not in content:
    print("ERROR: start marker not found")
else:
    idx_s = content.index(start_marker)
    idx_e = content.index(AFTER_MARKER, idx_s)
    # Find the end of the story IIFE: the })(); before the GCN marker
    chunk = content[idx_s:idx_e]
    new_content = content[:idx_s] + NEW_STORY.strip() + '\n\n' + content[idx_e:]
    with open('/Users/karthiks/Desktop/test/GraphEdu explanation/index.html','w') as f:
        f.write(new_content)
    print(f"SUCCESS. Lines: {len(new_content.splitlines())}")
