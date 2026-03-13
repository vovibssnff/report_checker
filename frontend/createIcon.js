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

const iconName = process.argv[2];

if (!iconName) {
  console.error('Error: Icon name is required');
  process.exit(1);
}

const dirPath = path.join(__dirname, 'src', 'components', 'icons', capitalizeFirstLetter(iconName));
const kebabIconName = toKebabCase(iconName);

async function run() {
  await fs.mkdir(dirPath, { recursive: true });
  console.log(`Directory ${dirPath} created`);

  const componentTemplate = `import React from 'react';
import type { IconProps } from '../IconProps';

interface ${capitalizeFirstLetter(iconName)}Props extends IconProps {}

const ${capitalizeFirstLetter(iconName)}: React.FC<${capitalizeFirstLetter(iconName)}Props> = ({
  size = '24px',
  fill = 'black',
  className = '',
  ...props
}) => {
  return (
    <svg
      width={size}
      height={size}
      fill={fill}
      className={\`${kebabIconName} \${className}\`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      {...props}
    >
      {/* Paste your SVG content here */}
    </svg>
  );
};

export default ${capitalizeFirstLetter(iconName)};
`;

  const componentFilePath = path.join(dirPath, `${capitalizeFirstLetter(iconName)}.tsx`);

  await fs.writeFile(componentFilePath, componentTemplate);
  console.log(`${capitalizeFirstLetter(iconName)}.tsx created`);
}

run().catch((err) => console.error('Error:', err));
