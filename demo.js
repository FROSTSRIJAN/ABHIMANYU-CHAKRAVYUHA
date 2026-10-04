const demoMessages = [
  'ABC Ltd may announce a new manufacturing project next quarter, according to early market chatter.',
  'ABC Ltd has confirmed a major manufacturing project and investors are expecting a strong reaction.',
  'Confirmed! ABC Ltd is set to explode after the project news. Guaranteed profit — invest immediately before everyone finds out.'
];
let messages = ['', '', ''];
let lang = 'en';
const screens = ['homeScreen','analyzerScreen','processingScreen','resultsScreen'];
const safety = {
  en: ['Pause before acting on messages that combine certainty with urgency.','Verify important claims independently using appropriate official sources.','Do not treat a forwarded message or repeated claim as evidence by itself.'],
  hi: ['ऐसे संदेशों पर तुरंत कार्रवाई न करें जिनमें बहुत ज़्यादा निश्चितता और जल्दी करने का दबाव हो।','महत्वपूर्ण दावों को उपयुक्त आधिकारिक स्रोतों से स्वतंत्र रूप से सत्यापित करें।','सिर्फ़ फ़ॉरवर्ड किए गए या बार-बार दोहराए गए संदेश को प्रमाण न मानें।']
};
const explanation = {
  en: 'The first message is cautious and frames the information as a possibility. The second version removes that uncertainty and presents the project as confirmed. The third version goes further by introducing a guaranteed financial outcome, urgency, and exclusivity. EchoTrap is identifying changes in language and framing; it is not proving whether the underlying claim is true or false.',
  hi: 'पहले संदेश में जानकारी को संभावना के रूप में रखा गया है। दूसरे संदेश में वही बात अधिक निश्चित तरीके से “कन्फर्म” बताई गई है। तीसरे संदेश में गारंटीड लाभ, तुरंत कार्रवाई और सीमित अवसर जैसी भाषा जोड़ दी गई है। EchoTrap केवल भाषा और दावे में आए बदलाव दिखाता है; यह अपने-आप यह साबित नहीं करता कि मूल दावा सही है या गलत।'
};
function show(id){ screens.forEach(s=>document.getElementById(s).classList.toggle('active',s===id)); window.scrollTo(0,0); }
function loadDemo(){ messages=[...demoMessages]; renderMessages(); }
function valid(){ return messages.length>=2 && messages.every(m=>m.trim().length>=12); }
function renderMessages(){
  const stack=document.getElementById('messageStack');
  stack.innerHTML='';
  messages.forEach((m,i)=>{
    const card=document.createElement('div'); card.className='input-card';
    card.innerHTML=`<div class="input-card-top"><div><span class="input-number">${String(i+1).padStart(2,'0')}</span><strong>${i===0?'Earliest version':i===messages.length-1?'Latest version':'Version '+(i+1)}</strong></div>${messages.length>2?`<button class="icon-button" data-remove="${i}" aria-label="Remove message">×</button>`:''}</div><textarea maxlength="500" placeholder="Paste the financial message exactly as you received it…">${m}</textarea><div class="input-meta"><span>${m.length}/500</span><span>${m.trim().length>0&&m.trim().length<12?'Add a little more context':'Text only'}</span></div>`;
    const ta=card.querySelector('textarea');
    ta.addEventListener('input',e=>{ messages[i]=e.target.value; card.querySelector('.input-meta span').textContent=`${e.target.value.length}/500`; updateRunState(); });
    const rm=card.querySelector('[data-remove]'); if(rm) rm.addEventListener('click',()=>{ messages.splice(i,1); renderMessages(); });
    stack.appendChild(card);
  });
  document.getElementById('messageCount').textContent=`${messages.length}/5`;
  document.getElementById('addMessage').style.display=messages.length<5?'flex':'none';
  updateRunState();
}
function updateRunState(){ const ok=valid(); document.getElementById('runAnalysis').disabled=!ok; document.getElementById('helperText').style.display=ok?'none':'block'; }
function renderSafety(){
  document.getElementById('langLabel').textContent=lang==='en'?'EN':'हिं';
  document.getElementById('explainLang').textContent=lang==='en'?'English':'हिंदी';
  document.getElementById('explanationCopy').textContent=explanation[lang];
  document.getElementById('safetyTitle').textContent=lang==='en'?'Before acting on the claim':'दावे पर कार्रवाई करने से पहले';
  document.getElementById('safetyList').innerHTML=safety[lang].map((s,i)=>`<div><span>${String(i+1).padStart(2,'0')}</span><p>${s}</p></div>`).join('');
}
document.getElementById('homeBtn').onclick=()=>show('homeScreen');
document.getElementById('navAnalyze').onclick=()=>show('analyzerScreen');
document.getElementById('startBtn').onclick=()=>{ loadDemo(); show('analyzerScreen'); };
document.getElementById('loadSample').onclick=loadDemo;
document.getElementById('addMessage').onclick=()=>{ if(messages.length<5){ messages.push(''); renderMessages(); }};
document.getElementById('runAnalysis').onclick=()=>{ if(!valid()) return; show('processingScreen'); setTimeout(()=>show('resultsScreen'),1700); };
document.getElementById('newAnalysis').onclick=()=>show('analyzerScreen');
document.getElementById('langBtn').onclick=()=>{ lang=lang==='en'?'hi':'en'; renderSafety(); };
renderMessages(); renderSafety();
