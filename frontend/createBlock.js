import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function toKebabCase(string) {
  return string.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
}

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

const blockName = process.argv[2];

if (!blockName) {
  console.error('Error: Block name is required');
  process.exit(1);
}

const dirPath = path.join(__dirname, 'src', 'components', capitalizeFirstLetter(blockName));
const kebabBlockName = toKebabCase(blockName);

async function run() {
  await fs.mkdir(dirPath, { recursive: true });
  console.log(`Directory ${dirPath} created`);

  const componentTemplate = `import React from 'react';
import './${capitalizeFirstLetter(blockName)}.css';

interface ${capitalizeFirstLetter(blockName)}Props {
  className?: string;
}

const ${capitalizeFirstLetter(blockName)}: React.FC<${capitalizeFirstLetter(blockName)}Props> = (props) => {
  const finalClassName = '${kebabBlockName} ' + (props.className || '');
  return (
    <div className={finalClassName}>
    </div>
  );
};

export default ${capitalizeFirstLetter(blockName)};
`;

  const scssTemplate = `.${kebabBlockName} {
}
`;

  const componentFilePath = path.join(dirPath, `${capitalizeFirstLetter(blockName)}.tsx`);
  const scssFilePath = path.join(dirPath, `${capitalizeFirstLetter(blockName)}.css`);

  await fs.writeFile(componentFilePath, componentTemplate);
  console.log(`${capitalizeFirstLetter(blockName)}.tsx created`);

  await fs.writeFile(scssFilePath, scssTemplate);
  console.log(`${blockName}.css created`);
}

run().catch((err) => console.error('Error:', err));
