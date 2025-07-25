// generateDraftFromAI.js

const fs = require('fs');
const path = require('path');
const axios = require('axios');

const inputPath = path.join(__dirname, '..', 'input', 'notes-part3.txt');
const outputDir = path.join(__dirname, '..', 'drafts', 'Part3');

// Make sure output directory exists
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

async function generateBlogDraft() {
  try {
    const inputText = fs.readFileSync(inputPath, 'utf8').trim();

    if (!inputText) {
      console.error('❌ No input text found.');
      return;
    }

    const prompt = `
You're an AI content writer for a tech blog. Based on the following notes, generate a blog post in Markdown format.

The format should be:
---
title: "HexForge Content Engine – Part 3"
slug: "hexforge-content-engine-part-3"
tags: ["hexforge", "ai", "automation"]
visibility: public
publishDate: ${new Date().toISOString().split('T')[0]}
meta:
  description: "Automating blog creation from logs and dev notes in Part 3."
image: ""
video: ""
affiliateLink: ""
isDraft: true
---

# HexForge Content Engine – Part 3

Then continue with the full article below based on the notes.

Notes:
${inputText}
`;

    // 🔧 You can replace this with another local API later
    const response = await axios.post('https://api.openai.com/v1/completions', {
      model: 'text-davinci-003',
      prompt,
      max_tokens: 1200,
      temperature: 0.7,
      n: 1,
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    const outputText = response.data.choices[0].text.trim();

    const outputPath = path.join(
      outputDir,
      `generated-draft-${Date.now()}.md`
    );

    fs.writeFileSync(outputPath, outputText);
    console.log(`✅ Draft generated: ${outputPath}`);
  } catch (err) {
    console.error('❌ Draft generation failed:', err.response?.data || err.message);
  }
}

generateBlogDraft();
