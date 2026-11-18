# Commands: Mac (Terminal or VS Code terminal)

## One-time setup

```bash
xcode-select --install            # installs git (skip if `git --version` works)
brew install gh python            # needs Homebrew: https://brew.sh
gh auth login                     # GitHub.com → HTTPS → log in with browser
git config --global user.name  "Shaswat Mohanty"
git config --global user.email "shaswatprof2000@gmail.com"
```

## Get the project and open it in VS Code

```bash
cd ~/Documents
gh repo clone shaswatprof2000-git-hub/ev-market-india
cd ev-market-india
code .                            # opens VS Code (Cmd+Shift+P → "Shell Command: Install 'code'" if missing)
```

## Run the full pipeline

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/clean_data.py      # raw → data/cleaned/ + reports/
python scripts/analysis.py        # → analysis/PRIMARY_ANSWERS.md
python scripts/build_powerbi.py   # → powerbi/ (project + measures.dax)
```

## Save and push changes

```bash
git status
git add -A
git commit -m "Describe what changed"
git push
```

## Give Siddharth access (collaborator, can push)

```bash
gh api -X PUT repos/shaswatprof2000-git-hub/ev-market-india/collaborators/Siddharth-dataground -f permission=push
```

He gets an email/GitHub notification to accept. Read-only alternative: keep the repo public
and send him the link. He follows `POWERBI_GUIDE.md` on his Windows machine.

## Pull Siddharth's Power BI work back to your Mac

```bash
git pull
```
