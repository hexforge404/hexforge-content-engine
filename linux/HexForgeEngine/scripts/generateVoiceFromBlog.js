// generateVoiceFromBlog.js
const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const projectDir = '/mnt/hdd-storage/hexforge-content-engine/Assets';
const latestPartDir = fs.readFileSync(`${projectDir}/Latest`, 'utf8').trim();
const blogPath = path.join(latestPartDir, 'blog.md');
const voiceTextPath = path.join(latestPartDir, 'voice.txt');
const outputWavPath = path.join(latestPartDir, 'voice.wav');

if (!fs.existsSync(blogPath)) {
  console.error("❌ blog.md not found.");
  process.exit(1);
}

const blogText = fs.readFileSync(blogPath, 'utf8');

// Save plain version for TTS
fs.writeFileSync(voiceTextPath, blogText);

console.log("🗣️ Running TTS voice generation...");
try {
  execSync(`python3 /root/ai-tools/SadTalker/tts_from_text.py "${voiceTextPath}" "${outputWavPath}"`, { stdio: 'inherit' });
  console.log(`✅ Voiceover generated at: ${outputWavPath}`);
} catch (err) {
  console.error("❌ TTS generation failed:", err);
  process.exit(1);
}
