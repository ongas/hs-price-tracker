# Python Code Quality Standards

## Automatic Linting After Edits

**CRITICAL REQUIREMENT:** After EVERY edit to Python files (.py), you MUST run:

```bash
ruff check --fix <filepath>
```

This automatically fixes:
- Indentation errors
- Line length violations (E501)
- Import ordering
- Unused imports
- Syntax formatting

## Why This Matters

The Replace/Edit tool sometimes introduces indentation errors when making changes to Python code. Running `ruff check --fix` immediately after each edit prevents cascading syntax errors and ensures code quality.

## Workflow

1. Make edit to Python file
2. **IMMEDIATELY** run `ruff check --fix <filepath>`
3. Verify the file passes linting
4. Continue with next task

## DO NOT SKIP THIS STEP

Skipping the ruff fix leads to:
- SyntaxError exceptions
- E501 line length violations
- Cascading indentation problems
- Wasted time fixing preventable issues

**Always run ruff check --fix after Python edits. No exceptions.**
