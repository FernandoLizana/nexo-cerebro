/**
 * Cámara + micrófono del cuidador → Nexo (visión periférica + conversación).
 * Voz celeste: audio espacial desde el cielo (SkyVoice).
 */
(function () {
  const statusEl = document.getElementById("caregiver-status");
  const preview = document.getElementById("caregiver-preview");
  const btnToggle = document.getElementById("btn-caregiver-toggle");
  const btnSpeak = document.getElementById("btn-caregiver-speak-now");
  const transcriptEl = document.getElementById("caregiver-transcript");
  const skyVoiceToggle = document.getElementById("chk-sky-voice");

  let stream = null;
  let recognition = null;
  let visionTimer = null;
  let active = false;
  let captureCanvas = null;
  let utterancePending = false;

  function setStatus(msg, ok) {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.classList.toggle("caregiver-ok", !!ok);
    statusEl.classList.toggle("caregiver-err", ok === false);
  }

  function skyVoiceOn() {
    if (skyVoiceToggle) return skyVoiceToggle.checked;
    return true;
  }

  async function postJson(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    return r.json();
  }

  function captureFrame() {
    if (!preview || !stream || preview.readyState < 2) return null;
    if (!captureCanvas) {
      captureCanvas = document.createElement("canvas");
    }
    const w = Math.min(320, preview.videoWidth || 320);
    const h = Math.min(240, preview.videoHeight || 240);
    if (w < 8 || h < 8) return null;
    captureCanvas.width = w;
    captureCanvas.height = h;
    const ctx = captureCanvas.getContext("2d");
    ctx.drawImage(preview, 0, 0, w, h);
    return captureCanvas.toDataURL("image/jpeg", 0.72);
  }

  async function sendVisionFrame() {
    const b64 = captureFrame();
    if (!b64) return;
    try {
      const j = await postJson("/api/caregiver/vision", { image_b64: b64 });
      if (j.gist) setStatus("👁 " + j.gist, true);
    } catch (e) {
      console.warn("vision", e);
    }
  }

  function speakNexo(text) {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "es-ES";
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  }

  async function sendSpeech(text, opts) {
    const t = (text || "").trim();
    if (!t) return;
    const fromSky = opts && opts.voiceFromSky;
    if (transcriptEl) {
      transcriptEl.textContent = (fromSky ? "☁ Tú (cielo): " : "Tú: ") + t;
    }
    setStatus(fromSky ? "☁ voz celeste…" : "🎤 enviando…", true);
    try {
      const j = await postJson("/api/caregiver/speak", {
        text: t,
        voice_from_sky: !!fromSky,
      });
      const reply = j.reply || (j.character && j.character.message) || "";
      if (reply) {
        if (transcriptEl) {
          transcriptEl.textContent =
            (fromSky ? "☁ Tú: " : "Tú: ") + t + " · Nexo: " + reply;
        }
        if (typeof window.showNexoBubble === "function") {
          window.showNexoBubble(reply);
        }
        speakNexo(reply);
      }
      if (typeof window.updateHud === "function") {
        window.updateHud(j);
      } else if (typeof window.refreshWorldTick === "function") {
        await window.refreshWorldTick();
      }
      setStatus(fromSky ? "☁ Nexo oyó la voz del cielo" : "🎤 Nexo respondió", true);
    } catch (e) {
      setStatus("Error al hablar con Nexo", false);
      console.warn(e);
    }
  }

  function setupRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setStatus("Micrófono: escribe en el chat o usa Chrome/Edge para voz", null);
      return null;
    }
    const rec = new SR();
    rec.lang = "es-ES";
    rec.continuous = true;
    rec.interimResults = true;

    rec.onspeechstart = () => {
      if (skyVoiceOn() && window.SkyVoice) {
        utterancePending = true;
        window.SkyVoice.beginUtterance();
      }
    };

    rec.onresult = async (ev) => {
      let interim = "";
      let final = "";
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const r = ev.results[i];
        if (r.isFinal) final += r[0].transcript;
        else interim += r[0].transcript;
      }
      if (transcriptEl && (interim || final)) {
        const prefix = skyVoiceOn() ? "☁ " : "";
        transcriptEl.textContent = prefix + (final || interim).trim();
      }
      if (final.trim()) {
        const text = final.trim();
        const fromSky = skyVoiceOn();
        if (fromSky && window.SkyVoice && utterancePending) {
          utterancePending = false;
          await window.SkyVoice.endUtterance();
        }
        await sendSpeech(text, { voiceFromSky: fromSky });
      }
    };

    rec.onspeechend = () => {
      if (utterancePending && window.SkyVoice) {
        utterancePending = false;
        window.SkyVoice.endUtterance();
      }
    };

    rec.onerror = (ev) => {
      if (ev.error !== "no-speech") setStatus("Mic: " + ev.error, false);
      utterancePending = false;
    };
    return rec;
  }

  async function startSensors() {
    if (active) return;
    setStatus("Pidiendo permisos…", true);
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: true,
      });
    } catch (e) {
      setStatus("Permiso denegado — cámara/mic", false);
      return;
    }
    if (preview) {
      preview.srcObject = stream;
      preview.classList.remove("hidden");
      await preview.play().catch(() => {});
    }
    if (window.SkyVoice) {
      window.SkyVoice.bindStream(stream);
      window.SkyVoice.setEnabled(skyVoiceOn());
      window.SkyVoice.ensureContext();
    }
    active = true;
    if (btnToggle) btnToggle.textContent = "⏹ Desconectar cámara y mic";
    await postJson("/api/caregiver/listening", { active: true });
    recognition = setupRecognition();
    if (recognition) {
      try {
        recognition.start();
      } catch (e) {
        console.warn("recognition start", e);
      }
    }
    visionTimer = setInterval(sendVisionFrame, 3000);
    sendVisionFrame();
    const sky = skyVoiceOn() ? " · voz celeste ☁" : "";
    setStatus("🎥👂 Conectado — habla o mira a la cámara" + sky, true);
  }

  async function stopSensors() {
    active = false;
    utterancePending = false;
    if (visionTimer) clearInterval(visionTimer);
    visionTimer = null;
    if (recognition) {
      try {
        recognition.stop();
      } catch (e) {
        /* ignore */
      }
      recognition = null;
    }
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    if (preview) {
      preview.srcObject = null;
      preview.classList.add("hidden");
    }
    if (window.NexoRenderer && window.NexoRenderer.setDivineVoice) {
      window.NexoRenderer.setDivineVoice(0);
    }
    await postJson("/api/caregiver/listening", { active: false });
    if (btnToggle) btnToggle.textContent = "🎥 Conectar cámara y micrófono";
    setStatus("Desconectado", null);
  }

  if (btnToggle) {
    btnToggle.addEventListener("click", () => {
      if (active) stopSensors();
      else startSensors();
    });
  }

  if (btnSpeak) {
    btnSpeak.addEventListener("click", () => {
      const inp = document.getElementById("chat-in");
      const t = inp && inp.value.trim();
      if (t) {
        sendSpeech(t, { voiceFromSky: skyVoiceOn() });
        inp.value = "";
      }
    });
  }

  if (skyVoiceToggle) {
    skyVoiceToggle.addEventListener("change", () => {
      if (window.SkyVoice) window.SkyVoice.setEnabled(skyVoiceToggle.checked);
    });
  }

  window.caregiverSensors = {
    start: startSensors,
    stop: stopSensors,
    sendSpeech,
    isActive: () => active,
  };
})();
