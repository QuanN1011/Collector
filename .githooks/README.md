After cloning, point Git at this directory (once per clone):

```bash
git config core.hooksPath .githooks
```

The `prepare-commit-msg` hook is a no-op pass-through so no third-party footers are appended.
