import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';

/** @type {import('eslint').Linter.FlatConfig[]} */
const ignores = [
  {
    ignores: ['build/*'],
  },
];

/** @type {import('eslint').Linter.FlatConfig[]} */
const jsConfig = [
  ...[js.configs.recommended].map((conf) => ({
    ...conf,
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  })),
];

const tsConfig = tseslint.config({
  files: ['**/*.ts'],
  extends: [
    js.configs.recommended,
    ...tseslint.configs.strictTypeChecked,
    ...tseslint.configs.stylisticTypeChecked,
  ],
  languageOptions: {
    parserOptions: {
      tsconfigRootDir: import.meta.dirname,
      project: ['./tsconfig.json'],
    },
  },
});

export default [...ignores, ...jsConfig, ...tsConfig];
