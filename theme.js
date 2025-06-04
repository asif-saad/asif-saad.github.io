// theme.js
function setTheme(theme) {
  document.body.className = theme;
  localStorage.setItem('theme', theme);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = theme === 'light' ? '🌚' : '🌙';
}
function toggleTheme() {
  setTheme(document.body.className === 'dark' ? 'light' : 'dark');
}
window.onload = function() {
  setTheme(localStorage.getItem('theme') || 'dark');
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.onclick = toggleTheme;
};
