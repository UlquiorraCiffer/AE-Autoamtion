/* globals app, $, comp, layer */

// ─── AnimeEdit AI — AE Host ExtendScript ───
// Exposes all functions under the `ae` global so the CEP panel
// can invoke them via  csInterface.evalScript("ae.someFunc()").
//
// @target AfterEffects 23.0+

(function () {
  var NS = {};

  // ═══════════════════════════════════════════════════════════════
  //  Utilities
  // ═══════════════════════════════════════════════════════════════

  function getActiveComp() {
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) {
      return null;
    }
    return comp;
  }

  function ensureLayer(comp, index) {
    index = index || 1;
    if (comp.numLayers === 0) return null;
    var layer = comp.layer(index);
    if (!layer) return null;
    return layer;
  }

  function parseJSON(str) {
    try {
      return JSON.parse(str);
    } catch (_) {
      return null;
    }
  }

  // ═══════════════════════════════════════════════════════════════
  //  Composition Markers
  // ═══════════════════════════════════════════════════════════════

  NS.addMarkers = function (beatsJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var beats = parseJSON(beatsJson);
    if (!beats || !beats.length) return "ERR:invalid beats";

    var count = 0;
    for (var i = 0; i < beats.length; i++) {
      var b = beats[i];
      var time = Number(b.time_seconds);
      if (isNaN(time) || time < 0) continue;
      var label = b.label || "Beat " + (i + 1);
      var marker = new MarkerValue(label);
      comp.markerProperty.setValueAtTime(time, marker);
      count++;
    }
    return "OK:added " + count + " markers";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Split Layer
  // ═══════════════════════════════════════════════════════════════

  NS.splitLayer = function (layerIndex, time) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var t = Number(time);
    if (isNaN(t) || t < 0) return "ERR:invalid time";

    layer.splitLayer(t);
    return "OK:split";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Trim Layer (set in/out points)
  // ═══════════════════════════════════════════════════════════════

  NS.trimLayer = function (layerIndex, inTime, outTime) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var inT = Number(inTime);
    var outT = Number(outTime);

    if (!isNaN(inT) && inT >= 0) {
      layer.inPoint = inT;
    }
    if (!isNaN(outT) && outT > 0) {
      layer.outPoint = outT;
    }
    return "OK:trimmed";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Reorder Layers
  //  orderJson — array of layer indices in desired order, e.g. [3,1,2]
  // ═══════════════════════════════════════════════════════════════

  NS.reorderLayers = function (orderJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var order = parseJSON(orderJson);
    if (!order || !order.length) return "ERR:invalid order";

    for (var i = order.length - 1; i >= 0; i--) {
      var srcIdx = Number(order[i]);
      if (srcIdx < 1 || srcIdx > comp.numLayers) continue;
      var layer = comp.layer(srcIdx);
      if (!layer) continue;
      layer.moveToBeginning();
    }
    return "OK:reordered";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Apply Transform Keyframes
  //  keyframesJson — array of {time, scale?, position?, rotation?, opacity?}
  // ═══════════════════════════════════════════════════════════════

  NS.applyTransform = function (layerIndex, keyframesJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var kfs = parseJSON(keyframesJson);
    if (!kfs || !kfs.length) return "ERR:invalid keyframes";

    for (var i = 0; i < kfs.length; i++) {
      var kf = kfs[i];
      var t = Number(kf.time);

      if (kf.scale !== undefined) {
        var scaleProp = layer.property("Transform/Scale");
        if (scaleProp && scaleProp.valid) {
          scaleProp.setValueAtTime(t, kf.scale);
        }
      }

      if (kf.position !== undefined) {
        var posProp = layer.property("Transform/Position");
        if (posProp && posProp.valid) {
          posProp.setValueAtTime(t, kf.position);
        }
      }

      if (kf.rotation !== undefined) {
        var rotProp = layer.property("Transform/Rotation");
        if (rotProp && rotProp.valid) {
          rotProp.setValueAtTime(t, kf.rotation);
        }
      }

      if (kf.opacity !== undefined) {
        var opProp = layer.property("Transform/Opacity");
        if (opProp && opProp.valid) {
          opProp.setValueAtTime(t, kf.opacity);
        }
      }
    }
    return "OK:transform";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Zoom Preset
  //  params — { magnitude: 1.3, direction: "in"|"out", duration: 0.3 }
  // ═══════════════════════════════════════════════════════════════

  NS.applyZoom = function (layerIndex, paramsJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var params = parseJSON(paramsJson) || {};
    var magnitude = Number(params.magnitude) || 1.2;
    var direction = params.direction || "in";
    var dur = Number(params.duration) || comp.duration * 0.15;

    var startScale = [100, 100, 100];
    var peakScale = [100 * magnitude, 100 * magnitude, 100];
    var endScale = [100, 100, 100];
    var peakTime = dur;
    var endTime = dur * 2;

    var scaleProp = layer.property("Transform/Scale");
    if (!scaleProp || !scaleProp.valid) return "ERR:no scale";

    if (direction === "out") {
      startScale = [100 * magnitude, 100 * magnitude, 100];
      peakScale = [100, 100, 100];
    }

    scaleProp.setValueAtTime(0, startScale);
    scaleProp.setValueAtTime(peakTime, peakScale);
    scaleProp.setValueAtTime(endTime, endScale);

    return "OK:zoom";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Shake Preset
  //  params — { intensity: 0.5, frequency: 15, amplitude: 20 }
  // ═══════════════════════════════════════════════════════════════

  NS.applyShake = function (layerIndex, paramsJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var params = parseJSON(paramsJson) || {};
    var freq = Number(params.frequency) || 15;
    var amp = Number(params.amplitude) || 20;

    var posProp = layer.property("Transform/Position");
    if (!posProp || !posProp.valid) return "ERR:no position";

    // Remove any existing expression then apply wiggle
    posProp.expression = "";
    posProp.expression = "wiggle(" + freq + ", " + amp + ")";

    return "OK:shake";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Flash Preset
  //  params — { opacity: 80, duration_seconds: 0.05 }
  // ═══════════════════════════════════════════════════════════════

  NS.applyFlash = function (paramsJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var params = parseJSON(paramsJson) || {};
    var opacityVal = Number(params.opacity) || 80;
    var dur = Number(params.duration_seconds) || 0.05;

    var whiteSolid = comp.layers.addSolid(
      [1, 1, 1],
      "Flash",
      comp.width,
      comp.height,
      comp.pixelAspect,
      dur
    );
    whiteSolid.blendingMode = BlendingMode.ADD;

    var opProp = whiteSolid.property("Transform/Opacity");
    if (opProp && opProp.valid) {
      opProp.setValueAtTime(0, 0);
      opProp.setValueAtTime(0.01, opacityVal);
      opProp.setValueAtTime(dur, 0);
    }
    return "OK:flash";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Glow Preset
  //  params — { intensity: 0.5, radius: 30 }
  // ═══════════════════════════════════════════════════════════════

  NS.applyGlow = function (layerIndex, paramsJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var params = parseJSON(paramsJson) || {};
    var radius = Number(params.radius) || 30;
    var intensity = Number(params.intensity) || 0.5;

    // Add a Glow effect via the built-in AE Glow
    var glow = layer.property("ADBE Effect Parade").addProperty("ADBE Glo Glo Level");

    if (glow) {
      // Glow Radius
      var radiusParam = glow.property("ADBE Glo Glo Level-0004");
      if (radiusParam && radiusParam.valid) radiusParam.setValue(radius);

      // Glow Intensity
      var intParam = glow.property("ADBE Glo Glo Level-0003");
      if (intParam && intParam.valid) intParam.setValue(intensity);
    }

    return "OK:glow";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Velocity Ramp
  //  params — { speed: 1.5, ramp_in: 0.2, ramp_out: 0.3 }
  // ═══════════════════════════════════════════════════════════════

  NS.applyVelocityRamp = function (layerIndex, paramsJson) {
    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var layer = ensureLayer(comp, Number(layerIndex));
    if (!layer) return "ERR:no layer";

    var params = parseJSON(paramsJson) || {};
    var speed = Number(params.speed) || 1.5;
    var rampIn = Number(params.ramp_in) || 0.2;
    var rampOut = Number(params.ramp_out) || 0.3;

    var duration = layer.outPoint - layer.inPoint;
    if (duration <= 0) duration = comp.duration;

    // Apply time-remapping and set speed keyframes
    layer.timeRemapEnabled = true;
    var trProp = layer.property("ADBE Time Remapping");
    if (!trProp || !trProp.valid) return "ERR:no time remap";

    var rampInEnd = rampIn;
    var rampOutStart = duration - rampOut;

    trProp.setValueAtTime(0, 0);
    trProp.setValueAtTime(rampInEnd, rampInEnd * speed);
    trProp.setValueAtTime(rampOutStart, rampOutStart + (duration - rampOutStart) * speed);
    trProp.setValueAtTime(duration, duration);

    return "OK:velocity_ramp";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Execute an Edit Plan
  //  planJson — serialised EditPlan from the decision engine
  // ═══════════════════════════════════════════════════════════════

  NS.executePlan = function (planJson) {
    var plan = parseJSON(planJson);
    if (!plan || !plan.timeline) return "ERR:invalid plan";

    var comp = getActiveComp();
    if (!comp) return "ERR:no comp";

    var report = [];
    var timeline = plan.timeline;
    var effects = plan.effects || [];

    // 1. Trim and reorder according to timeline
    for (var t = 0; t < timeline.length; t++) {
      var entry = timeline[t];
      if (!entry.keep) {
        var idx = Number(entry.segment_index) + 1;
        var layer = comp.layer(idx);
        if (layer) layer.remove();
        report.push("removed layer " + idx);
      }
    }

    // 2. Apply effects
    for (var e = 0; e < effects.length; e++) {
      var fx = effects[e];
      var layerIdx = fx.segment_index !== undefined ? Number(fx.segment_index) + 1 : 1;
      var paramsStr = JSON.stringify(fx.params || {});
      switch (fx.type) {
        case "zoom":
          report.push(NS.applyZoom(layerIdx, paramsStr));
          break;
        case "shake":
          report.push(NS.applyShake(layerIdx, paramsStr));
          break;
        case "flash":
          report.push(NS.applyFlash(paramsStr));
          break;
        case "glow":
          report.push(NS.applyGlow(layerIdx, paramsStr));
          break;
        case "velocity_ramp":
          report.push(NS.applyVelocityRamp(layerIdx, paramsStr));
          break;
        default:
          report.push("unknown effect: " + fx.type);
      }
    }

    return "OK:plan executed (" + report.length + " steps)";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Legacy API (kept for backward compatibility)
  // ═══════════════════════════════════════════════════════════════

  NS.beatDetect = function () {
    return "OK:beatDetect (use addMarkers instead)";
  };

  NS.sceneDetect = function () {
    return "OK:sceneDetect";
  };

  NS.addZoom = function () {
    return NS.applyZoom(1, JSON.stringify({ magnitude: 1.2 }));
  };

  NS.addShake = function () {
    return NS.applyShake(1, JSON.stringify({ frequency: 15, amplitude: 20 }));
  };

  NS.addFlash = function () {
    return NS.applyFlash(JSON.stringify({ opacity: 80, duration_seconds: 0.05 }));
  };

  NS.ping = function () {
    return "pong";
  };

  // ═══════════════════════════════════════════════════════════════
  //  Settings Persistence
  // ═══════════════════════════════════════════════════════════════

  NS.getSettings = function () {
    try {
      return app.getPrefForPersistence("AnimeEditAI", "settings") || "";
    } catch (_) {
      return "";
    }
  };

  NS.setSettings = function (json) {
    try {
      app.setPrefForPersistence("AnimeEditAI", "settings", json);
      return "OK";
    } catch (_) {
      return "ERR";
    }
  };

  // ═══════════════════════════════════════════════════════════════
  //  Register global `ae` object
  // ═══════════════════════════════════════════════════════════════

  try {
    if (typeof ae !== "undefined" && ae !== null) {
      for (var key in NS) {
        if (NS.hasOwnProperty(key) && !ae.hasOwnProperty(key)) {
          ae[key] = NS[key];
        }
      }
    } else {
      this.ae = NS;
    }
  } catch (_) {
    this.ae = NS;
  }

  return NS;
})();
