import {
  copyFileSync,
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const pub = join(root, "public");

mkdirSync(dist, { recursive: true });

cpSync(join(pub, "manifest.json"), join(dist, "manifest.json"));
if (existsSync(join(pub, "icons"))) {
  cpSync(join(pub, "icons"), join(dist, "icons"), { recursive: true });
}

// sidepanel.html is emitted at dist root by Vite
const htmlPath = join(dist, "sidepanel.html");
if (existsSync(htmlPath)) {
  let html = readFileSync(htmlPath, "utf8");
  html = html.replace(/src="\/assets\//g, 'src="./assets/');
  html = html.replace(/href="\/assets\//g, 'href="./assets/');
  writeFileSync(htmlPath, html);
}

console.log("Frontend build copied to dist/");
