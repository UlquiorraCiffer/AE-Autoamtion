/* globals app, $, comp, layer */

// ─── AnimeEdit AI — AE Host ExtendScript ───
// Provides functions callable from the CEP panel via evalScript.
//
// Naming convention: all exported functions live under the `ae` object
// so the panel can invoke them like  `ae.beatDetect()`.

// @target AfterEffects 23.0+

(function () {
  // eslint-disable-next-line no-unused-vars
  var ae = (function () {
    var NS = {};

    // ─── Utilities ───

    function getActiveComp() {
      var comp = app.project.activeItem;
      if (!comp || !(comp instanceof CompItem)) {
        alert("No active composition found.\nSelect a comp and try again.");
        return null;
      }
      return comp;
    }

    function ensureLayer(comp) {
      if (comp.numLayers === 0) {
        alert("The active composition is empty.\nAdd footage or a solid first.");
        return null;
      }
      return comp.layer(1);
    }

    function findOrCreateMarker(comp, time, comment) {
      var marker = new MarkerValue(comment);
      comp.markerProperty.setValueAtTime(time, marker);
    }

    function setKeyframe(layer, property, time, value) {
      var prop = layer.property(property);
      if (!prop || !prop.valid) return;
      prop.setValueAtTime(time, value);
    }

    // ─── Public API ───

    NS.beatDetect = function () {
      var comp = getActiveComp();
      if (!comp) return "ERR:no comp";
      // Placeholder: in v0.1 this will call the backend beat detector.
      // For now, place a sample marker at the start.
      findOrCreateMarker(comp, 0, "Beat");
      return "OK:beatDetect";
    };

    NS.sceneDetect = function () {
      var comp = getActiveComp();
      if (!comp) return "ERR:no comp";
      // Placeholder
      return "OK:sceneDetect";
    };

    NS.addZoom = function () {
      var comp = getActiveComp();
      if (!comp) return "ERR:no comp";
      var layer = ensureLayer(comp);
      if (!layer) return "ERR:no layer";
      var dur = comp.duration;
      // Scale keyframes: 100% → 120% → 100%
      setKeyframe(layer, "Transform/Scale", 0, [100, 100, 100]);
      setKeyframe(layer, "Transform/Scale", dur * 0.15, [120, 120, 100]);
      setKeyframe(layer, "Transform/Scale", dur * 0.3, [100, 100, 100]);
      return "OK:addZoom";
    };

    NS.addShake = function () {
      var comp = getActiveComp();
      if (!comp) return "ERR:no comp";
      var layer = ensureLayer(comp);
      if (!layer) return "ERR:no layer";
      // Apply the built-in Wiggle expression to Position
      var pos = layer.property("Transform/Position");
      if (pos && pos.valid) {
        pos.expression = "wiggle(15, 20)";
      }
      return "OK:addShake";
    };

    NS.addFlash = function () {
      var comp = getActiveComp();
      if (!comp) return "ERR:no comp";
      var whiteSolid = comp.layers.addSolid(
        [1, 1, 1],
        "Flash",
        comp.width,
        comp.height,
        comp.pixelAspect,
        comp.duration
      );
      whiteSolid.blendingMode = BlendingMode.ADD;
      var opacity = whiteSolid.property("Transform/Opacity");
      if (opacity && opacity.valid) {
        opacity.setValueAtTime(0, 0);
        opacity.setValueAtTime(0.05, 80);
        opacity.setValueAtTime(0.1, 0);
      }
      return "OK:addFlash";
    };

    NS.ping = function () {
      return "pong";
    };

    NS.getSettings = function () {
      try {
        var data = app.getPrefForPersistence(
          "AnimeEditAI",
          "settings"
        );
        return data || "";
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

    // ─── Register global ───
    // The CEP panel calls  evalScript("ae.beatDetect()")  etc.
    // We expose `ae` on the global object.
    try {
      // If another version already set `ae`, merge
      if (typeof ae !== "undefined" && ae !== null) {
        for (var key in NS) {
          if (NS.hasOwnProperty(key) && !ae.hasOwnProperty(key)) {
            ae[key] = NS[key];
          }
        }
      } else {
        // First load — assign
        this.ae = NS;
      }
    } catch (_) {
      this.ae = NS;
    }

    return NS;
  })();
})();
