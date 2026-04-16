(function(){
  const API_KEY = 'mobile_events_v1';
  const EVENTS_KEY = 'mobile_events_store';
  const NOTES_KEY = 'mobile_notes_store';

  function q(id){return document.getElementById(id)}

  function isoDate(d){return d.toISOString().slice(0,10)}

  function mondayOf(date){
    const d = new Date(date);
    const day = d.getDay();
    const diff = (day + 6) % 7; // Monday=0
    d.setDate(d.getDate() - diff);
    d.setHours(0,0,0,0);
    return d;
  }

  function loadLocal(){
    const raw = localStorage.getItem(EVENTS_KEY);
    try{ return raw ? JSON.parse(raw) : null }catch(e){return null}
  }
  function saveLocal(events){
    localStorage.setItem(EVENTS_KEY, JSON.stringify(events || []));
  }
  function clearLocal(){
    localStorage.removeItem(EVENTS_KEY);
    render();
  }

  function loadNote(){
    return localStorage.getItem(NOTES_KEY) || '';
  }
  function saveNote(v){localStorage.setItem(NOTES_KEY, v)}
  function clearNote(){localStorage.removeItem(NOTES_KEY); q('noteText').value='';}

  function render(){
    const container = q('eventsContainer');
    container.innerHTML = '';
    const events = loadLocal();
    if(!events || events.length===0){
      container.innerHTML = '<p>No hay eventos locales. Pulsa "Sincronizar".</p>';
      return;
    }
    // group by date
    const grouped = {};
    events.forEach(e=>{
      grouped[e.date] = grouped[e.date] || [];
      grouped[e.date].push(e);
    });
    const dates = Object.keys(grouped).sort();
    dates.forEach(d=>{
      const dayDiv = document.createElement('div'); dayDiv.className='day';
      const hd = document.createElement('h3'); hd.textContent = (new Date(d)).toLocaleDateString();
      dayDiv.appendChild(hd);
      grouped[d].forEach(ev=>{
        const evDiv = document.createElement('div'); evDiv.className='event';
        const t = document.createElement('div'); t.className='time'; t.textContent = ev.all_day ? 'Todo el día' : (ev.time || '');
        const title = document.createElement('div'); title.textContent = `${ev.item_name || ''} ${ev.note ? '— ' + ev.note : ''}`;
        evDiv.appendChild(t); evDiv.appendChild(title);
        dayDiv.appendChild(evDiv);
      });
      container.appendChild(dayDiv);
    });
  }

  async function syncFromServer(){
    const apiBase = q('apiUrl').value.trim() || '/api/events';
    const start = mondayOf(new Date());
    const end = new Date(start); end.setDate(start.getDate()+13);
    const url = `${apiBase}?start=${isoDate(start)}&end=${isoDate(end)}`;
    try{
      const res = await fetch(url, {cache:'no-store'});
      if(!res.ok) throw new Error('HTTP '+res.status);
      const j = await res.json();
      if(!j.ok) throw new Error('Response not ok');
      const events = j.events || [];
      saveLocal(events);
      render();
      alert('Sincronización completa. Eventos: '+events.length);
    }catch(err){
      alert('Error sincronizando: '+err.message);
    }
  }

  // init
  document.addEventListener('DOMContentLoaded', ()=>{
    q('apiUrl').value = localStorage.getItem('mobile_api_url') || '/api/events';
    q('sync').addEventListener('click', ()=>{
      localStorage.setItem('mobile_api_url', q('apiUrl').value.trim()||'/api/events');
      if(confirm('Sincronizar reemplazará los eventos locales. Continuar?')){
        syncFromServer();
      }
    });
    q('clearLocal').addEventListener('click', ()=>{ if(confirm('Borrar eventos locales?')){ clearLocal(); } });
    q('saveNote').addEventListener('click', ()=>{ saveNote(q('noteText').value || ''); alert('Nota guardada'); });
    q('clearNote').addEventListener('click', ()=>{ if(confirm('Borrar nota?')) clearNote(); });
    q('noteText').value = loadNote();
    render();
  });
})();
