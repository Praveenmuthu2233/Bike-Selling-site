
const fs = require('fs');
const files = [
  'my-node-app/templates/profile.html',
  'my-node-app/templates/admin.html',
  'my-node-app/templates/enquiry-bike-details.html',
  'my-node-app/templates/SoldOutPage.html'
];

let hasError = false;
for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  const scripts = content.match(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/gi) || [];
  let scriptIndex = 0;
  for (const s of scripts) {
    scriptIndex++;
    let code = s.replace(/<script[^>]*>/i, '').replace(/<\/script>/i, '');
    // Clean Jinja template placeholders
    code = code.replace(/\{\{[^}]*\}\}/g, 'placeholder_val');
    code = code.replace(/\{%[^%]*%\}/g, '');
    try {
      new Function(code);
    } catch (e) {
      console.error(`JS Syntax Error in ${file} (Script #${scriptIndex}):`, e.message);
      hasError = true;
    }
  }
  console.log(`  ✓ Checked ${scripts.length} script tags in ${file}`);
}
if (hasError) process.exit(1);
