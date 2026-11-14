import { defineConfig } from "vite";

export default defineConfig({
  // Relative paths so the build works under the GitHub Pages sub-path.
  base: "./",
  build: {
    rollupOptions: {
      // Two pages: the map and the methods page.
      input: { main: "index.html", methods: "methods.html" },
    },
  },
});
