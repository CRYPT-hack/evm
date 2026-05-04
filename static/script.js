/* script.js — Electronic Voting System Frontend Logic */

/* ─── Flash message dismissal ─────────────────────────────────────────────── */
document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.flash').style.display = 'none';
    });
});

/* Auto-dismiss flash messages after 5 seconds */
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
        el.style.transition = 'opacity .5s';
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 500);
    }, 5000);
});


/* ─── Candidate card selection ────────────────────────────────────────────── */
document.querySelectorAll('.candidate-card').forEach(card => {
    card.addEventListener('click', () => {
        /* Deselect all */
        document.querySelectorAll('.candidate-card').forEach(c => c.classList.remove('selected'));
        /* Select clicked */
        card.classList.add('selected');
        const radio = card.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
    });
});


/* ─── Animate vote bars on results/report pages ───────────────────────────── */
function animateBars() {
    document.querySelectorAll('.vote-bar-fill[data-pct]').forEach(bar => {
        const pct = parseFloat(bar.dataset.pct) || 0;
        setTimeout(() => { bar.style.width = pct + '%'; }, 100);
    });
}
if (document.querySelector('.vote-bar-fill')) {
    window.addEventListener('load', animateBars);
}


/* ─── Confirm before reset ────────────────────────────────────────────────── */
const resetForm = document.getElementById('reset-form');
if (resetForm) {
    resetForm.addEventListener('submit', e => {
        if (!confirm('Reset all votes? This cannot be undone.')) {
            e.preventDefault();
        }
    });
}


/* ─── Simulation runner ───────────────────────────────────────────────────── */
const simBtn    = document.getElementById('sim-btn');
const simOutput = document.getElementById('sim-output');

if (simBtn) {
    simBtn.addEventListener('click', async () => {
        simBtn.disabled = true;
        simBtn.innerHTML = '<span class="spinner"></span> Running Simulation…';
        if (simOutput) simOutput.style.display = 'none';

        try {
            const res  = await fetch('/run_simulation', { method: 'POST' });
            const data = await res.json();

            if (!data.success) throw new Error('Simulation failed');

            renderSimulation(data);
            simOutput.style.display = 'block';
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            simBtn.disabled = false;
            simBtn.innerHTML = '▶ Run Random Election Simulation';
        }
    });
}

function renderSimulation(data) {
    /* Summary stats */
    document.getElementById('sim-cast')       && (document.getElementById('sim-cast').textContent       = data.total_votes);
    document.getElementById('sim-registered') && (document.getElementById('sim-registered').textContent = data.total_registered);
    document.getElementById('sim-turnout')    && (document.getElementById('sim-turnout').textContent    =
        ((data.total_votes / data.total_registered) * 100).toFixed(1) + '%');

    /* Verification status */
    const verStatus = document.getElementById('sim-ver-status');
    if (verStatus) {
        const ok = data.verifier?.ALL_CHECKS === 'PASS';
        verStatus.textContent  = ok ? '✔ All Checks Passed' : '✖ Verification Failed';
        verStatus.className    = 'badge ' + (ok ? 'badge-green' : 'badge-red');
    }

    /* Candidate bars */
    const barsEl = document.getElementById('sim-bars');
    if (!barsEl || !data.results) return;

    const maxVotes = Math.max(...data.results.map(r => r.votes), 1);
    barsEl.innerHTML = '';

    data.results.forEach((r, i) => {
        const pct   = ((r.votes / maxVotes) * 100).toFixed(1);
        const color = r.color || '#2563EB';
        barsEl.innerHTML += `
          <div style="margin-bottom:14px">
            <div style="display:flex;justify-content:space-between;font-size:.88rem;font-weight:600;margin-bottom:4px">
              <span>${i === 0 ? '🏆 ' : ''}${r.name} (${r.symbol})</span>
              <span style="color:var(--primary)">${r.votes} votes</span>
            </div>
            <div class="sim-bar">
              <div class="sim-bar-fill" style="width:0%;background:${color}" data-pct="${pct}"></div>
            </div>
          </div>`;
    });

    /* Animate bars */
    setTimeout(() => {
        barsEl.querySelectorAll('.sim-bar-fill[data-pct]').forEach(bar => {
            bar.style.width = bar.dataset.pct + '%';
        });
    }, 100);

    /* Winner */
    const winEl = document.getElementById('sim-winner');
    if (winEl) {
        const top = data.results[0];
        const tie = data.verifier?.IS_TIE === 'YES';
        winEl.textContent = tie ? '⚖ Result: Tie' : `🏆 Winner: ${top?.name || 'N/A'}`;
    }
}


/* ─── Verification page: show check detail on hover ──────────────────────── */
document.querySelectorAll('.check-row').forEach(row => {
    row.addEventListener('mouseenter', () => row.style.transform = 'translateX(4px)');
    row.addEventListener('mouseleave', () => row.style.transform = '');
});
