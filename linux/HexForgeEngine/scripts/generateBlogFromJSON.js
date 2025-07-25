// scripts/generateBlogFromJSON.js

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const slugify = require('slugify');

// Input JSON
const inputPath = path.join(__dirname, '../input/blog.json');
const outputDir = path.join(__dirname, '../drafts');

// Ensure output directory exists
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

const input = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));

// Required fields
const title = input.title;
const slug =
  input.slug ||
  slugify(title, { lower: true, strict: true }) + '-' + Date.now();
const meta = input.meta || {};
const image = input.image || '';
const video = input.video || '';
const affiliateLink = input.affiliateLink || '';
const notes = input.notes || '';
const project = input.project || 'Unnamed Project';
const videoPath = input.videoPath || '';
const logs = input.logs || '';

const prompt = `
You're an AI content writer for the HexForge Labs blog.

Using the following project details, development notes, and logs — generate a full Markdown blog post (800–1200 words). Use helpful section headers, bullet points where appropriate, and an informative tone. Do NOT include YAML frontmatter. Do NOT repeat the title at the top.

---
Project: ${project}
Title: ${title}

🔧 Notes:
${notes}

🎥 Video Path:
${videoPath}

📜 Logs:
${logs}
`;

async function generateBlogContent() {
  try {
    const res = await axios.post('http://localhost:11434/api/generate', {
      model: 'mistral',
      prompt,
      stream: false
    });

    const content = res.data.response.trim();

    const frontmatter = `---\ntitle: "${title}"\nslug: "${slug}"\nmeta:\n  description: "${meta.description || ''}"\n  tags: [${(meta.tags || [])
      .map((t) => `"${t}"`)
      .join(', ')}]\nimage: "${image}"\nvideo: "${video}"\naffiliateLink: "${affiliateLink}"\nvisibility: "public"\nisDraft: true\npublishDate: ""\n---\n\n`;

    const finalOutput = frontmatter + content;
    const outputPath = path.join(outputDir, `${slug}.md`);

    fs.writeFileSync(outputPath, finalOutput, 'utf-8');
    console.log(`✅ Blog draft saved: drafts/${slug}.md`);
  } catch (err) {
    console.error('❌ Failed to generate blog post:', err.message);
  }
}

generateBlogContent();
