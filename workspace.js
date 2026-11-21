(() => {
  const $ = id => document.getElementById(id);
  const root = document.documentElement;
  const account = document.body.dataset.account;
  const prefix = 'errand:' + account + ':';
  const keyName = prefix + 'openrouter';
  const get = (storage,key) => { try { return storage.getItem(key); } catch { return null; } };
  const set = (storage,key,value) => { try { storage.setItem(key,value); return true; } catch { return false; } };
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const prefers = key => get(localStorage,prefix+key) !== 'off';
  const savePref = (key,on) => set(localStorage,prefix+key,on?'on':'off');
  function theme(value) {
    root.dataset.theme=value;
    set(localStorage,'errand:theme',value);
    if ($('pref-theme')) $('pref-theme').value=value;
  }
  document.querySelector('[data-theme-switch]').onclick=() => theme(root.dataset.theme==='dark'?'light':'dark');
  const toggleRail = () => {
    const mobile=matchMedia('(max-width:760px)').matches;
    const flag=mobile?'menuOpen':'railSmall';
    const opened=root.dataset[flag]!=='yes';
    root.dataset[flag]=opened?'yes':'no';
    document.querySelector('.mobilemenu').setAttribute('aria-expanded',String(mobile && opened));
    document.querySelector('.collapse').setAttribute('aria-expanded',String(mobile?opened:!opened));
    if (!mobile) set(localStorage,'errand:rail',root.dataset.railSmall);
  };
  root.dataset.railSmall=get(localStorage,'errand:rail') || 'no';
  document.querySelector('.collapse').onclick=toggleRail;
  document.querySelector('.mobilemenu').onclick=toggleRail;
  document.addEventListener('keydown',event=>{if(event.key==='Escape') root.dataset.menuOpen='no';});
  const dialog=$('capi-dialog');
  const launcher=$('capi-launch');
  const messages=$('messages');
  const input=$('chat-input');
  const starters=document.querySelector('.starters');
  let controller=null;
  const history=[];
  function mascot(state) { dialog.dataset.state=launcher.dataset.state=state; }
  function applyPrefs() {
    launcher.hidden=!prefers('mascot');
    document.querySelector('.notify').hidden=!prefers('notifications');
  }
  applyPrefs();
  launcher.onclick=()=>{dialog.showModal(); input.focus(); mascot('listening');};
  dialog.querySelector('[data-close]').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{controller?.abort(); mascot('idle'); launcher.focus();});
  input.addEventListener('input',()=>{if(!controller) mascot(input.value?'listening':'idle');});
  if (location.pathname.startsWith('/run/')) set(sessionStorage,prefix+'notice','Your latest route comparison is ready.');
  $('notif-text').textContent=get(sessionStorage,prefix+'notice') || 'No new route updates.';
  const secret=()=>get(sessionStorage,keyName) || '';
  const openrouter='https://openrouter.ai/api/v1';
  const model='nvidia/nemotron-3-ultra-550b-a55b:free';
  const reason=status=>({401:'OpenRouter rejected this key. Update it in Settings.',403:'OpenRouter or the selected model provider denied the request.',429:'The free model reached its request limit. Try again later.'}[status] || 'OpenRouter could not complete this request. Try again.');
  if ($('api-key')) {
    const key=$('api-key'),status=$('key-status');
    key.value=secret();
    status.textContent=key.value?'An OpenRouter key is stored for this tab. Test it to verify the connection.':'No OpenRouter key saved.';
    $('reveal-key').onclick=()=>{key.type=key.type==='password'?'text':'password'; $('reveal-key').textContent=key.type==='text'?'Hide':'Show';};
    $('forget-key').onclick=()=>{sessionStorage.removeItem(keyName);key.value='';status.textContent='Key removed.';};
    $('check-key').onclick=async()=>{
      const candidate=key.value.trim();
      if (!candidate) { status.textContent='Enter your OpenRouter key first.';return; }
      status.textContent='Testing the connection…';
      try {
        const response=await fetch(openrouter+'/models',{headers:{Authorization:'Bearer '+candidate,'HTTP-Referer':location.origin,'X-Title':'ErrandLab'},signal:AbortSignal.timeout(15000),credentials:'omit',redirect:'error'});
        if(candidate!==key.value.trim()) return;
        if(!response.ok) throw new Error(reason(response.status));
        status.textContent=set(sessionStorage,keyName,candidate)?'Connected. Key saved for this tab.':'Connected, but browser storage is unavailable.';
      } catch(e) {status.textContent=e instanceof TypeError?'Could not reach OpenRouter. Check your connection.':e.message;}
    };
    $('pref-theme').value=root.dataset.theme;
    $('pref-theme').onchange=e=>theme(e.target.value);
    $('pref-intensity').value=root.dataset.motion;
    $('pref-intensity').onchange=e=>{root.dataset.motion=e.target.value;set(localStorage,'errand:motion',e.target.value);};
    for(const k of ['mascot','notifications']){
      const field=$('pref-'+k);
      field.checked=prefers(k);
      field.onchange=()=>{savePref(k,field.checked);applyPrefs();$('pref-status').textContent='Preference saved.';};
    }
  }
  function bubble(role,text) {
    const line=document.createElement('p');line.className='bubble '+role;
    line.textContent=text; messages.append(line);messages.scrollTop=messages.scrollHeight;return line;
  }
  async function stream(response,onText) {
    const reader=response.body.getReader(),decoder=new TextDecoder();
    let buffer='';
    try {
      while(true) {
        const {done,value}=await reader.read();
        buffer+=decoder.decode(value,{stream:!done});
        const lines=buffer.split(/\r?\n/);
        buffer=lines.pop();
        if(done && buffer){lines.push(buffer);buffer='';}
        for(const line of lines){
          if(!line.startsWith('data:')) continue;
          const payload=line.slice(5).trim();if(payload==='[DONE]') return;
          const event=JSON.parse(payload);
          if(event.error) throw new Error('OpenRouter interrupted this response.');
          const text=event.choices?.[0]?.delta?.content;
          if(text) onText(text);
        }
        if(done) return;
      }
    } finally {reader.releaseLock();}
  }
  $('chat-form').onsubmit=async e=>{
    e.preventDefault();
    const question=input.value.trim(), key=secret();
    if(!question || controller) return;
    if(!key){bubble('error','Add and test your OpenRouter key in Settings first.');return;}
    controller=new AbortController();
    const timeout=setTimeout(()=>controller?.abort(),50000);
    input.value='';bubble('user',question);const answer=bubble('assistant','Thinking…');
    mascot('thinking');$('chat-form').querySelector('button').disabled=true;
    let result='';
    try {
      const details=location.pathname.startsWith('/run/')?document.querySelector('.metrics')?.innerText:'';
      const res=await fetch(openrouter+'/chat/completions',{method:'POST',signal:controller.signal,credentials:'omit',redirect:'error',
        headers:{'Content-Type':'application/json',Authorization:'Bearer '+key,'HTTP-Referer':location.origin,'X-Title':'ErrandLab'},
        body:JSON.stringify({model,stream:true,max_tokens:420,
          messages:[{role:'system',content:'You are Capi, a concise, calm route-planning capybara. Help users understand errands, time windows and simulation uncertainty. You cannot edit their account or plan. Distinguish estimates from observed trips. Current page: '+document.title+'. Route metrics: '+(details||'none supplied')},...history.slice(-8),{role:'user',content:question}]})});
      if(!res.ok) throw new Error(reason(res.status));
      await stream(res,text=>{mascot('speaking');result+=text;answer.textContent=result;messages.scrollTop=messages.scrollHeight;});
      if(!result) throw new Error('No reply arrived. Try asking again.');
      history.push({role:'user',content:question},{role:'assistant',content:result});
    } catch(error) {answer.textContent=(result?result+' · ':'')+(error.name==='AbortError'?'Reply stopped.':error instanceof TypeError?'OpenRouter is unreachable. Check your connection.':error.message);}
    finally {clearTimeout(timeout);controller=null;mascot('idle');$('chat-form').querySelector('button').disabled=false;}
  };
  starters.onclick=e=>{if(e.target.tagName==='BUTTON'){input.value=e.target.textContent;$('chat-form').requestSubmit();}};
  document.querySelector('.logout')?.addEventListener('submit',()=>{
    controller?.abort();sessionStorage.removeItem(keyName);sessionStorage.removeItem(prefix+'notice');
    set(localStorage,prefix+'signout',String(Date.now()));
  });
  window.addEventListener('storage',event=>{
    if(event.key===prefix+'signout'){
      controller?.abort();sessionStorage.removeItem(keyName);sessionStorage.removeItem(prefix+'notice');
      location.replace('/login');
    }
  });
  window.addEventListener('pageshow',e=>{if(e.persisted) location.reload();});
  let frame=0;
  window.addEventListener('pointermove',e=>{
    if(frame || reduced.matches || root.dataset.motion!=='Full') return;
    frame=requestAnimationFrame(()=>{root.style.setProperty('--px',((e.clientX/innerWidth-.5)*14)+'px');root.style.setProperty('--py',((e.clientY/innerHeight-.5)*12)+'px');frame=0;});
  },{passive:true});
})();
