/* ------------------------------------------------------------------ *
 * Lightbox for the feature-model mapping exports.
 *
 * The exported images are ~4917x288 (a 17:1 strip) up to 5724px wide, so
 * they are illegible inline. Thumbnails are progressive enhancement: with
 * JS off the .fm-shot button still shows the image and links to the file.
 *
 * Vanilla, no dependencies. Pan by drag, zoom by wheel/buttons, arrow keys
 * to step through the shots of the same figure, Esc to close.
 * ------------------------------------------------------------------ */
(function () {
  'use strict';

  var shots = Array.prototype.slice.call(document.querySelectorAll('.fm-shot'));
  if (!shots.length) return;

  var MAX_ZOOM = 8;

  // These strips are up to 5724px wide, so on a narrow viewport fitting one to
  // the screen needs a smaller scale than any fixed floor would allow. Derive
  // the floor from the current image instead, so "fit width" always works and
  // the user can always zoom back out to it.
  function minZoom() {
    if (!img.naturalWidth || !stage.clientWidth) return 0.02;
    return Math.min(0.1, (stage.clientWidth - 4) / img.naturalWidth);
  }

  var group = [];      // shots belonging to the figure currently open
  var index = 0;       // position within that group
  var zoom = 1;
  var fitWidth = true; // default: scale the strip to the viewport width
  var lastFocus = null;
  var panned = false;  // did the current gesture move far enough to be a pan?

  /* ---------------------------------------------------------- build */

  var lb = document.createElement('div');
  lb.className = 'lb';
  lb.hidden = true;
  lb.setAttribute('role', 'dialog');
  lb.setAttribute('aria-modal', 'true');
  lb.setAttribute('aria-label', 'Image viewer');
  lb.innerHTML =
    '<div class="lb-bar">' +
      '<span class="lb-title"></span>' +
      '<button type="button" data-act="fit" aria-pressed="true">Fit width</button>' +
      '<button type="button" data-act="out" aria-label="Zoom out">&minus;</button>' +
      '<span class="lb-zoom" aria-live="polite">100%</span>' +
      '<button type="button" data-act="in" aria-label="Zoom in">+</button>' +
      '<button type="button" data-act="prev" aria-label="Previous image">&#8592;</button>' +
      '<button type="button" data-act="next" aria-label="Next image">&#8594;</button>' +
      '<button type="button" data-act="close" aria-label="Close viewer">&times;</button>' +
    '</div>' +
    '<div class="lb-stage"><img alt=""></div>' +
    '<p class="lb-hint">Drag to pan · scroll to zoom · &larr; &rarr; to switch image · Esc to close</p>';
  document.body.appendChild(lb);

  var stage = lb.querySelector('.lb-stage');
  var img = lb.querySelector('.lb-stage img');
  var title = lb.querySelector('.lb-title');
  var zoomOut = lb.querySelector('.lb-zoom');
  var fitBtn = lb.querySelector('[data-act="fit"]');
  var prevBtn = lb.querySelector('[data-act="prev"]');
  var nextBtn = lb.querySelector('[data-act="next"]');

  // Images are draggable by default, and that broke drag-to-pan: pressing on
  // the strip started a native HTML5 image drag, which cancels the pointer
  // capture and fires pointercancel. The pan handler below treats that as
  // "gesture over", so panning died a few pixels in and left a drag ghost
  // trailing the cursor. Both guards are needed -- the CSS -webkit-user-drag
  // rule that accompanies this is non-standard and does nothing in Firefox.
  img.draggable = false;
  img.addEventListener('dragstart', function (e) { e.preventDefault(); });

  /* --------------------------------------------------------- render */

  function applyZoom(keepCentre) {
    var cx = 0, cy = 0;
    if (keepCentre && img.naturalWidth) {
      cx = (stage.scrollLeft + stage.clientWidth / 2) / (img.naturalWidth * zoom);
      cy = (stage.scrollTop + stage.clientHeight / 2) / (img.naturalHeight * zoom);
    }

    img.style.width = (img.naturalWidth * zoom) + 'px';
    img.style.height = 'auto';
    zoomOut.textContent = Math.round(zoom * 100) + '%';

    if (keepCentre && img.naturalWidth) {
      stage.scrollLeft = cx * img.naturalWidth * zoom - stage.clientWidth / 2;
      stage.scrollTop = cy * img.naturalHeight * zoom - stage.clientHeight / 2;
    }
  }

  function setZoom(next, keepCentre) {
    zoom = Math.min(MAX_ZOOM, Math.max(minZoom(), next));
    fitWidth = false;
    fitBtn.setAttribute('aria-pressed', 'false');
    applyZoom(keepCentre);
  }

  function doFit() {
    fitWidth = true;
    fitBtn.setAttribute('aria-pressed', 'true');
    if (!img.naturalWidth) return;
    // Leave a little room so the scrollbar never covers the edge.
    zoom = (stage.clientWidth - 4) / img.naturalWidth;
    applyZoom(false);
    stage.scrollTop = 0;
    stage.scrollLeft = 0;
  }

  function show(i) {
    index = (i + group.length) % group.length;
    var shot = group[index];
    var src = shot.getAttribute('data-full');
    var label = shot.getAttribute('data-title') || '';

    title.textContent = group.length > 1
      ? label + '  (' + (index + 1) + ' of ' + group.length + ')'
      : label;
    img.alt = shot.getAttribute('data-alt') || label;

    var multiple = group.length > 1;
    prevBtn.hidden = !multiple;
    nextBtn.hidden = !multiple;

    img.style.width = 'auto';
    img.src = src;
    if (img.complete && img.naturalWidth) {
      fitWidth ? doFit() : applyZoom(false);
    }
  }

  img.addEventListener('load', function () {
    fitWidth ? doFit() : applyZoom(false);
  });

  /* ----------------------------------------------------- open/close */

  function open(shot) {
    var fig = shot.closest('figure.fm-image') || document;
    group = Array.prototype.slice.call(fig.querySelectorAll('.fm-shot'));
    if (group.indexOf(shot) === -1) group = [shot];

    // Return focus to the thumbnail itself on close. document.activeElement is
    // unreliable here: a mouse click does not necessarily focus a <button>, so
    // it would often be <body> and focus would be lost when the viewer closes.
    lastFocus = shot;
    fitWidth = true;
    fitBtn.setAttribute('aria-pressed', 'true');
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    show(group.indexOf(shot));
    lb.querySelector('[data-act="close"]').focus();
  }

  function close() {
    lb.hidden = true;
    img.removeAttribute('src');
    document.body.style.overflow = '';
    // Prefer the thumbnail of whichever image is showing, so arrowing through
    // the group and closing leaves focus on what the user was last looking at.
    var target = group[index] || lastFocus;
    if (target && target.focus) target.focus();
  }

  shots.forEach(function (shot) {
    shot.addEventListener('click', function (e) {
      e.preventDefault();
      open(shot);
    });
  });

  /* -------------------------------------------------------- controls */

  // Swallow the click that ends a pan, before the backdrop handler below sees
  // it. The pan calls setPointerCapture on the stage, and pointer capture
  // retargets the trailing click to the capturing element -- so releasing after
  // a drag looks exactly like a genuine backdrop click and would close the
  // viewer every time. Only a gesture that actually moved is swallowed, so a
  // real click on the backdrop still closes. Capture phase, since the handler
  // it guards is registered on this same element.
  lb.addEventListener('click', function (e) {
    if (panned) {
      panned = false;
      e.stopPropagation();
    }
  }, true);

  lb.addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-act]');
    if (!btn) {
      // Backdrop click closes, but only outside the image itself.
      if (e.target === lb || e.target === stage) close();
      return;
    }
    switch (btn.getAttribute('data-act')) {
      case 'close': close(); break;
      case 'in':    setZoom(zoom * 1.25, true); break;
      case 'out':   setZoom(zoom / 1.25, true); break;
      case 'fit':   doFit(); break;
      case 'prev':  show(index - 1); break;
      case 'next':  show(index + 1); break;
    }
  });

  stage.addEventListener('wheel', function (e) {
    if (lb.hidden) return;
    e.preventDefault();
    var factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;

    // Zoom toward the pointer so the detail under the cursor stays put.
    var rect = stage.getBoundingClientRect();
    var px = stage.scrollLeft + (e.clientX - rect.left);
    var py = stage.scrollTop + (e.clientY - rect.top);
    var before = zoom;

    zoom = Math.min(MAX_ZOOM, Math.max(minZoom(), zoom * factor));
    fitWidth = false;
    fitBtn.setAttribute('aria-pressed', 'false');
    applyZoom(false);

    var ratio = zoom / before;
    stage.scrollLeft = px * ratio - (e.clientX - rect.left);
    stage.scrollTop = py * ratio - (e.clientY - rect.top);
  }, { passive: false });

  // Drag to pan.
  var dragging = false, sx = 0, sy = 0, sl = 0, st = 0;

  // Below this many pixels a gesture is a click with a shaky hand, not a drag.
  var PAN_SLOP = 3;

  stage.addEventListener('pointerdown', function (e) {
    if (e.button !== 0) return;
    dragging = true;
    panned = false;
    sx = e.clientX; sy = e.clientY;
    sl = stage.scrollLeft; st = stage.scrollTop;
    stage.classList.add('is-panning');
    stage.setPointerCapture(e.pointerId);
    // Suppress the text/image selection the press would otherwise begin; a
    // selection drag competes with the pan for the same gesture.
    e.preventDefault();
  });

  stage.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    if (Math.abs(e.clientX - sx) > PAN_SLOP ||
        Math.abs(e.clientY - sy) > PAN_SLOP) {
      panned = true;
    }
    stage.scrollLeft = sl - (e.clientX - sx);
    stage.scrollTop = st - (e.clientY - sy);
  });

  ['pointerup', 'pointercancel'].forEach(function (type) {
    stage.addEventListener(type, function (e) {
      dragging = false;
      stage.classList.remove('is-panning');
      // Release explicitly rather than relying on the implicit release: a
      // capture left dangling would keep routing the next gesture's events
      // here even after this one ended.
      if (stage.hasPointerCapture && stage.hasPointerCapture(e.pointerId)) {
        stage.releasePointerCapture(e.pointerId);
      }
    });
  });

  window.addEventListener('resize', function () {
    if (!lb.hidden && fitWidth) doFit();
  });

  /* -------------------------------------------------------- keyboard */

  document.addEventListener('keydown', function (e) {
    if (lb.hidden) return;

    switch (e.key) {
      case 'Escape': e.preventDefault(); close(); return;
      case 'ArrowLeft':  if (group.length > 1) { e.preventDefault(); show(index - 1); } return;
      case 'ArrowRight': if (group.length > 1) { e.preventDefault(); show(index + 1); } return;
      case '+': case '=': e.preventDefault(); setZoom(zoom * 1.25, true); return;
      case '-': e.preventDefault(); setZoom(zoom / 1.25, true); return;
      case '0': e.preventDefault(); doFit(); return;
    }

    // Focus trap.
    if (e.key === 'Tab') {
      var focusable = Array.prototype.filter.call(
        lb.querySelectorAll('button:not([hidden])'),
        function (el) { return el.offsetParent !== null; }
      );
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    }
  });
})();
