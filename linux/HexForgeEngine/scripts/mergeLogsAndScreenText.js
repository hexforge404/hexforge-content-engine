// File: scripts/mergeLogsAndScreenText.js

const fs = require('fs');
const path = require('path');

// Define input directory and output path
const inputDir = path.join(__dirname, '..', 'input');
const outputPath = path.join(inputDir, 'session_data.json');

// Helper function to read a file if it exists
function readFileIfExists(filename) {
  const fullPath = path.join(inputDir, filename);
  console.log(`📄 Checking for file: ${fullPath}`);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ Found: ${filename}`);
    return fs.readFileSync(fullPath, 'utf-8').trim();
  } else {
    console.warn(`⚠️ Missing: ${filename}`);
    return '';
  }
}

console.log('🔍 Reading session files...');

// Read logs and extracted screen text
const windowsLog = readFileIfExists('session_windows.log');
const linuxLog = readFileIfExists('session_linux.log');
const screenText = readFileIfExists('screen-text.txt');
const chatTranscript = readFileIfExists('chattranscript.txt');

// Find all PNG screenshots in input directory
console.log('🖼️ Scanning for screenshots...');
const screenshots = fs
  .readdirSync(inputDir)
  .filter(file => file.endsWith('.png'));

console.log(`🧾 Found ${screenshots.length} screenshot(s):`, screenshots);

// Combine all session data into one JSON object
const sessionData = {
  project: '', // Optional: insert project name here
  part: '',    // Optional: insert part number here
  windowsLog,
  linuxLog,
  screenText,
  screenshots,
  chatTranscript
};

// Write combined session data to output JSON
fs.writeFileSync(outputPath, JSON.stringify(sessionData, null, 2));
console.log(`✅ Combined session data written to ${outputPath}`);
