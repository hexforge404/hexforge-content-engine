// File: buildBlogJsonFromAssets.js
// Purpose: Builds blog-draft.json from a specific asset folder passed as an argument

const fs = require("fs");
const path = require("path");

const inputDir = process.argv[2];
if (!inputDir || !fs.existsSync(inputDir)) {
  console.error("❌ Invalid or missing input directory.");
  process.exit(1);
}

console.log(`📂 Scanning folder: ${inputDir}`);

// Grab all logs, screen text, and video name
const logs = [];
let screenText = "";
let videoFilename = "";

fs.readdirSync(inputDir).forEach((file) => {
  const full = path.join(inputDir, file);
  if (file.endsWith(".log")) logs.push(fs.readFileSync(full, "utf-8"));
  if (file === "screen-text.txt") screenText = fs.readFileSync(full, "utf-8");
  if (file.endsWith(".mkv")) videoFilename = file;
});

const blog = {
  title: `Dev Blog: ${path.basename(inputDir)}`,
  slug: path.basename(inputDir).toLowerCase().replace(/\s+/g, "-"),
  logs,
  screenText,
  video: videoFilename,
  timestamp: new Date().toISOString(),
  meta: {
    description: "Auto-generated dev blog from logs and video",
    tags: ["hexforge", "automation", "dev"]
  },
  isDraft: true,
  visibility: "private"
};

const outPath = "/mnt/hdd-storage/hexforge-content-engine/output/blog-draft.json";
fs.writeFileSync(outPath, JSON.stringify(blog, null, 2));
console.log(`✅ Saved blog draft JSON to: ${outPath}`);
