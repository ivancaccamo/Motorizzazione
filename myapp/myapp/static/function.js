// js/function.js

// Main: dopo che il DOM è pronto
document.addEventListener('DOMContentLoaded', () => {

  // ----- 1) Chart.js Doughnut & Bar Chart (se chartData è definito) -----
  if (typeof chartData !== 'undefined') {
    const draw = (id, type, data, options = {}) => {
      const c = document.getElementById(id);
      if (!c) return;
      new Chart(c.getContext('2d'), { type, data, options });
    };
    draw('chartVeicoli', 'doughnut', {
      labels: ['Con targa attiva','Senza targa attiva'],
      datasets: [{ data: [chartData.veicoliConAttiva, chartData.veicoliSenza], backgroundColor: ['#357ABD','#6c757d'] }]
    });
    draw('chartTarghe', 'doughnut', {
      labels: ['Attive','Restituite'],
      datasets: [{ data: [chartData.attiveTarghe, chartData.restituiteTarghe], backgroundColor: ['#357ABD','#6c757d'] }]
    });
    draw('chartRevisione', 'doughnut', {
      labels: ['Superate','Non superate'],
      datasets: [{ data: [chartData.revSuperate, chartData.revNonSuperate], backgroundColor: ['#357ABD','#6c757d'] }]
    });
    draw('chartMarche', 'bar', {
      labels: chartData.marcheLabels,
      datasets: [{ label: 'Numero veicoli', data: chartData.marcheCounts, backgroundColor: '#357ABD' }]
    }, {
      scales: { y: { beginAtZero: true } }
    });
  }

  // ----- 2) Auto-focus per campi 'telaio[]' e 'targa[]' -----
  window.moveFocus = (el, idx, field) => {
    if (el.value.length === el.maxLength) {
      const nxt = document.getElementsByName(field + '[]')[idx + 1];
      if (nxt) nxt.focus();
    }
  };
  window.moveFocusOnBackspace = (e, idx, field) => {
    const inputs = document.getElementsByName(field + '[]');
    const cur = inputs[idx];
    if (e.key === 'Backspace' && cur.selectionStart === 0 && idx > 0) {
      e.preventDefault();
      const prev = inputs[idx - 1];
      prev.focus();
      prev.setSelectionRange(prev.value.length, prev.value.length);
      prev.value = prev.value.slice(0, -1);
      const hidden = document.getElementById(field === 'telaio' ? 'telaio_hidden' : 'numero_hidden');
      hidden.value = Array.from(inputs).map(c => c.value).join('');
    }
  };

  // ----- 3) Toggle motivazione revisione -----
  const sel = document.getElementById('esito'),
        divMot = document.getElementById('motivazioneDiv'),
        ta = document.getElementById('motivazione');
  if (sel && divMot && ta) {
    const tog = () => {
      if (sel.value === 'Non superata') {
        divMot.style.display = 'block';
        ta.required = true;
      } else {
        divMot.style.display = 'none';
        ta.required = false;
      }
    };
    sel.addEventListener('change', tog);
    tog();
  }

  // ----- 4) Gestione input Telaio dinamico (modifica veicolo) con autofocus -----
  const telaioInputs = document.querySelectorAll('.telaio-input'),
        telaioHidden = document.getElementById('telaio_hidden');
  if (telaioInputs.length && telaioHidden) {
    telaioInputs.forEach((inp, i) => {
      inp.addEventListener('input', () => {
        inp.value = inp.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        telaioHidden.value = Array.from(telaioInputs).map(c => c.value).join('');
        if (inp.value.length === inp.maxLength) {
          const next = telaioInputs[i + 1];
          if (next) next.focus();
        }
      });
      inp.addEventListener('keydown', e => moveFocusOnBackspace(e, i, 'telaio'));
    });
  }

  // ----- 5) Gestione input Targa dinamico (modifica targa) -----
  const targaInputs = document.querySelectorAll('.targa-input'),
        numeroHidden = document.getElementById('numero_hidden');
  if (targaInputs.length && numeroHidden) {
    targaInputs.forEach((inp, i) => {
      inp.addEventListener('input', () => {
        let v = inp.value.toUpperCase();
        if ([0,1,5,6].includes(i)) v = v.replace(/[^ABCDEFGHJKLMNPRSTVWXYZ]/g, '');
        else v = v.replace(/[^0-9]/g, '');
        inp.value = v;
        numeroHidden.value = Array.from(targaInputs).map(c => c.value).join('');
        if (v.length === inp.maxLength) {
          const next = targaInputs[i + 1];
          if (next) next.focus();
        }
      });
      inp.addEventListener('keydown', e => moveFocusOnBackspace(e, i, 'targa'));
    });
  }

  // ----- 6) Ricerca e selezione veicoli (form targa) -----
  if (typeof availableVehicles !== 'undefined') {
    const inpSearch = document.getElementById('veicolo_search'),
          dd = document.getElementById('vehicleDropdown'),
          hid = document.getElementById('veicolo_telaio'),
          clr = document.getElementById('clearSelection');
    let hl = -1;
    const render = list => {
      dd.innerHTML = '';
      if (!list.length) {
        dd.innerHTML = '<div class="no-results">Nessun veicolo trovato</div>';
      } else {
        list.forEach((v, i) => {
          const o = document.createElement('div');
          o.className = 'vehicle-option';
          o.innerHTML = `<div><strong>${v.telaio}</strong></div><div class="vehicle-info">${v.marca} ${v.modello} (${v.dataProd})</div>`;
          o.addEventListener('click', () => {
            inpSearch.value = `${v.telaio} - ${v.marca} ${v.modello}`;
            hid.value = v.telaio;
            inpSearch.classList.add('selected-vehicle');
            dd.style.display = 'none';
            clr.style.display = 'block';
            hl = -1;
          });
          dd.appendChild(o);
        });
      }
      dd.style.display = 'block';
    };
    inpSearch.addEventListener('input', e => {
      clr.style.display = 'none';
      const q = e.target.value.trim().toLowerCase();
      if (!q) return void(dd.style.display = 'none');
      render(availableVehicles.filter(v =>
        v.telaio.toLowerCase().includes(q) || v.marca.toLowerCase().includes(q) || v.modello.toLowerCase().includes(q)
      ));
    });
    inpSearch.addEventListener('keydown', e => {
      const opts = dd.querySelectorAll('.vehicle-option');
      if (!opts.length) return;
      switch (e.key) {
        case 'ArrowDown': e.preventDefault(); hl = Math.min(hl + 1, opts.length - 1); break;
        case 'ArrowUp':   e.preventDefault(); hl = Math.max(hl - 1, 0); break;
        case 'Enter':     e.preventDefault(); if (hl >= 0) opts[hl].click(); break;
        case 'Escape':    dd.style.display = 'none'; hl = -1; break;
      }
      opts.forEach((o, i) => o.classList.toggle('highlighted', i === hl));
      if (hl >= 0) opts[hl].scrollIntoView({ block: 'nearest' });
    });
    clr.addEventListener('click', () => {
      inpSearch.value = '';
      hid.value = '';
      inpSearch.classList.remove('selected-vehicle');
      clr.style.display = 'none';
      dd.style.display = 'none';
      hl = -1;
    });
    document.addEventListener('click', e => {
      if (!inpSearch.contains(e.target) && !dd.contains(e.target)) {
        dd.style.display = 'none'; hl = -1;
      }
    });
  }

  // ----- 7) Modali restituisci/elimina -----
  window.apriDialogRestituisci = (num, de) => {
    document.getElementById('modal-targa-numero').value = num;
    document.getElementById('testo-restituisci').innerHTML = `Vuoi davvero restituire la targa <strong>${num}</strong>`;
    document.getElementById('modal-restituisci').style.display = 'flex';
  };
  window.chiudiDialogRestituisci = () => {
    document.getElementById('modal-restituisci').style.display = 'none';
  };

  let curr = {};
  window.apriDialogDelete = (table, id) => {
    curr = { table, id };
    document.getElementById('modal-table').value = table;
    document.getElementById('modal-id').value = id;
        document.getElementById('testo-restituisci').innerHTML = `Vuoi davvero eliminare ${table}<br><strong>${id} </strong>? `;

    document.getElementById('modal-restituisci').style.display = 'flex';
  };
  window.chiudiDialogDelete = () => {
    document.getElementById('modal-restituisci').style.display = 'none';
  };
  window.confermaDelete = () => {
    const btn = document.getElementById('confirmDelete');
    btn.disabled = true;
    btn.textContent = 'Eliminando...';
    const fd = new FormData();
    fd.append('table', curr.table);
    fd.append('id', curr.id);
    fetch('../operations/delete_handler.php', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(d => { window.chiudiDialogDelete(); alert(d.message); location.reload(); })
      .catch(e => { window.chiudiDialogDelete(); alert('Errore: ' + e.message); });
  };
});

function hideMessageAfterDelay(delay = 4000) {
    const message = document.querySelector('.message');
    if (message) {
        setTimeout(() => {
        	message.style.transition = 'opacity 1.5s ease';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 1500); // Rimuove dopo dissolvenza
        }, delay);
    }
}