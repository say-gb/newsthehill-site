(function () {
  'use strict';
  var list = document.getElementById('tick');
  if (!list) return;
  var region = list.closest('.ticker');
  var button = region.querySelector('.tk-toggle');
  var items = Array.from(list.children);
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var index = 0, timer = null, paused = false, hovering = false;
  var clone;

  function exposeCurrent() {
    items.forEach(function (item, i) {
      var link = item.querySelector('a');
      if (i === index % items.length) {
        item.removeAttribute('aria-hidden');
        link.removeAttribute('aria-hidden');
        link.removeAttribute('tabindex');
      } else {
        item.setAttribute('aria-hidden', 'true');
        link.setAttribute('aria-hidden', 'true');
        link.setAttribute('tabindex', '-1');
      }
    });
  }
  function position(instant) {
    if (instant) list.style.transition = 'none';
    list.style.transform = 'translateY(-' + (index * region.querySelector('.tk-window').clientHeight) + 'px)';
    if (instant) {
      void list.offsetHeight;
      list.style.transition = '';
    }
  }
  function schedule() {
    window.clearTimeout(timer);
    if (items.length < 2 || reduced.matches || paused || hovering || document.hidden || region.contains(document.activeElement)) return;
    timer = window.setTimeout(function () {
      index += 1;
      exposeCurrent();
      position(false);
      schedule();
    }, 4500);
  }
  function resetMotion() {
    if (reduced.matches) {
      index = 0;
      exposeCurrent();
      position(true);
    }
    button.hidden = reduced.matches || items.length < 2;
    schedule();
  }
  if (items.length > 1) {
    clone = items[0].cloneNode(true);
    clone.setAttribute('aria-hidden', 'true');
    clone.querySelector('a').setAttribute('aria-hidden', 'true');
    clone.querySelector('a').setAttribute('tabindex', '-1');
    list.appendChild(clone);
  }
  list.addEventListener('transitionend', function (event) {
    if (event.target === list && event.propertyName === 'transform' && index === items.length) {
      index = 0;
      position(true);
    }
  });
  region.addEventListener('mouseenter', function () { hovering = true; schedule(); });
  region.addEventListener('mouseleave', function () { hovering = false; schedule(); });
  region.addEventListener('focusin', schedule);
  region.addEventListener('focusout', function () { window.setTimeout(schedule, 0); });
  button.addEventListener('click', function () {
    paused = !paused;
    button.textContent = paused ? '▶' : '❚❚';
    button.setAttribute('aria-label', '최신 기사 자동 넘김 ' + (paused ? '재생' : '정지'));
    button.setAttribute('aria-pressed', String(paused));
    schedule();
  });
  document.addEventListener('visibilitychange', schedule);
  window.addEventListener('resize', function () {
    index %= items.length || 1;
    position(true);
  });
  if (reduced.addEventListener) reduced.addEventListener('change', resetMotion);
  else reduced.addListener(resetMotion);
  document.documentElement.classList.add('tk-js');
  exposeCurrent();
  resetMotion();
})();
