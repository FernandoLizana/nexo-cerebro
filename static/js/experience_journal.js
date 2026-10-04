/**
 * Diario de experiencias + rutinas del cuidador.
 */
(function () {
  const listEl = document.getElementById("journal-entries");
  const suggEl = document.getElementById("journal-suggestions");
  const routinesEl = document.getElementById("journal-routines");
  const statsEl = document.getElementById("journal-stats");

  async function fetchJournal() {
    try {
      const r = await fetch("/api/experience/journal");
      return r.json();
    } catch (e) {
      console.warn("journal", e);
      return null;
    }
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function render(data) {
    if (!data) return;
    if (statsEl) {
      const s = data.stats || {};
      statsEl.textContent =
        `Recuerdos ${s.hippocampus_size ?? "—"} · ensambles ${s.virtual_assemblies ?? "—"} · ` +
        `habitación ${s.room ?? "—"}`;
    }
    if (listEl) {
      listEl.innerHTML = "";
      (data.entries || []).slice(0, 12).forEach((e) => {
        const li = document.createElement("li");
        li.className = "journal-item journal-" + (e.kind || "memory");
        li.innerHTML =
          `<span class="journal-kind">${esc(e.kind)}</span> ` +
          `<strong>${esc(e.label)}</strong>` +
          `<span class="muted"> · ${esc(e.detail)}</span>`;
        listEl.appendChild(li);
      });
      if (!(data.entries || []).length) {
        listEl.innerHTML = '<li class="muted">Aún sin episodios registrados — interactúa o espera autonomía.</li>';
      }
    }
    if (suggEl) {
      suggEl.innerHTML = "";
      (data.suggestions || []).forEach((s) => {
        const p = document.createElement("p");
        p.className = "journal-sugg priority-" + (s.priority || "baja");
        p.textContent = s.text;
        suggEl.appendChild(p);
      });
    }
    if (routinesEl) {
      routinesEl.innerHTML = "";
      (data.routines || []).forEach((r) => {
        const card = document.createElement("div");
        card.className = "routine-card";
        const steps = (r.steps || []).map((st) => `<li>${esc(st)}</li>`).join("");
        card.innerHTML =
          `<strong>${esc(r.title)}</strong>` +
          `<ol class="routine-steps">${steps}</ol>` +
          `<button type="button" class="secondary small btn-routine" data-id="${esc(r.id)}">Iniciar</button>`;
        routinesEl.appendChild(card);
      });
      routinesEl.querySelectorAll(".btn-routine").forEach((btn) => {
        btn.addEventListener("click", () => startRoutine(btn.dataset.id, data.routines));
      });
    }
  }

  async function startRoutine(id, routines) {
    const r = (routines || []).find((x) => x.id === id);
    if (!r) return;
    const hint = document.getElementById("interact-hint");
    if (hint) hint.textContent = "Rutina: " + r.title;
    if (r.echo) {
      await fetch("/api/caregiver/routine/echo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: r.echo }),
      });
    }
    if (r.id === "morning_presence" && window.caregiverSensors) {
      await window.caregiverSensors.start();
    }
    if (r.id === "evening_echo") {
      await fetch("/api/time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ realtime: false, hour: 22, minute: 30, paused: false }),
      });
    }
    alert(r.title + "\n\n" + (r.steps || []).join("\n"));
    refresh();
  }

  async function refresh() {
    render(await fetchJournal());
  }

  window.refreshExperienceJournal = refresh;
  const btnRefresh = document.getElementById("btn-journal-refresh");
  if (btnRefresh) btnRefresh.addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 45000);
})();
