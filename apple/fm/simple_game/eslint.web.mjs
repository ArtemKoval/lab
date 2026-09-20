// Lint gate for the model generated browser layer.
// The build script runs "npx eslint -c eslint.web.mjs web/game.js" at step 10.
// The rule no-undef is the point of this gate: a renderer that calls a name which
// does not exist must never pass. Flat config enables no rule on its own.
export default [
  {
    files: ["web/*.js"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: {
        document: "readonly",
        window: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        requestAnimationFrame: "readonly",
        Math: "readonly"
      }
    },
    rules: {
      complexity: ["error", { max: 10 }],
      "max-depth": ["error", 2],
      "max-params": ["error", 4],
      "no-undef": "error",
      "no-unused-vars": "error"
    }
  }
];
