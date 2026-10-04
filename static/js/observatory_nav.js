/**
 * Observatory section nav + inspectors fed by real APIs.
 * Uses textContent only for untrusted / API text.
 */
(function () {
  "use strict";

  const SECTIONS = [
    "observatorio",
    "constelacion",
    "memoria",
    "laboratorio",
    "conexiones",
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function clearEl(el) {
    if (!el) return;
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text == null ? "" : String(text);
  }

  function appendLine(parent, text, className) {
    const p = document.createElement("p");
    if (className) p.className = className;
    p.textContent = text;
    parent.appendChild(p);
    return p;
  }

  function setBadge(key, label, kind) {
    const nodes = document.querySelectorAll('[data-badge-for="' + key + '"]');
    nodes.forEach(function (el) {
      el.textContent = label;
      el.classList.remove("badge-real", "badge-empty", "badge-demo", "badge-unavailable");
      if (kind) el.classList.add("badge-" + kind);
    });
  }

  function sourceKind(data) {
    if (!data) return "unavailable";
    if (data.demo) return "demo";
    const src = data.source || "";
    if (src === "empty" || data.available === false) {
      if (src === "unavailable") return "unavailable";
      return "empty";
    }
    return "real";
  }

  function sourceLabel(data) {
    const kind = sourceKind(data);
    if (kind === "demo") return "DEMO";
    if (kind === "empty") return "sin datos · real";
    if (kind === "unavailable") return "no disponible";
    return "datos reales";
  }

  async function fetchJson(path) {
    const res = await fetch(path, { headers: { Accept: "application/json" } });
    const data = await res.json().catch(function () {
      return null;
    });
    if (!res.ok) {
      return { error: true, status: res.status, source: "unavailable", available: false };
    }
    return data;
  }

  function showSection(name) {
    if (SECTIONS.indexOf(name) < 0) name = "observatorio";
    document.querySelectorAll(".obs-section").forEach(function (sec) {
      const match = sec.getAttribute("data-section") === name;
      sec.classList.toggle("is-active", match);
      if (match) {
        sec.removeAttribute("hidden");
      } else {
        sec.setAttribute("hidden", "");
      }
    });
    document.querySelectorAll(".obs-nav-btn").forEach(function (btn) {
      const on = btn.getAttribute("data-section") === name;
      btn.classList.toggle("is-active", on);
      if (on) btn.setAttribute("aria-current", "page");
      else btn.removeAttribute("aria-current");
    });
    document.querySelectorAll(".obs-section-shared").forEach(function (el) {
      const showIn = (el.getAttribute("data-show-in") || "").split(/\s+/);
      const visible = showIn.indexOf(name) >= 0;
      el.classList.toggle("is-hidden-section", !visible);
      el.hidden = !visible;
    });
    try {
      history.replaceState(null, "", "#" + name);
    } catch (_) {}
    loadInspectors(name);
  }

  function renderPersonalities(data) {
    const el = $("insp-personalities");
    clearEl(el);
    setBadge("personalities", sourceLabel(data), sourceKind(data));
    if (!data || data.error) {
      appendLine(el, "No se pudo cargar brain.personality_archetypes.", "muted");
      return;
    }
    appendLine(el, "Fuente: " + (data.source || "—"), "muted");
    if (data.note) appendLine(el, data.note, "muted");
    const nexus = data.nexus || {};
    const nira = data.nira || {};
    appendLine(
      el,
      "Nexus · " + (nexus.role || "—") + " · aprendizaje " + (nexus.learning || "—")
    );
    appendLine(
      el,
      "Nira · " + (nira.role || "—") + " · aprendizaje " + (nira.learning || "—")
    );
    const presets = data.presets || [];
    appendLine(el, "Presets de arquetipo: " + presets.length, "muted");
    presets.slice(0, 4).forEach(function (p) {
      appendLine(
        el,
        (p.sign || "?") + " — " + (p.tendency || "") + " / tensión: " + (p.tension || "")
      );
    });
    if (presets.length > 4) {
      appendLine(el, "… +" + (presets.length - 4) + " más (ver API)", "muted");
    }
  }

  function renderRelationships(data) {
    const el = $("insp-relationships");
    clearEl(el);
    setBadge("relationships", sourceLabel(data), sourceKind(data));
    if (!data || data.error) {
      appendLine(el, "Error al consultar /api/relationships.", "muted");
      return;
    }
    if (!data.available || !data.snapshot) {
      appendLine(el, data.note || "Sin RelationshipModel en el cerebro.", "muted");
      appendLine(el, "friendship_score: null (por diseño)", "muted");
      return;
    }
    const s = data.snapshot;
    appendLine(el, "Afinidad: " + s.affinity);
    appendLine(el, "Reciprocidad: " + s.reciprocity);
    appendLine(el, "Desacuerdos pendientes: " + (s.pending_disagreements || []).length);
    appendLine(el, "friendship_score: " + String(s.friendship_score), "muted");
  }

  function renderAutonomy(data) {
    const el = $("insp-autonomy");
    clearEl(el);
    setBadge("autonomy", sourceLabel(data), sourceKind(data));
    if (!data || data.error) {
      appendLine(el, "Error al consultar decisiones.", "muted");
      return;
    }
    appendLine(el, "Política: " + (data.policy_version || "—"), "muted");
    const list = data.decisions || [];
    if (!list.length) {
      appendLine(el, "Aún no hay decisiones registradas.", "muted");
      return;
    }
    list.slice(0, 8).forEach(function (d) {
      appendLine(
        el,
        (d.character || "?") +
          " → " +
          (d.choice || d.character_choice || "?") +
          " · " +
          String(d.proposal || "").slice(0, 80)
      );
    });
  }

  function renderDyad(data) {
    const el = $("insp-dyad");
    clearEl(el);
    setBadge("dyad", sourceLabel(data), sourceKind(data));
    if (!data || data.error) {
      appendLine(el, "Error al consultar aprendizaje diádico.", "muted");
      return;
    }
    if (!data.available) {
      appendLine(el, "Sin asociaciones aún (espera un ciclo de sueño o aprendizaje).", "muted");
      return;
    }
    const dyad = data.dyad_learning || {};
    appendLine(
      el,
      "Nira receptiva: " +
        String(dyad.nira_receptive) +
        " · promovido: " +
        String(dyad.promoted) +
        " · asociaciones: " +
        String(dyad.associations != null ? dyad.associations : (data.nira_associations || []).length)
    );
    (data.nira_associations || []).slice(0, 6).forEach(function (a) {
      appendLine(
        el,
        "[" + (a.kind || "?") + "] " + String(a.content || "").slice(0, 100)
      );
    });
    (data.nexus_recent || []).slice(0, 4).forEach(function (a) {
      appendLine(
        el,
        "Nexus [" + (a.kind || "?") + "] " + String(a.content || "").slice(0, 100)
      );
    });
  }

  function renderHub(data) {
    const el = $("insp-hub");
    clearEl(el);
    setBadge("hub", sourceLabel(data), sourceKind(data));
    if (!data || data.error) {
      appendLine(el, "Error al consultar el hub.", "muted");
      return;
    }
    if (!data.available || !data.hub) {
      appendLine(el, data.note || "Hub no alcanzable en 127.0.0.1:8770.", "muted");
      return;
    }
    const h = data.hub;
    appendLine(el, (h.name || "hub") + " · " + (h.mood || "—") + " · tick " + String(h.tick));
    appendLine(el, "Capacidad reportada: " + String(h.capacity), "muted");
    const links = h.links || {};
    const keys = Object.keys(links);
    if (!keys.length) {
      appendLine(el, "Sin entradas de links en el hub.", "muted");
    } else {
      keys.forEach(function (k) {
        const L = links[k] || {};
        appendLine(
          el,
          k + ": " + (L.online ? "en línea" : "fuera") + (L.last ? " · last " + L.last : "")
        );
      });
    }
    const conns = h.connections || [];
    appendLine(el, "Conexiones con fuerza > 0: " + conns.length, "muted");
  }

  function renderCollective(data) {
    const el = $("insp-collective");
    clearEl(el);
    const kind = data && !data.error ? "real" : "unavailable";
    setBadge("collective", data && !data.error ? "datos reales" : "no disponible", kind);
    if (!data || data.error) {
      appendLine(el, "Error al consultar /api/collective.", "muted");
      return;
    }
    appendLine(
      el,
      "WM: " + String(data.wm) + " · hipocampo: " + String(data.hippocampus) + " · links: " + String(data.links)
    );
    appendLine(el, "Métrica: " + (data.metric || "—") + " (no connectome)", "muted");
    const q = data.quarantine || {};
    appendLine(
      el,
      "Cuarentena: " +
        (q.quarantined ? "sí" : "no") +
        " · validado: " +
        (q.validated ? "sí" : "no") +
        (q.last_source ? " · fuente " + q.last_source : "")
    );
    if (q.last_phrase) {
      appendLine(el, "Última frase: " + String(q.last_phrase).slice(0, 120), "muted");
    }
  }

  const cache = {};

  async function loadInspectors(section) {
    if (section === "constelacion") {
      if (!cache.personalities) cache.personalities = fetchJson("/api/personalities");
      if (!cache.relationships) cache.relationships = fetchJson("/api/relationships");
      if (!cache.autonomy) cache.autonomy = fetchJson("/api/autonomy/decisions");
      renderPersonalities(await cache.personalities);
      renderRelationships(await cache.relationships);
      renderAutonomy(await cache.autonomy);
    }
    if (section === "memoria") {
      if (!cache.dyad) cache.dyad = fetchJson("/api/dyad/learning");
      renderDyad(await cache.dyad);
    }
    if (section === "conexiones") {
      // Always refresh hub/collective — availability can change.
      cache.hub = fetchJson("/api/connections/hub");
      cache.collective = fetchJson("/api/collective");
      renderHub(await cache.hub);
      renderCollective(await cache.collective);
    }
  }

  function bindNav() {
    const nav = $("obs-nav");
    if (!nav) return;
    nav.addEventListener("click", function (ev) {
      const btn = ev.target.closest(".obs-nav-btn");
      if (!btn) return;
      showSection(btn.getAttribute("data-section"));
    });
    nav.addEventListener("keydown", function (ev) {
      const buttons = Array.prototype.slice.call(nav.querySelectorAll(".obs-nav-btn"));
      const i = buttons.indexOf(document.activeElement);
      if (i < 0) return;
      let next = i;
      if (ev.key === "ArrowRight" || ev.key === "ArrowDown") next = (i + 1) % buttons.length;
      else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") next = (i - 1 + buttons.length) % buttons.length;
      else if (ev.key === "Home") next = 0;
      else if (ev.key === "End") next = buttons.length - 1;
      else return;
      ev.preventDefault();
      buttons[next].focus();
      showSection(buttons[next].getAttribute("data-section"));
    });
  }

  function boot() {
    bindNav();
    const hash = (location.hash || "").replace(/^#/, "");
    showSection(SECTIONS.indexOf(hash) >= 0 ? hash : "observatorio");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
