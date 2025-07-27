// Quando il DOM è pronto
document.addEventListener('DOMContentLoaded', () => {

  // 1) Grafici (se disponibili dati)
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

  // 2) Gestione input targa (split in più campi)
  const setupTargaInputs = () => {
    let targaInputs = document.querySelectorAll('.targa-input');
    let numeroHidden = document.getElementById('numero_hidden');

    if (!targaInputs.length) {
      targaInputs = document.querySelectorAll('input[name="targa[]"]');
      numeroHidden = document.getElementById('numero_hidden') || document.querySelector('input[name="numero"]');
    }

    if (!targaInputs.length) return;

    const validateTargaInput = (input, index) => {
      let value = input.value.toUpperCase();
      if ([0, 1, 5, 6].includes(index)) {
        value = value.replace(/[^ABCDEFGHJKLMNPRSTVWXYZ]/g, '');
      } else {
        value = value.replace(/[^0-9]/g, '');
      }
      return value;
    };

    const updateHiddenField = () => {
      if (numeroHidden) {
        numeroHidden.value = Array.from(targaInputs).map(input => input.value).join('');
      }
    };

    const moveToNext = (currentIndex) => {
      if (currentIndex < targaInputs.length - 1) {
        targaInputs[currentIndex + 1].focus();
      }
    };

    const handleBackspace = (e, currentIndex) => {
      const currentInput = targaInputs[currentIndex];
      if (e.key === 'Backspace' && currentInput.selectionStart === 0 && currentIndex > 0) {
        e.preventDefault();
        const prevInput = targaInputs[currentIndex - 1];
        prevInput.focus();
        prevInput.setSelectionRange(prevInput.value.length, prevInput.value.length);
        prevInput.value = prevInput.value.slice(0, -1);
        updateHiddenField();
      }
    };

    targaInputs.forEach((input, index) => {
      input.addEventListener('input', () => {
        input.value = validateTargaInput(input, index);
        updateHiddenField();
        if (input.value.length === input.maxLength) {
          moveToNext(index);
        }
      });

      input.addEventListener('keydown', (e) => {
        handleBackspace(e, index);
      });
    });

    updateHiddenField();
  };

  // 3) Gestione input telaio (split in più campi)
  const setupTelaioInputs = () => {
    let telaioInputs = document.querySelectorAll('.telaio-input');
    let telaioHidden = document.getElementById('telaio_hidden');

    if (!telaioInputs.length) {
      telaioInputs = document.querySelectorAll('input[name="telaio[]"]');
      telaioHidden = document.getElementById('telaio_hidden') || document.querySelector('input[name="telaio"]');
    }

    if (!telaioInputs.length) return;

    const validateTelaioInput = (input) => {
      return input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    };

    const updateHiddenField = () => {
      if (telaioHidden) {
        telaioHidden.value = Array.from(telaioInputs).map(input => input.value).join('');
      }
    };

    const moveToNext = (currentIndex) => {
      if (currentIndex < telaioInputs.length - 1) {
        telaioInputs[currentIndex + 1].focus();
      }
    };

    const handleBackspace = (e, currentIndex) => {
      const currentInput = telaioInputs[currentIndex];
      if (e.key === 'Backspace' && currentInput.selectionStart === 0 && currentIndex > 0) {
        e.preventDefault();
        const prevInput = telaioInputs[currentIndex - 1];
        prevInput.focus();
        prevInput.setSelectionRange(prevInput.value.length, prevInput.value.length);
        prevInput.value = prevInput.value.slice(0, -1);
        updateHiddenField();
      }
    };

    telaioInputs.forEach((input, index) => {
      input.addEventListener('input', () => {
        input.value = validateTelaioInput(input);
        updateHiddenField();
        if (input.value.length === input.maxLength) {
          moveToNext(index);
        }
      });

      input.addEventListener('keydown', (e) => {
        handleBackspace(e, index);
      });
    });

    updateHiddenField();
  };

  setupTargaInputs();
  setupTelaioInputs();

  // 4) Mostra/nasconde campo motivazione revisione
  const toggleMotivazione = () => {
    const sel = document.getElementById('esito');
    const divMot = document.getElementById('motivazioneDiv');
    const ta = document.getElementById('motivazione');

    if (sel && divMot && ta) {
      const handleToggle = () => {
        if (sel.value === 'Non superata') {
          divMot.style.display = 'block';
          ta.required = true;
        } else {
          divMot.style.display = 'none';
          ta.required = false;
          ta.value = '';
        }
      };
      sel.addEventListener('change', handleToggle);
      handleToggle();
    }
  };

  toggleMotivazione();

  // 5) Ricerca e selezione veicolo (creazione targa)
  if (typeof availableVehicles !== 'undefined') {
    const inpSearch = document.getElementById('veicolo_search'),
          dd = document.getElementById('vehicleDropdown'),
          hid = document.getElementById('veicolo_telaio'),
          clr = document.getElementById('clearSelection');
    
    if (inpSearch && dd && hid && clr) {
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
          v.telaio.toLowerCase().includes(q) || 
          v.marca.toLowerCase().includes(q) || 
          v.modello.toLowerCase().includes(q)
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
          dd.style.display = 'none';
          hl = -1;
        }
      });
    }
  }

  // 6) Modali di conferma (restituzione / eliminazione)
  window.apriDialogRestituisci = (num, de) => {
    const modalTargaNumero = document.getElementById('modal-targa-numero');
    const testoRestituisci = document.getElementById('testo-restituisci');
    const modalRestituisci = document.getElementById('modal-restituisci');
    
    if (modalTargaNumero && testoRestituisci && modalRestituisci) {
      modalTargaNumero.value = num;
      testoRestituisci.innerHTML = `Vuoi davvero restituire la targa <strong>${num}</strong>`;
      modalRestituisci.style.display = 'flex';
    }
  };

  window.chiudiDialogRestituisci = () => {
    const modalRestituisci = document.getElementById('modal-restituisci');
    if (modalRestituisci) {
      modalRestituisci.style.display = 'none';
    }
  };

  let curr = {};
  window.apriDialogDelete = (table, id) => {
    curr = { table, id };
    const modalTable = document.getElementById('modal-table');
    const modalId = document.getElementById('modal-id');
    const testoRestituisci = document.getElementById('testo-restituisci');
    const modalRestituisci = document.getElementById('modal-restituisci');
    
    if (modalTable && modalId && testoRestituisci && modalRestituisci) {
      modalTable.value = table;
      modalId.value = id;
      testoRestituisci.innerHTML = `Vuoi davvero eliminare ${table}<br><strong>${id}</strong>?`;
      modalRestituisci.style.display = 'flex';
    }
  };

  window.chiudiDialogDelete = () => {
    const modalRestituisci = document.getElementById('modal-restituisci');
    if (modalRestituisci) {
      modalRestituisci.style.display = 'none';
    }
  };

  window.confermaDelete = () => {
    const btn = document.getElementById('confirmDelete');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = 'Eliminando...';
    const fd = new FormData();
    fd.append('table', curr.table);
    fd.append('id', curr.id);

    fetch('../operations/delete_handler.php', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(d => {
        window.chiudiDialogDelete();
        alert(d.message);
        location.reload();
      })
      .catch(e => {
        window.chiudiDialogDelete();
        alert('Errore: ' + e.message);
        btn.disabled = false;
        btn.textContent = 'Conferma';
      });
  };
});

// Nasconde i messaggi flash dopo un tempo
function hideMessageAfterDelay(delay = 4000) {
  const message = document.querySelector('.message');
  if (message) {
    setTimeout(() => {
      message.style.transition = 'opacity 1.5s ease';
      message.style.opacity = '0';
      setTimeout(() => message.remove(), 1500);
    }, delay);
  }
}
