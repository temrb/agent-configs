export function nextTheme(current) {
  return current === "dark" ? "light" : "dark";
}

export function restoreTheme(root, storage) {
  root.dataset.theme = "light";
}

export function toggleTheme(root, storage) {
  const selected = nextTheme(root.dataset.theme);
  root.dataset.theme = selected;
  storage.setItem("theme", selected);
}

if (typeof document !== "undefined" && typeof localStorage !== "undefined") {
  const root = document.documentElement;
  restoreTheme(root, localStorage);
  document.querySelector("#theme-toggle")?.addEventListener("click", () => {
    toggleTheme(root, localStorage);
  });
}
