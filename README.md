# po-diff

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/yeager/po-diff/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-green)](LICENSE)
[![Transifex](https://img.shields.io/badge/translate-Transifex-blue)](https://app.transifex.com/danielnylander/po-diff/)

🔄 Compare gettext .po and Qt .ts translation files

Shows what changed between two versions of a translation file.

## Features

- **Added/Removed** – New or deleted translations
- **Modified** – Changed translations with diff
- **Fuzzy changes** – Track fuzzy flag changes
- **Multiple formats** – text, JSON, HTML reports
- **Man pages** – English + Swedish (`man po-diff`)
- **Internationalized** – 11+ languages via [Transifex](https://app.transifex.com/danielnylander/po-diff/)

## Installation

### Debian/Ubuntu
```bash
echo "deb [trusted=yes] https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager.list
sudo apt update && sudo apt install po-diff
```

### Fedora/RHEL
```bash
sudo tee /etc/yum.repos.d/yeager.repo << REPO
[yeager]
name=Yeager Tools
baseurl=https://yeager.github.io/rpm-repo
enabled=1
gpgcheck=0
REPO
sudo dnf install po-diff
```

## Usage

```bash
# Compare two files
po-diff old.po new.po

# Generate HTML report
po-diff -f html -o diff.html old.po new.po

# JSON output
po-diff -f json old.po new.po > changes.json
```

## Output Example

```
📊 po-diff: old.po → new.po
============================================================

📈 Summary
   Old entries: 150
   New entries: 165
   Added: 20
   Removed: 5
   Modified: 8

➕ Added (20)
----------------------------------------
  [45] "New feature message"
  [67] "Another new string"
  ...
```

## Translation

This app is translated via Transifex. Help translate it into your language!

**[→ Translate on Transifex](https://app.transifex.com/danielnylander/po-diff/)**

1. Create a free account at [Transifex](https://www.transifex.com)
2. Join the [danielnylander](https://app.transifex.com/danielnylander/) organization
3. Pick `po-diff` and start translating

Currently available in: ar, de, es, fr, ja, ko, pl, pt_BR, ru, sv, zh_CN

## License

GPL-3.0-or-later

## Author

Daniel Nylander <daniel@danielnylander.se>
