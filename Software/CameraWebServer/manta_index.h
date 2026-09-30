#pragma once

// Stored in flash. Line recognition and warning audio run in the connected
// browser so the ESP32 only has to serve this page and the camera stream.
static const char manta_index_html[] PROGMEM = R"MANTAHTML(
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MANTA Path Test</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#111;color:#eee;font:16px system-ui,sans-serif;text-align:center}main{max-width:720px;margin:auto;padding:12px}h1{font-size:20px;margin:4px 0 10px}#status{padding:18px 8px;background:#555;color:#fff;font-size:28px;font-weight:700}#metrics{font-size:14px;margin-top:5px}canvas{display:block;width:100%;height:auto;margin:10px 0;background:#000}button,select,input{font:inherit}button{padding:10px 18px;margin:4px}details{margin-top:10px;text-align:left;border:1px solid #555;padding:8px}summary{cursor:pointer}label{display:block;margin:10px 0}.value{float:right}input[type=range]{width:100%}.small{font-size:13px;color:#bbb}#source{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}#alert{position:fixed;inset:0;z-index:10;display:none;pointer-events:none;align-items:flex-start;justify-content:center;padding-top:max(34px,env(safe-area-inset-top));border:14px solid transparent}#alert.active{display:flex}#alert.drift{border-color:#ff9d00;background:rgba(255,157,0,.08);animation:pulse 1.2s infinite}#alert.critical{border-color:#f00000;background:rgba(240,0,0,.2);animation:flash .55s steps(2,end) infinite}#alertText{width:100%;padding:12px;background:#111;color:#fff;font-size:30px;font-weight:800}@keyframes pulse{50%{background:rgba(255,157,0,.2)}}@keyframes flash{50%{background:rgba(240,0,0,.04);border-color:#500}}
</style>
</head>
<body>
<div id="alert" role="alert" aria-live="assertive"><div id="alertText"></div></div>
<main>
<h1>MANTA PATH TEST</h1>
<div id="status">READY<div id="metrics">Press Start</div></div>
<canvas id="view" width="160" height="120"></canvas>
<img id="source" crossorigin="anonymous" alt="">
<button id="start">Start tracking</button>
<button id="stop" disabled>Stop</button>

<details>
<summary>Settings</summary>
<label>Red minimum <span class="value" id="redOut">120</span><input id="redMin" type="range" min="40" max="240" value="120"></label>
<label>Red dominance <span class="value" id="ratioOut">1.45</span><input id="ratio" type="range" min="110" max="250" value="145"></label>
<label>Clear zone <span class="value" id="safeOut">10%</span><input id="safe" type="range" min="2" max="30" value="10"></label>
<label>Alarm point <span class="value" id="alarmOut">25%</span><input id="alarm" type="range" min="10" max="60" value="25"></label>
<label><input id="sound" type="checkbox" checked> Sound</label>
<label>Camera resolution
<select id="resolution">
<option value="1">160 x 120</option>
<option value="5" selected>320 x 240</option>
<option value="8">640 x 480</option>
</select>
</label>
<p class="small">Detection runs on this phone. Adjust Red minimum and Red dominance until only the tape is tracked.</p>
</details>
</main>
<script>
const W=160,H=120;
const view=document.getElementById('view'),ctx=view.getContext('2d',{willReadFrequently:true});
const source=document.getElementById('source'),statusBox=document.getElementById('status'),metrics=document.getElementById('metrics');
const startButton=document.getElementById('start'),stopButton=document.getElementById('stop');
const alertBox=document.getElementById('alert'),alertText=document.getElementById('alertText');
let timer=null,audio=null,lastBeep=0,pathState='starting';
const streamURL=`${location.protocol}//${location.hostname}:81/stream`;

function value(id){return Number(document.getElementById(id).value)}
function colour(t){t=Math.max(0,Math.min(1,t));return `rgb(${Math.round(20+215*t)},${Math.round(180*(1-t))},35)`}
function setStatus(title,detail,c){statusBox.style.background=c;statusBox.firstChild.nodeValue=title;metrics.textContent=detail}

