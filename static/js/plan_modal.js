// provide a minimal shim so other inline scripts can call these APIs
window.planModal = window.planModal || {
  openModal: function(){},
  closeModal: function(){},
  wireInjectedContent: function(){},
  wireToggleButtons: function(){},
  updateModalVisibility: function(){}
};

document.addEventListener('DOMContentLoaded', function(){
  const backdrop = document.getElementById('plan-modal-backdrop');
  if(!backdrop) return; // nothing to do if modal not present
  const form = document.getElementById('plan-modal-form');
  const title = document.getElementById('plan-modal-title');
  const contextEl = document.getElementById('plan-modal-context');
  const submitBtn = document.getElementById('submit-plan-modal');
  const kindSelect = document.getElementById('modal-kind');
  const kindRow = document.getElementById('modal-kind-row');
  const allDayInput = document.getElementById('modal-all-day');
  const timeInput = document.getElementById('modal-time');

  function getBlock(name){ return document.querySelector('.modal-plan-' + name); }

  function resetModalForm(){
    form.reset();
    form.action = '';
    document.getElementById('modal-plan-item-id').value = '';
    document.getElementById('modal-update-plan-id').value = '';
    document.getElementById('modal-selected-item-id').value = '';
    // remove any transient hidden inputs used by special modes (e.g. edit-occurrence)
    const oldType = form.querySelector('input[name="type"]'); if(oldType) oldType.remove();
    const oldTime = form.querySelector('input[name="time"]'); if(oldTime) oldTime.remove();
    ['date','end','time','note','month-day'].forEach(function(id){ const el = document.getElementById('modal-' + id); if(el) el.value = ''; });
    ['weekly-interval','monthly-interval'].forEach(function(id){ const el = document.getElementById('modal-' + id); if(el) el.value = '1'; });
    const daily = document.getElementById('modal-daily-weekdays'); if(daily) daily.value = 'all';
    const weekly = document.getElementById('modal-weekly-weekdays'); if(weekly) weekly.value = 'Lunes';
    if(kindSelect) kindSelect.value = 'once';
    if(allDayInput) allDayInput.checked = false;
    submitBtn.style.background = '';
    submitBtn.style.color = '';
    setReadOnly(false);
    const errEl = document.getElementById('plan-modal-error'); if(errEl){ errEl.style.display='none'; errEl.textContent=''; }
    updateModalVisibility();
  }

  function setReadOnly(readOnly){
    form.querySelectorAll('input, select').forEach(function(el){
      if(el.type === 'hidden') return;
      if(['modal-all-day','modal-kind','modal-date','modal-end','modal-time','modal-note','modal-month-day','modal-weekly-interval','modal-monthly-interval'].includes(el.id)){
        el.disabled = readOnly;
      }
    });
  }

  function updateModalVisibility(){
    const kind = kindSelect.value;
    ['once','daily','weekly','monthly'].forEach(function(name){ const block = getBlock(name); if(block) block.style.display = (name===kind)?'block':'none'; });
    const dateInput = document.getElementById('modal-date');
    const endInput = document.getElementById('modal-end');
    const dailyWeekdays = document.getElementById('modal-daily-weekdays');
    const weeklyInterval = document.getElementById('modal-weekly-interval');
    const weeklyWeekday = document.getElementById('modal-weekly-weekdays');
    const monthlyInterval = document.getElementById('modal-monthly-interval');
    const monthDay = document.getElementById('modal-month-day');
    const readOnly = submitBtn.dataset.mode === 'delete';
    if(dateInput) dateInput.disabled = kind !== 'once' || readOnly;
    if(endInput) endInput.disabled = kind !== 'once' || readOnly;
    if(dailyWeekdays) dailyWeekdays.disabled = kind !== 'daily' || readOnly;
    if(weeklyInterval) weeklyInterval.disabled = kind !== 'weekly' || readOnly;
    if(weeklyWeekday) weeklyWeekday.disabled = kind !== 'weekly' || readOnly;
    if(monthlyInterval) monthlyInterval.disabled = kind !== 'monthly' || readOnly;
    if(monthDay) monthDay.disabled = kind !== 'monthly' || readOnly;
    if(dateInput) dateInput.required = false;
    if(weeklyInterval) weeklyInterval.required = false;
    if(weeklyWeekday) weeklyWeekday.required = false;
    if(monthlyInterval) monthlyInterval.required = false;
    if(monthDay) monthDay.required = false;
    if(timeInput) { timeInput.required = false; if(!readOnly) timeInput.disabled = false; }
    if(kind === 'once' && dateInput) dateInput.required = true;
    if(kind === 'weekly'){ if(weeklyInterval) weeklyInterval.required = true; if(weeklyWeekday) weeklyWeekday.required = true; }
    if(kind === 'monthly'){ if(monthlyInterval) monthlyInterval.required = true; if(monthDay) monthDay.required = true; }
    if(!readOnly){ if(allDayInput && allDayInput.checked){ if(timeInput) { timeInput.disabled = true; timeInput.required = false; } } }
  }

  function openModal(mode, data){
    resetModalForm();
    data = data || {};
    submitBtn.dataset.mode = mode;
    document.getElementById('modal-selected-item-id').value = data.itemId || '';
    document.getElementById('modal-plan-item-id').value = data.itemId || '';
    if(mode === 'add'){
      title.textContent = 'Añadir planificación';
      contextEl.textContent = data.itemName ? ('Item: ' + data.itemName) : '';
      submitBtn.textContent = 'Añadir planificación';
      // set action to project endpoint if provided
      if(data.projectId) form.action = '/project/' + data.projectId + '/';
    }
    if(mode === 'edit-occurrence'){
      title.textContent = 'Editar ocurrencia';
      contextEl.textContent = data.itemName ? ('Item: ' + data.itemName + ' — editando sólo esta ocurrencia') : 'Editar ocurrencia';
      // behave like a one-off plan
      kindSelect.value = 'once';
      kindSelect.disabled = true;
      // ensure disabled select value is submitted by creating a hidden input
      let hkind = form.querySelector('input[name="kind"]');
      if(!hkind){ hkind = document.createElement('input'); hkind.type = 'hidden'; hkind.name = 'kind'; form.appendChild(hkind); }
      hkind.value = kindSelect.value;
      document.getElementById('modal-date').value = data.date || '';
      document.getElementById('modal-time').value = data.time || '';
      document.getElementById('modal-note').value = data.note || '';
      document.getElementById('modal-plan-item-id').value = data.itemId || '';
      if(data.planId){ 
        if(data.exceptionId){
          // editing an existing exception
          form.action = '/exception/' + data.exceptionId + '/edit';
        } else {
          form.action = '/plan/' + data.planId + '/exception';
        }
      }
      // ensure hidden inputs
      let typ = form.querySelector('input[name="type"]');
      if(!typ){ typ = document.createElement('input'); typ.type = 'hidden'; typ.name = 'type'; typ.value = 'edit'; form.appendChild(typ); } else { typ.value = 'edit'; }
      let htime = form.querySelector('input[name="time"]');
      if(!htime){ htime = document.createElement('input'); htime.type = 'hidden'; htime.name = 'time'; htime.value = document.getElementById('modal-time').value || ''; form.appendChild(htime); } else { htime.value = document.getElementById('modal-time').value || ''; }
      // store original occurrence date/time so server can create a cancel if date/time changed
      let origDate = form.querySelector('input[name="original_date"]');
      if(!origDate){ origDate = document.createElement('input'); origDate.type = 'hidden'; origDate.name = 'original_date'; origDate.value = data.date || ''; form.appendChild(origDate); } else { origDate.value = data.date || ''; }
      let origTime = form.querySelector('input[name="original_time"]');
      if(!origTime){ origTime = document.createElement('input'); origTime.type = 'hidden'; origTime.name = 'original_time'; origTime.value = data.time || ''; form.appendChild(origTime); } else { origTime.value = data.time || ''; }
      submitBtn.textContent = 'Guardar cambios';
    }
    if(mode === 'edit' || mode === 'delete'){
      title.textContent = mode === 'edit' ? 'Modificar planificación' : 'Eliminar planificación';
      contextEl.textContent = data.itemName ? ('Item: ' + data.itemName) : '';
      document.getElementById('modal-update-plan-id').value = data.planId || '';
      if(data.kind) kindSelect.value = data.kind;
      document.getElementById('modal-date').value = data.date || '';
      document.getElementById('modal-end').value = data.end || '';
      document.getElementById('modal-time').value = data.time || '';
      document.getElementById('modal-note').value = data.note || '';
      document.getElementById('modal-month-day').value = data.monthDay || '';
      document.getElementById('modal-weekly-interval').value = data.interval || '1';
      document.getElementById('modal-monthly-interval').value = data.interval || '1';
      if(['all','weekdays','weekend'].includes((data.weekdays||'').toString())){
        const d = document.getElementById('modal-daily-weekdays'); if(d) d.value = data.weekdays;
      }
      if(data.weekdays && !['all','weekdays','weekend'].includes((data.weekdays||'').toString())){
        const w = document.getElementById('modal-weekly-weekdays'); if(w) w.value = data.weekdays;
      }
      const completedBox = document.getElementById('modal-completed'); if(completedBox) completedBox.checked = (data.completed === '1');
      // set all-day flag from dataset so validation and UI match the plan
      if(allDayInput) allDayInput.checked = (data.allDay === '1');
      // set action: if projectId present use project endpoint, else default to plan delete for delete mode
      if(mode === 'edit'){
        if(data.projectId) form.action = '/project/' + data.projectId + '/';
        submitBtn.textContent = 'Guardar cambios';
        // user requested: cannot change `kind` on edit
        kindSelect.disabled = true;
        // create hidden field so value is posted (disabled selects are not submitted)
        let hkind2 = form.querySelector('input[name="kind"]');
        if(!hkind2){ hkind2 = document.createElement('input'); hkind2.type = 'hidden'; hkind2.name = 'kind'; form.appendChild(hkind2); }
        hkind2.value = kindSelect.value;
      }
      if(mode === 'delete'){
        form.action = '/plan/' + (data.planId || '') + '/delete';
        submitBtn.textContent = 'Eliminar planificación';
        submitBtn.style.background = '#a40000';
        submitBtn.style.color = '#fff';
        setReadOnly(true);
      }
    }
    if(mode !== 'edit'){
      kindSelect.disabled = false;
      const h = form.querySelector('input[name="kind"]'); if(h) h.remove();
    } else {
      // if kind field was previously hidden for edit mode, keep it in sync
      const h = form.querySelector('input[name="kind"]'); if(h) h.value = kindSelect.value;
    }
    // hide or show kind row depending on origin (calendar vs project)
    if(data.source === 'calendar'){
      if(kindRow) kindRow.style.display = 'none';
      // ensure a hidden 'kind' input exists so value is posted when select is hidden/disabled
      let h = form.querySelector('input[name="kind"]');
      if(!h){ h = document.createElement('input'); h.type = 'hidden'; h.name = 'kind'; form.appendChild(h); }
      h.value = kindSelect.value || 'once';
      kindSelect.disabled = true;
    } else {
      if(kindRow) kindRow.style.display = '';
      // if not in edit mode, remove any leftover hidden kind input created by calendar hiding
      if(submitBtn.dataset.mode !== 'edit'){
        const hk = form.querySelector('input[name="kind"]'); if(hk) hk.remove();
        kindSelect.disabled = false;
      }
    }
    // if opened from exceptions modal, raise z-index so this modal appears above
    if(data.source === 'exceptions'){
      backdrop.style.zIndex = '1202';
    } else {
      backdrop.style.zIndex = '1000';
    }
    // ensure visibility and time disabling respects the all-day flag
    updateModalVisibility();
    updateModalVisibility();
    backdrop.style.display = 'block';
  }

  function closeModal(){ backdrop.style.display = 'none'; }

  function wireInjectedContent(){
    document.querySelectorAll('.open-plan-modal').forEach(function(btn){
      if(btn._wired) return;
      btn.addEventListener('click', function(e){
        e.preventDefault();
        const d = btn.dataset || {};
        openModal(btn.dataset.mode, {
          planId: d.planId || '',
          itemId: d.itemId || '',
          itemName: d.itemName || '',
          kind: d.kind || 'once',
          source: d.source || '',
          date: d.date || '',
          end: d.end || '',
          time: d.time || '',
          interval: d.interval || '1',
          weekdays: d.weekdays || '',
          monthDay: d.monthDay || '',
          note: d.note || '',
          allDay: d.allDay || '0',
          completed: d.completed || '0',
          projectId: d.projectId || ''
        });
      });
      btn._wired = true;
    });
  }

  function wireToggleButtons(){
    document.querySelectorAll('.plan-toggle-btn').forEach(function(b){
      if(b._wiredToggle) return;
      b.addEventListener('click', function(){
        const pid = b.dataset.planId;
        if(!pid) return;
        fetch('/plan/' + pid + '/toggle_completed', {method:'POST', headers:{'X-Requested-With':'XMLHttpRequest'}})
          .then(function(){ location.reload(); })
          .catch(function(){ location.reload(); });
      });
      b._wiredToggle = true;
    });
  }

  document.getElementById('close-plan-modal').addEventListener('click', closeModal);
  document.getElementById('cancel-plan-modal').addEventListener('click', closeModal);
  // Only close modal when the click both starts and ends on the backdrop.
  // This avoids closing the modal when the user selects text and releases
  // the mouse outside the modal.
  let backdropMouseDown = false;
  backdrop.addEventListener('mousedown', function(e){ if(e.target === backdrop) backdropMouseDown = true; else backdropMouseDown = false; });
  backdrop.addEventListener('click', function(e){
    if(e.target === backdrop && backdropMouseDown){
      closeModal();
    }
    backdropMouseDown = false;
  });
  // ensure flag is cleared on any mouseup elsewhere
  document.addEventListener('mouseup', function(){ backdropMouseDown = false; });

  kindSelect.addEventListener('change', updateModalVisibility);
  allDayInput.addEventListener('change', updateModalVisibility);

  // initial wiring
  wireInjectedContent();
  wireToggleButtons();
  // handle submit via AJAX for add/edit to surface modal errors
  form.addEventListener('submit', function(e){
    // allow normal submit for delete mode
    if(submitBtn.dataset.mode === 'delete') return;
    e.preventDefault();
    const action = form.action || window.location.pathname;
    // if submitting to an exception endpoint, ensure hidden 'time' is up-to-date
    if(action && (action.match(/\/plan\/\d+\/exception$/) || action.match(/\/exception\/\d+\/edit$/))){
      const htime = form.querySelector('input[name="time"]');
      if(htime) htime.value = (document.getElementById('modal-time').value || '');
      // ensure hidden 'type' is present (edit or cancel)
      const htype = form.querySelector('input[name="type"]');
      if(!htype){ const t = document.createElement('input'); t.type='hidden'; t.name='type'; t.value='edit'; form.appendChild(t); }
    }
    const fd = new FormData(form);
    fetch(action, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' }, body: fd })
      .then(function(resp){ return resp.json().catch(function(){ return { ok: false, error: 'Respuesta inválida del servidor' }; }); })
      .then(function(js){
        const errEl = document.getElementById('plan-modal-error');
        if(!js) return;
        if(js.ok){
          if(js.redirect){ window.location.href = js.redirect; return; }
          // if modal was opened from exceptions management, return to the project page and reopen exceptions
          if(form.dataset && form.dataset.returnToExceptionsFor){
            const parent = form.dataset.returnToExceptionsFor;
            const itemId = document.getElementById('modal-plan-item-id').value || '';
            const url = window.location.pathname + (itemId?('?selected_item=' + encodeURIComponent(itemId) + '&open_exceptions_for=' + encodeURIComponent(parent)) : ('?open_exceptions_for=' + encodeURIComponent(parent)));
            window.location.href = url;
            return;
          }
          window.location.reload();
        } else {
          if(errEl){ errEl.textContent = js.error || 'Error en el formulario'; errEl.style.display = 'block'; }
        }
      }).catch(function(){
        const errEl = document.getElementById('plan-modal-error');
        if(errEl){ errEl.textContent = 'Error de red. Inténtalo de nuevo.'; errEl.style.display = 'block'; }
      });
  });
  // expose for other scripts
  window.planModal = { openModal: openModal, closeModal: closeModal, wireInjectedContent: wireInjectedContent, wireToggleButtons: wireToggleButtons, updateModalVisibility: updateModalVisibility };
});
