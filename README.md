# po-diff

🔄 Compare gettext .po and Qt .ts translation files

Shows what changed between two versions of a translation file.

## Features

- **Added/Removed** – New or deleted translations
- **Modified** – Changed translations with diff
- **Fuzzy changes** – Track fuzzy flag changes
- **Multiple formats** – text, JSON, HTML reports
- **Localized** – Swedish and English

## Installation

```bash
# Debian/Ubuntu
echo "deb [trusted=yes] https://yeager.github.io/debian-repo stable main" | sudo tee /etc/apt/sources.list.d/yeager.list
sudo apt update && sudo apt install po-diff
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

## License

GPL-3.0-or-later
