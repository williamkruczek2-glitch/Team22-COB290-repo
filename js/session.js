/*
 * session.js — who is logged in.
 *
 * Part 1 is a static    prototype, so the user is hardcoded here.
 * When the login page (R06/R07) is merged in, it should store the signed-in
 * user with MIA.session.set(user) and these pages will pick it up.
 */
var MIA = window.MIA || {};

MIA.session = (function () {
  var KEY = 'mia_user';
  var fallback = { id: 'E01', name: 'Dilip Shah', role: 'manager', teamId: 'T1' };

  function get() {
    try {
      var raw = sessionStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) { return fallback; }
  }
  function set(user) {
    try { sessionStorage.setItem(KEY, JSON.stringify(user)); } catch (e) { /* storage blocked: keep fallback */ }
  }
  function isManager() { return get().role === 'manager'; }

  return { get: get, set: set, isManager: isManager };
})();

window.MIA = MIA;
