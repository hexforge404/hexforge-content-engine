// uploadBlogPost.js

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const axios = require('axios');

const draftName = 'test-draft-2.md'; // Change if needed
const draftPath = path.join(__dirname, '..', 'drafts', draftName);
const postedDir = path.join(__dirname, '..', 'posted');
const logPath = path.join(__dirname, '..', 'logs', 'upload-log.txt');

async function uploadBlogPost() {
  try {
    const fileContent = fs.readFileSync(draftPath, 'utf8');
    const { data: frontmatter, content: body } = matter(fileContent);

    const payload = {
      title: frontmatter.title,
      slug: frontmatter.slug,
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

    const response = await axios.post('http://localhost:8000/api/blog', payload, {
      headers: { 'Content-Type': 'application/json' }
    });

    console.log('✅ Blog post uploaded successfully:', response.data);

    // Log the post
    const timestamp = new Date().toISOString();
    fs.appendFileSync(logPath, `[${timestamp}] Uploaded: ${frontmatter.title} (slug: ${frontmatter.slug})\n`);

    // Ensure posted directory exists
    if (!fs.existsSync(postedDir)) {
      fs.mkdirSync(postedDir);
    }

    // Move draft file to posted with timestamped filename
    const newFilename = `${frontmatter.slug}-${Date.now()}.md`;
    const newFilePath = path.join(postedDir, newFilename);
    fs.renameSync(draftPath, newFilePath);
    console.log(`📦 Archived draft to: ${newFilePath}`);
  } catch (err) {
    console.error('❌ Blog upload failed:', err.response?.data || err.message);
  }
}

uploadBlogPost();
