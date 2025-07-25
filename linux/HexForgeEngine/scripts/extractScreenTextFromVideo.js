// File: scripts/extractScreenTextFromVideo.js

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Define the directory where videos are stored
const videoPath = '/mnt/hdd-storage/Videos/HexForge';

// Define base output directory for extracted frames and OCR results
const outputBase = '/mnt/hdd-storage/hexforge-content-engine/output';

// Define temp directory for storing extracted video frames
const tmpFramesDir = path.join(outputBase, 'frames');

// Check for a manual filename argument, fallback to latest if not provided
const args = process.argv.slice(2);
const manualFile = args[0];
console.log(`🛠️ Arguments received: ${args}`);

// Function to find the most recently modified MKV file in the given directory
function getLatestVideo(dir) {
  const files = fs.readdirSync(dir)
    .filter(f => f.endsWith('.mkv'))
    .map(f => ({ name: f, time: fs.statSync(path.join(dir, f)).mtime }))
    .sort((a, b) => b.time - a.time);
  console.log(`📄 Found ${files.length} MKV file(s)`);
  return files.length ? path.join(dir, files[0].name) : null;
}

// Determine video file to use
const videoFile = manualFile
  ? (path.isAbsolute(manualFile) ? manualFile : path.join(videoPath, manualFile))
  : getLatestVideo(videoPath);


if (!videoFile || !fs.existsSync(videoFile)) {
  console.error('❌ Video file not found:', videoFile);
  process.exit(1);
}
console.log('🎥 Using video:', videoFile);

// Extract base name to create a unique output directory for this video session
const baseName = path.basename(videoFile).replace(/\.[^/.]+$/, '');
const runOutputDir = path.join(outputBase, baseName);
console.log(`📂 Output will be saved to: ${runOutputDir}`);

// Ensure all necessary output directories exist
if (!fs.existsSync(outputBase)) fs.mkdirSync(outputBase, { recursive: true });
if (!fs.existsSync(tmpFramesDir)) fs.mkdirSync(tmpFramesDir, { recursive: true });
if (!fs.existsSync(runOutputDir)) fs.mkdirSync(runOutputDir, { recursive: true });

// Define path for final OCR text output
const ocrOutputPath = path.join(runOutputDir, 'screen-text.txt');

// Remove any previously extracted frames to avoid conflict
const existingFrames = fs.readdirSync(tmpFramesDir);
console.log(`🧹 Clearing ${existingFrames.length} old frame(s)`);
existingFrames.forEach(f => {
  const full = path.join(tmpFramesDir, f);
  if (f.endsWith('.png')) fs.unlinkSync(full);
});

// Extract frames from video using ffmpeg at 1 frame per second
console.log('🖼️ Extracting frames (1 fps)...');
try {
  execSync(`ffmpeg -loglevel error -stats -i "${videoFile}" -vf fps=1 "${tmpFramesDir}/frame_%05d.png"`, { stdio: 'inherit' });
  console.log(`✅ Frame extraction complete. Frames stored in: ${tmpFramesDir}`);
} catch (err) {
  console.error('❌ Frame extraction failed:', err.message);
  process.exit(1);
}

// Run OCR on each frame and collect all text output
console.log('🔍 Running OCR on frames...');
const frameFiles = fs.readdirSync(tmpFramesDir).filter(f => f.endsWith('.png')).sort();
console.log(`🧮 Found ${frameFiles.length} frame(s) to process.`);

let allText = '';

frameFiles.forEach((file, index) => {
  const framePath = path.join(tmpFramesDir, file);
  const preppedPath = framePath.replace('.png', '_prep.png');
  console.log(`🔠 Processing frame ${index + 1}/${frameFiles.length}: ${file}`);

  try {
    // Preprocess the image to improve OCR accuracy: resize, grayscale, threshold
    execSync(`convert "${framePath}" -resize 150% -colorspace Gray -threshold 50% "${preppedPath}"`);
    console.log(`🧪 Preprocessed frame saved as: ${preppedPath}`);

    // Run tesseract OCR on the preprocessed image
    const text = execSync(`tesseract "${preppedPath}" stdout`, { encoding: 'utf-8' });
    console.log(`📝 OCR result length: ${text.length} characters`);

    // Append the extracted text to the full output, labeling by frame
    allText += `\n\n--- Frame ${index + 1} (${file}) ---\n${text.trim()}`;
  } catch (err) {
    // If OCR fails, log the error and add a warning message in output
    console.warn(`⚠️ OCR failed on ${file}:`, err.message);
    allText += `\n\n--- Frame ${index + 1} (${file}) ---\n⚠️ OCR failed: ${err.message}`;
  }
});

// Save the combined OCR results to the output text file
fs.writeFileSync(ocrOutputPath, allText);
console.log(`✅ Screen text saved to: ${ocrOutputPath}`);
