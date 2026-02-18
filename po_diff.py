#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# po-diff - Compare PO/TS translation files
# Copyright (C) 2026 Daniel Nylander <daniel@danielnylander.se>
"""
po-diff - Compare gettext .po and Qt .ts translation files

Shows what changed between two versions:
- New translations
- Removed translations
- Modified translations
- Fuzzy changes
"""

import argparse
import gettext
import json
import locale
import os
import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

__version__ = "1.0.1"

# Translation setup
DOMAIN = "po-diff"

_possible_locale_dirs = [
    Path("/usr/share/po-diff/locale"),
    Path(__file__).parent / "locale",
]
LOCALE_DIR = None
for _dir in _possible_locale_dirs:
    if _dir.is_dir() and (list(_dir.glob("*/LC_MESSAGES")) or list(_dir.glob("*.pot"))):
        LOCALE_DIR = _dir
        break

try:
    lang = locale.getlocale()[0]
    if lang:
        lang = lang.split('_')[0]
    if LOCALE_DIR:
        translation = gettext.translation(DOMAIN, LOCALE_DIR, languages=[lang], fallback=True)
        _ = translation.gettext
    else:
        _ = lambda x: x
except:
    _ = lambda x: x


class ChangeType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    FUZZY_ADDED = "fuzzy_added"
    FUZZY_REMOVED = "fuzzy_removed"


@dataclass
class Change:
    """Represents a single change between files."""
    change_type: ChangeType
    msgid: str
    old_value: str = ""
    new_value: str = ""
    line: int = 0
    
    def to_dict(self):
        return {
            "type": self.change_type.value,
            "msgid": self.msgid,
            "old": self.old_value,
            "new": self.new_value,
            "line": self.line
        }


@dataclass
class DiffResult:
    """Result of comparing two files."""
    old_file: str
    new_file: str
    changes: list = field(default_factory=list)
    old_count: int = 0
    new_count: int = 0
    
    @property
    def added_count(self):
        return sum(1 for c in self.changes if c.change_type == ChangeType.ADDED)
    
    @property
    def removed_count(self):
        return sum(1 for c in self.changes if c.change_type == ChangeType.REMOVED)
    
    @property
    def modified_count(self):
        return sum(1 for c in self.changes if c.change_type == ChangeType.MODIFIED)


def parse_po_file(filepath: str) -> dict:
    """Parse a .po file into a dictionary of msgid -> (msgstr, line, fuzzy)."""
    entries = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple PO parser
    current_msgid = None
    current_msgstr = None
    current_line = 0
    is_fuzzy = False
    in_msgid = False
    in_msgstr = False
    
    for i, line in enumerate(content.split('\n'), 1):
        line_stripped = line.strip()
        
        if line_stripped.startswith('#,') and 'fuzzy' in line_stripped:
            is_fuzzy = True
            continue
        
        if line_stripped.startswith('#'):
            continue
        
        if line_stripped.startswith('msgid '):
            if current_msgid is not None and current_msgstr is not None:
                if current_msgid:  # Skip header
                    entries[current_msgid] = (current_msgstr, current_line, is_fuzzy)
            
            match = re.match(r'msgid\s+"(.*)"', line_stripped)
            current_msgid = match.group(1) if match else ""
            current_msgstr = None
            current_line = i
            in_msgid = True
            in_msgstr = False
            is_fuzzy = False
            
        elif line_stripped.startswith('msgstr '):
            match = re.match(r'msgstr\s+"(.*)"', line_stripped)
            current_msgstr = match.group(1) if match else ""
            in_msgid = False
            in_msgstr = True
            
        elif line_stripped.startswith('"') and line_stripped.endswith('"'):
            value = line_stripped[1:-1]
            if in_msgid:
                current_msgid += value
            elif in_msgstr:
                current_msgstr += value
    
    # Don't forget last entry
    if current_msgid is not None and current_msgstr is not None:
        if current_msgid:
            entries[current_msgid] = (current_msgstr, current_line, is_fuzzy)
    
    return entries


