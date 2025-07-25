// File: scripts/buildBlogJsonFromSession.js

const fs = require('fs');
const path = require('path');
const slugify = require('slugify');

// Define the input directory and paths to session data and output blog file
const inputDir = path.join(__dirname, '..', 'input');
const sessionPath = path.join(inputDir, 'session_data.json');
const outputPath = path.join(inputDir, 'blog.json');

console.log('📦 Loading session data...');

// Check if session_data.json exists; if not, halt execution
if (!fs.existsSync(sessionPath)) {
  console.error('❌ session_data.json not found. Run mergeLogsAndScreenText.js first.');
  process.exit(1);
}

// Parse session data from file
const session = JSON.parse(fs.readFileSync(sessionPath, 'utf-8'));

// Construct title and slug using the current date and part number if available
const titleDate = new Date().toISOString().split('T')[0];
const partLabel = session.part ? `Part ${session.part}` : '';
const title = `Auto Blog: ${titleDate} ${partLabel}`.trim();
const slug = slugify(title, { lower: true, strict: true });

console.log(`📝 Building blog metadata for: ${title}`);

// Assemble the blog metadata object
const blog = {
  title,
  slug,
  meta: {
    description: 'Auto-generated blog from CLI, logs, and screen text.',
    tags: ['hexforge', 'dev', 'automation']
  },
  image: '',
  videoRaw: '',
  video: '',
  affiliateLink: '',
  visibility: 'public',
  isDraft: true,
  publishDate: '',
  project: session.project || '',
  notes: session.chatTranscript || '',
  videoPath: '',
  logs: `
----- WINDOWS LOG -----\n${session.windowsLog}

----- LINUX LOG -----\n${session.linuxLog}

----- SCREEN TEXT -----\n${session.screenText}`
};

console.log('🧾 Blog object constructed:', JSON.stringify(blog, null, 2));

// Write the constructed blog object to the output JSON file
fs.writeFileSync(outputPath, JSON.stringify(blog, null, 2));
console.log(`✅ Final blog input written to: ${outputPath}`);