function showAlert(level,text){alertBox.className=`active ${level}`;alertText.textContent=text}
function hideAlert(){alertBox.className='';alertText.textContent=''}
function tone(freq,duration,delay=0,volume=.16){
  const start=audio.currentTime+delay,osc=audio.createOscillator(),gain=audio.createGain();
  osc.frequency.setValueAtTime(freq,start);gain.gain.setValueAtTime(volume,start);gain.gain.exponentialRampToValueAtTime(.001,start+duration);
  osc.connect(gain).connect(audio.destination);osc.start(start);osc.stop(start+duration+.02);
}
function speak(message){
  if(!document.getElementById('sound').checked||!('speechSynthesis' in window))return;
  speechSynthesis.cancel();
  const words=new SpeechSynthesisUtterance(message);words.rate=.95;words.volume=1;speechSynthesis.speak(words);
}
function recoveryDing(){
  if(!document.getElementById('sound').checked||!audio)return;
  if(audio.state==='suspended')audio.resume().catch(()=>{});
  tone(880,.08,0,.13);tone(1175,.18,.1,.16);
}
function changePathState(next){
  if(next===pathState)return;
  const previous=pathState;pathState=next;
  if(next==='lost')speak('Path lost');
  else if(next==='off')speak('Off path');
  else if(next==='on'&&(previous==='lost'||previous==='off'||previous==='drift')){
    recoveryDing();setTimeout(()=>speak('On track'),220);
  }
}
function soundAlarm(kind,severity=0){
  if(!document.getElementById('sound').checked||!audio)return;
  if(audio.state==='suspended')audio.resume().catch(()=>{});
  const now=performance.now(),gap=kind==='drift'?1800:kind==='lost'?420:650;if(now-lastBeep<gap)return;lastBeep=now;
  if(kind==='drift')tone(420+Math.round(severity*180),.09,0,.1);
  else if(kind==='lost'){tone(920,.11);tone(620,.13,.16)}
  else{tone(720,.12);tone(720,.12,.18)}
}
async function unlockAudio(){
  if(!audio)audio=new (window.AudioContext||window.webkitAudioContext)();
  await audio.resume();
  const silent=audio.createBufferSource();silent.buffer=audio.createBuffer(1,1,22050);silent.connect(audio.destination);silent.start();
}

function analyse(){
  if(!source.naturalWidth)return;
  try{ctx.drawImage(source,0,0,W,H)}catch(e){return}
  const pixels=ctx.getImageData(0,0,W,H).data;
  const redMin=value('redMin'),ratio=value('ratio')/100;
  let count=0,sumX=0,nearN=0,nearX=0,farN=0,farX=0;
  for(let y=4;y<H;y+=2){
    for(let x=0;x<W;x+=2){
      const i=(y*W+x)*4,r=pixels[i],g=pixels[i+1],b=pixels[i+2];
      if(r>=redMin&&r>g*ratio&&r>b*ratio){
        count++;sumX+=x;
        if(y>H*.58){nearN++;nearX+=x}else if(y<H*.42){farN++;farX+=x}
      }
    }
  }

  ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(W/2,0);ctx.lineTo(W/2,H);ctx.stroke();
  if(count<22){
    setStatus('PATH LOST',`Red samples: ${count}`,'#c41414');showAlert('critical','PATH LOST');changePathState('lost');soundAlarm('lost');return;
  }

  const cx=sumX/count,lateral=(cx-W/2)/(W/2);
  const near=nearN?nearX/nearN:cx,far=farN?farX/farN:cx;
  const heading=(near-far)/(W/2);
  const error=Math.min(1,Math.max(Math.abs(lateral),Math.abs(heading)*.65));
  const safe=value('safe')/100,alarm=value('alarm')/100;
  const progress=error<=safe?0:(error-safe)/Math.max(.01,alarm-safe);
  const direction=lateral<-safe?'LEFT':lateral>safe?'RIGHT':'';

  ctx.strokeStyle='#00ffff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(cx,0);ctx.lineTo(cx,H);ctx.stroke();
  const detail=`Offset ${Math.round(lateral*100)}% | Heading ${Math.round(heading*100)}%`;
  if(error<=safe){setStatus('ON PATH',detail,colour(0));hideAlert();changePathState('on')}
  else if(error<alarm){const text=`DRIFT ${direction}`.trim();setStatus(text,detail,colour(progress));showAlert('drift',text);changePathState('drift');soundAlarm('drift',progress)}
  else{const text=`OFF PATH ${direction}`.trim();setStatus(text,detail,colour(1));showAlert('critical',text);changePathState('off');soundAlarm('off')}
}

async function start(){
  try{await unlockAudio()}catch(e){}
  pathState='starting';
  source.src=streamURL;clearInterval(timer);timer=setInterval(analyse,100);
  startButton.disabled=true;stopButton.disabled=false;setStatus('STARTING','Waiting for camera','#555');
}
function stop(){clearInterval(timer);timer=null;source.src='';pathState='starting';if('speechSynthesis' in window)speechSynthesis.cancel();startButton.disabled=false;stopButton.disabled=true;hideAlert();setStatus('STOPPED','Press Start','#555');ctx.clearRect(0,0,W,H)}
startButton.onclick=start;stopButton.onclick=stop;

for(const [input,out,suffix,scale] of [['redMin','redOut','',1],['ratio','ratioOut','',.01],['safe','safeOut','%',1],['alarm','alarmOut','%',1]]){
  document.getElementById(input).oninput=e=>document.getElementById(out).textContent=(e.target.value*scale).toFixed(input==='ratio'?2:0)+suffix;
}
document.getElementById('resolution').onchange=e=>fetch(`/control?var=framesize&val=${e.target.value}`).catch(()=>{});
</script>
</body>
</html>
)MANTAHTML";
