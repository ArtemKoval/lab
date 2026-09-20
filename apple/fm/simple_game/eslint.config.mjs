// Complexity gate for the model generated core.
// The build script runs "npx eslint src" at step 7.
// The build exports COMPLEXITY_MAX, so the documented knob reaches this file.
// Keep the thresholds the same as stryker.config.json expects.
const MAX = Number(process.env.COMPLEXITY_MAX || 5);
export default [
  {
    ignores: [
      "node_modules/**",
      ".build/**",
      ".stryker-tmp/**",
      "reports/**",
      "web/**"
    ]
  },
  {
    files: ["src/**/*.js"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module"
    },
    rules: {
      complexity: ["error", { max: MAX }],
      "max-depth": ["error", 2],
      "max-lines-per-function": ["error", { max: 25, skipBlankLines: true, skipComments: true }],
      "max-params": ["error", 4],
      "no-undef": "error",
      "no-unused-vars": "error"
    }
  }
];