def compare_files(old_path: str, new_path: str) -> DiffResult:
    """Compare two PO files and return the differences."""
    old_entries = parse_po_file(old_path)
    new_entries = parse_po_file(new_path)
    
    result = DiffResult(
        old_file=old_path,
        new_file=new_path,
        old_count=len(old_entries),
        new_count=len(new_entries)
    )
    
    # Find added and modified
    for msgid, (msgstr, line, fuzzy) in new_entries.items():
        if msgid not in old_entries:
            result.changes.append(Change(
                change_type=ChangeType.ADDED,
                msgid=msgid,
                new_value=msgstr,
                line=line
            ))
        else:
            old_msgstr, old_line, old_fuzzy = old_entries[msgid]
            if msgstr != old_msgstr:
                result.changes.append(Change(
                    change_type=ChangeType.MODIFIED,
                    msgid=msgid,
                    old_value=old_msgstr,
                    new_value=msgstr,
                    line=line
                ))
            elif fuzzy and not old_fuzzy:
                result.changes.append(Change(
                    change_type=ChangeType.FUZZY_ADDED,
                    msgid=msgid,
                    new_value=msgstr,
                    line=line
                ))
            elif not fuzzy and old_fuzzy:
                result.changes.append(Change(
                    change_type=ChangeType.FUZZY_REMOVED,
                    msgid=msgid,
                    new_value=msgstr,
                    line=line
                ))
    
    # Find removed
    for msgid, (msgstr, line, fuzzy) in old_entries.items():
        if msgid not in new_entries:
            result.changes.append(Change(
                change_type=ChangeType.REMOVED,
                msgid=msgid,
                old_value=msgstr,
                line=line
            ))
    
    return result


def format_text(result: DiffResult) -> str:
    """Format diff result as text."""
    lines = []
    lines.append(_("📊 po-diff: {old} → {new}").format(old=result.old_file, new=result.new_file))
    lines.append("=" * 60)
    lines.append("")
    
    # Summary
    lines.append(_("📈 Summary"))
    lines.append(_("   Old entries: {count}").format(count=result.old_count))
    lines.append(_("   New entries: {count}").format(count=result.new_count))
    lines.append(_("   Added: {count}").format(count=result.added_count))
    lines.append(_("   Removed: {count}").format(count=result.removed_count))
    lines.append(_("   Modified: {count}").format(count=result.modified_count))
    lines.append("")
    
    if not result.changes:
        lines.append(_("✅ No changes found"))
        return '\n'.join(lines)
    
    # Group by type
    for change_type, icon, label in [
        (ChangeType.ADDED, "➕", _("Added")),
        (ChangeType.REMOVED, "➖", _("Removed")),
        (ChangeType.MODIFIED, "✏️", _("Modified")),
        (ChangeType.FUZZY_REMOVED, "✓", _("Fuzzy resolved")),
        (ChangeType.FUZZY_ADDED, "❓", _("Marked fuzzy")),
    ]:
        changes = [c for c in result.changes if c.change_type == change_type]
        if changes:
            lines.append(f"{icon} {label} ({len(changes)})")
            lines.append("-" * 40)
            for c in changes[:20]:  # Limit to 20 per category
                msgid_short = c.msgid[:50] + "..." if len(c.msgid) > 50 else c.msgid
                lines.append(f"  [{c.line}] \"{msgid_short}\"")
                if c.old_value and c.new_value:
                    lines.append(f"      - {c.old_value[:60]}")
                    lines.append(f"      + {c.new_value[:60]}")
            if len(changes) > 20:
                lines.append(_("      ... and {count} more").format(count=len(changes) - 20))
            lines.append("")
    
    return '\n'.join(lines)


def format_json(result: DiffResult) -> str:
    """Format diff result as JSON."""
    return json.dumps({
        "old_file": result.old_file,
        "new_file": result.new_file,
        "old_count": result.old_count,
        "new_count": result.new_count,
        "summary": {
            "added": result.added_count,
            "removed": result.removed_count,
            "modified": result.modified_count
        },
        "changes": [c.to_dict() for c in result.changes]
    }, indent=2, ensure_ascii=False)


