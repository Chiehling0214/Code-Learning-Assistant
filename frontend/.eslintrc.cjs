module.exports = {
  root: true,
  env: { browser: true, es2021: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  // src/components/ui holds vendored shadcn/ui primitives; they intentionally
  // co-export variant helpers, which conflicts with the react-refresh rule.
  ignorePatterns: ["dist", ".eslintrc.cjs", "src/components/ui"],
  parser: "@typescript-eslint/parser",
  plugins: ["react-refresh"],
  rules: {
    "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
  },
};
