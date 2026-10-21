## Git

GitHub Actions builds this project on macOS and Windows. Import
`.github/rulesets/protect-main.json` in GitHub Settings → Rules → Rulesets
to require the `Required validation` check before merging into `main`.
Tracking the JSON alone does not activate branch protection.

If no repository exists, run inside this project:

```sh
git init -b main
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git commit -m "Initial commit"
git remote add origin <repository-url>
```

For an existing repository, use `git remote -v` to inspect the remote.
Use `git remote set-url origin <repository-url>` to change it, or `git remote
add origin <repository-url>` when none exists. Scaffolding preserves existing Git metadata, hooks, and
configuration. Manage repository setup and cleanup yourself.
