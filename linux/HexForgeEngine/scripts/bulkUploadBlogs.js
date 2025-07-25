const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const axios = require('axios');

const draftsDir = path.join(__dirname, '..', 'drafts');
const postedDir = path.join(__dirname, '..', 'posted');
const logPath = path.join(__dirname, '..', 'logs', 'upload-log.txt');

async function uploadBlog(file) {
  const fileContent = fs.readFileSync(file, 'utf8');
  const { data: frontmatter, content: body } = matter(fileContent);

  const timestamp = Date.now();
  const uniqueSlug = `${frontmatter.slug}-${timestamp}`;

  const payload = {
    title: frontmatter.title,
    slug: uniqueSlug,
    tags: frontmatter.tags || [],
    visibility: frontmatter.visibility || 'public',
    publishDate: frontmatter.publishDate,
    meta: {
      description: frontmatter.meta?.description || ''
    },
    content: body,
    image: frontmatter.image || '',
    video: frontmatter.video || '',
    affiliateLink: frontmatter.affiliateLink || '',
    isDraft: frontmatter.isDraft || false
  };

  try {
    const response = await axios.post('http://localhost:8000/api/blog', payload, {
      headers: { 'Content-Type': 'application/json' }
    });

    const newFilename = `${uniqueSlug}.md`;
    fs.renameSync(file, path.join(postedDir, newFilename));

    const successLog = `[${new Date().toISOString()}] ✅ Uploaded: ${payload.slug} → ${newFilename}\n`;
    fs.appendFileSync(logPath, successLog);
    console.log(successLog.trim());
  } catch (err) {
    const errorMsg = err.response?.data?.error || err.message;
    const failLog = `[${new Date().toISOString()}] ❌ Failed: ${payload.slug} → ${errorMsg}\n`;
    fs.appendFileSync(logPath, failLog);
    console.warn(failLog.trim());
  }
}

async function runBulkUpload() {
  // Recursively find all .md files in draftsDir and subfolders
  function walkDir(dir, filelist = []) {
    fs.readdirSync(dir).forEach(file => {
      const fullPath = path.join(dir, file);
      if (fs.statSync(fullPath).isDirectory()) {
        walkDir(fullPath, filelist);
      } else if (file.endsWith('.md')) {
        filelist.push(fullPath);
      }
    });
    return filelist;
  }

  const files = walkDir(draftsDir);

  if (files.length === 0) {
    console.log('📭 No draft files found in /drafts.');
    return;
  }

  console.log(`🚀 Found ${files.length} draft(s) to process...\n`);

  for (const file of files) {
    await uploadBlog(file);
  }

  console.log('\n✅ Bulk upload finished.');
}

runBulkUpload();
