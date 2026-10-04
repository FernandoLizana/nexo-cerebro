/**
 * Voz celeste — micrófono del cuidador desde el cielo (audio espacial + reverb).
 */
(function (global) {
  let audioCtx = null;
  let mediaStream = null;
  let mediaRecorder = null;
  let recordChunks = [];
  let enabled = true;
  let speaking = false;
  let panner = null;
  let reverbGain = null;
  let dryGain = null;
  let skyAnchor = { x: 40, y: 22, z: 20 };

  function ensureContext() {
    if (!audioCtx) {
      const AC = global.AudioContext || global.webkitAudioContext;
      if (!AC) return null;
      audioCtx = new AC();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume().catch(() => {});
    }
    return audioCtx;
  }

  function buildChain() {
    const ctx = ensureContext();
    if (!ctx) return null;
    if (panner) return ctx;

    panner = ctx.createPanner();
    panner.panningModel = "HRTF";
    panner.distanceModel = "inverse";
    panner.refDistance = 2;
    panner.maxDistance = 80;
    panner.rolloffFactor = 0.8;
    panner.coneInnerAngle = 360;
    panner.coneOuterAngle = 0;
    setSkyPosition(skyAnchor.x, skyAnchor.y, skyAnchor.z);

    const convolver = ctx.createConvolver();
    convolver.buffer = makeReverbImpulse(ctx, 2.8, 2.5);

    reverbGain = ctx.createGain();
    reverbGain.gain.value = 0.55;
    dryGain = ctx.createGain();
    dryGain.gain.value = 0.35;

    panner.connect(dryGain);
    panner.connect(convolver);
    convolver.connect(reverbGain);
    dryGain.connect(ctx.destination);
    reverbGain.connect(ctx.destination);
    return ctx;
  }

  function makeReverbImpulse(ctx, duration, decay) {
    const rate = ctx.sampleRate;
    const len = rate * duration;
    const impulse = ctx.createBuffer(2, len, rate);
    for (let c = 0; c < 2; c++) {
      const ch = impulse.getChannelData(c);
      for (let i = 0; i < len; i++) {
        ch[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
      }
    }
    return impulse;
  }

  function setSkyPosition(x, y, z) {
    skyAnchor = { x, y, z };
    if (!panner) return;
    if (panner.positionX) {
      panner.positionX.setValueAtTime(x, audioCtx.currentTime);
      panner.positionY.setValueAtTime(y, audioCtx.currentTime);
      panner.positionZ.setValueAtTime(z, audioCtx.currentTime);
    } else {
      panner.setPosition(x, y, z);
    }
  }

  function updateListener(x, y, z, fx, fy, fz) {
    const ctx = ensureContext();
    if (!ctx || !ctx.listener) return;
    const l = ctx.listener;
    if (l.positionX) {
      l.positionX.setValueAtTime(x, ctx.currentTime);
      l.positionY.setValueAtTime(y, ctx.currentTime);
      l.positionZ.setValueAtTime(z, ctx.currentTime);
      if (fx != null) {
        l.forwardX.setValueAtTime(fx, ctx.currentTime);
        l.forwardY.setValueAtTime(fy, ctx.currentTime);
        l.forwardZ.setValueAtTime(fz, ctx.currentTime);
      }
    } else if (l.setPosition) {
      l.setPosition(x, y, z);
    }
  }

  function bindStream(stream) {
    mediaStream = stream;
    buildChain();
    try {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      mediaRecorder = new MediaRecorder(stream, { mimeType: mime, audioBitsPerSecond: 96000 });
      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) recordChunks.push(e.data);
      };
    } catch (e) {
      console.warn("SkyVoice MediaRecorder", e);
      mediaRecorder = null;
    }
  }

  function beginUtterance() {
    if (!enabled || !mediaRecorder) return;
    recordChunks = [];
    try {
      if (mediaRecorder.state === "inactive") {
        mediaRecorder.start(200);
      }
    } catch (e) {
      console.warn("SkyVoice record start", e);
    }
    speaking = true;
    if (typeof global.NexoRenderer !== "undefined" && global.NexoRenderer.setDivineVoice) {
      global.NexoRenderer.setDivineVoice(1.0);
    }
  }

  function playBlobFromSky(blob) {
    return new Promise((resolve, reject) => {
      const ctx = buildChain();
      if (!ctx || !panner) {
        resolve(false);
        return;
      }
      blob
        .arrayBuffer()
        .then((ab) => ctx.decodeAudioData(ab))
        .then((buffer) => {
          const src = ctx.createBufferSource();
          src.buffer = buffer;
          const gain = ctx.createGain();
          gain.gain.value = 1.15;
          src.connect(gain);
          gain.connect(panner);
          src.onended = () => {
            speaking = false;
            if (global.NexoRenderer && global.NexoRenderer.setDivineVoice) {
              global.NexoRenderer.setDivineVoice(0);
            }
            resolve(true);
          };
          src.start(0);
        })
        .catch(reject);
    });
  }

  function endUtterance() {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state !== "recording") {
        speaking = false;
        resolve(false);
        return;
      }
      mediaRecorder.onstop = async () => {
        const blob = new Blob(recordChunks, { type: recordChunks[0]?.type || "audio/webm" });
        recordChunks = [];
        if (blob.size > 800 && enabled) {
          try {
            await playBlobFromSky(blob);
            resolve(true);
          } catch (e) {
            console.warn("SkyVoice playback", e);
            speaking = false;
            resolve(false);
          }
        } else {
          speaking = false;
          if (global.NexoRenderer && global.NexoRenderer.setDivineVoice) {
            global.NexoRenderer.setDivineVoice(0);
          }
          resolve(false);
        }
      };
      try {
        mediaRecorder.stop();
      } catch (e) {
        speaking = false;
        resolve(false);
      }
    });
  }

  function setEnabled(on) {
    enabled = !!on;
  }

  function isEnabled() {
    return enabled;
  }

  function isSpeaking() {
    return speaking;
  }

  global.SkyVoice = {
    bindStream,
    beginUtterance,
    endUtterance,
    setSkyPosition,
    updateListener,
    setEnabled,
    isEnabled,
    isSpeaking,
    ensureContext,
  };
})(window);