def format_html(result: DiffResult) -> str:
    """Format diff result as HTML."""
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>po-diff Report</title>
    <style>
        :root {{
            --bg: #1a1a2e;
            --card: #16213e;
            --text: #eee;
            --added: #2ecc71;
            --removed: #e74c3c;
            --modified: #f39c12;
            --info: #3498db;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: var(--text); border-bottom: 2px solid var(--info); padding-bottom: 10px; }}
        h2 {{ color: var(--info); margin-top: 30px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat {{
            background: var(--card);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.8em; font-weight: bold; }}
        .stat-label {{ opacity: 0.8; font-size: 0.85em; }}
        .added {{ color: var(--added); }}
        .removed {{ color: var(--removed); }}
        .modified {{ color: var(--modified); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: var(--card);
            border-radius: 10px;
            overflow: hidden;
        }}
        th, td {{ padding: 10px 15px; text-align: left; }}
        th {{ background: rgba(52, 152, 219, 0.2); }}
        tr:nth-child(even) {{ background: rgba(255,255,255,0.05); }}
        .diff-old {{ background: rgba(231, 76, 60, 0.2); text-decoration: line-through; }}
        .diff-new {{ background: rgba(46, 204, 113, 0.2); }}
        .msgid {{ font-family: monospace; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 po-diff Report</h1>
        <p><strong>{result.old_file}</strong> → <strong>{result.new_file}</strong></p>
        <p>Generated: {time.strftime("%Y-%m-%d %H:%M")}</p>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{result.old_count}</div>
                <div class="stat-label">Old entries</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.new_count}</div>
                <div class="stat-label">New entries</div>
            </div>
            <div class="stat">
                <div class="stat-value added">{result.added_count}</div>
                <div class="stat-label">Added</div>
            </div>
            <div class="stat">
                <div class="stat-value removed">{result.removed_count}</div>
                <div class="stat-label">Removed</div>
            </div>
            <div class="stat">
                <div class="stat-value modified">{result.modified_count}</div>
                <div class="stat-label">Modified</div>
            </div>
        </div>
'''
    
    if not result.changes:
        html += '<p style="color: var(--added); font-size: 1.2em;">✅ No changes found!</p>\n'
    else:
        html += '''
        <h2>📋 All Changes</h2>
        <table>
            <tr><th>Type</th><th>Line</th><th>Message ID</th><th>Old</th><th>New</th></tr>
'''
        for c in sorted(result.changes, key=lambda x: x.line):
            type_class = c.change_type.value.replace('_', '-')
            icon = {"added": "➕", "removed": "➖", "modified": "✏️", 
                    "fuzzy_added": "❓", "fuzzy_removed": "✓"}.get(c.change_type.value, "•")
            old_val = c.old_value[:100] + "..." if len(c.old_value) > 100 else c.old_value
            new_val = c.new_value[:100] + "..." if len(c.new_value) > 100 else c.new_value
            msgid_short = c.msgid[:80] + "..." if len(c.msgid) > 80 else c.msgid
            
            html += f'''            <tr>
                <td class="{type_class}">{icon} {c.change_type.value}</td>
                <td>{c.line}</td>
                <td class="msgid">{msgid_short}</td>
                <td class="diff-old">{old_val}</td>
                <td class="diff-new">{new_val}</td>
            </tr>
'''
        html += '        </table>\n'
    
    html += '''
    </div>
</body>
</html>'''
    
    return html


class TranslatedHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def start_section(self, heading):
        translations = {
            'positional arguments': _('positional arguments'),
            'options': _('options'),
            'optional arguments': _('options'),
        }
        heading = translations.get(heading, heading)
        super().start_section(heading)


def main():
    parser = argparse.ArgumentParser(
        description=_('po-diff - Compare PO/TS translation files'),
        add_help=False,
        formatter_class=TranslatedHelpFormatter,
        epilog=_("""
Examples:
  po-diff old.po new.po                    # Compare two files
  po-diff -f html -o diff.html old.po new.po  # Generate HTML report
  po-diff -f json old.po new.po            # JSON output
        """)
    )
    
    parser.add_argument('old_file', help=_('Old/original file'))
    parser.add_argument('new_file', help=_('New/updated file'))
    parser.add_argument('-f', '--format', choices=['text', 'json', 'html'], default='text',
                        help=_('Output format (default: text)'))
    parser.add_argument('-o', '--output', metavar='FILE', help=_('Save report to file'))
    parser.add_argument('-h', '--help', action='help', help=_('Show this help message and exit'))
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}',
                        help=_('Show version number and exit'))
    
    args = parser.parse_args()
    
    # Validate files exist
    if not os.path.exists(args.old_file):
        print(_("❌ Error: File not found: {file}").format(file=args.old_file), file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.new_file):
        print(_("❌ Error: File not found: {file}").format(file=args.new_file), file=sys.stderr)
        sys.exit(1)
    
    # Compare
    result = compare_files(args.old_file, args.new_file)
    
    # Format output
    if args.format == 'json':
        output = format_json(result)
    elif args.format == 'html':
        output = format_html(result)
    else:
        output = format_text(result)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(_("📄 Report saved to: {file}").format(file=args.output))
    else:
        print(output)
    
    # Exit code: 0 if no changes, 1 if changes
    sys.exit(0 if not result.changes else 1)


if __name__ == '__main__':
    main()
