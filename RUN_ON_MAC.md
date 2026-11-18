# Commands: Mac (Terminal or VS Code terminal)

## One-time setup

```bash
xcode-select --install            # installs git (skip if `git --version` works)
brew install gh python            # needs Homebrew: https://brew.sh
gh auth login                     # GitHub.com → HTTPS → log in with browser
git config --global user.name  "Shaswat Mohanty"
git config --global user.email "shaswatprof2000@gmail.com"
```

## Publish to GitHub (first time)

```bash
cd ~/Downloads/ev-market-india
gh repo create shaswatprof2000-git-hub/ev-market-india --public --source=. --remote=origin --push
```

The repo must be **public**: the Power BI file loads its data from GitHub's public raw URLs.

If the repo already exists on GitHub:

```bash
git remote add origin https://github.com/shaswatprof2000-git-hub/ev-market-india.git
git push -u origin main
```

## Share with Siddharth

Send him one of these:

- Dashboard in the browser (no Power BI needed):
  https://github.com/shaswatprof2000-git-hub/ev-market-india/blob/main/DASHBOARD.md
- Power BI files (download, extract, open `powerbi/EV_Market_Study.pbip`, Refresh):
  https://github.com/shaswatprof2000-git-hub/ev-market-india/archive/refs/heads/main.zip

Optional: make him a collaborator so he can push his `.pbix` back:

```bash
gh api -X PUT repos/shaswatprof2000-git-hub/ev-market-india/collaborators/Siddharth-dataground -f permission=push
```

## Re-run the pipeline after changing anything

```bash
cd ~/Downloads/ev-market-india
code .                            # open in VS Code
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/clean_data.py      # raw → data/cleaned/ + reports/
python scripts/analysis.py        # → analysis/PRIMARY_ANSWERS.md
python scripts/build_dashboard.py # → DASHBOARD.md + dashboard/*.png
python scripts/build_powerbi.py   # → powerbi/ (project + measures.dax)

git add -A
git commit -m "Describe what changed"
git push
```

## Pull Siddharth's Power BI work back

```bash
git pull
```
