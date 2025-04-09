const fs = require('fs');
const path = require('path');

const srcPath = path.join(__dirname, '..', 'tsconfig.react-library.json');
const destDir = path.join(__dirname, '..', 'node_modules', 'tsconfig');
const destPath = path.join(destDir, 'react-library.json');

try {
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }
  fs.copyFileSync(srcPath, destPath);
  console.log('Successfully copied tsconfig.react-library.json');
} catch (error) {
  console.error('Error copying tsconfig:', error);
  process.exit(1);
}
