"""Output formatters for reading lists."""

import json
from typing import List, Dict, Any, Optional


class MarkdownFormatter:
    """Format reading list as Markdown checklist."""

    def format(
        self,
        name: str,
        description: str,
        items: List[Dict[str, Any]],
    ) -> str:
        """Format items as Markdown checklist.

        Args:
            name: List name
            description: List description
            items: List of matched items with keys: title, url, confidence, note

        Returns:
            Markdown formatted string
        """
        lines = []

        # Header
        lines.append(f"# {name}")
        lines.append("")

        if description:
            lines.append(description)
            lines.append("")

        lines.append("## Checklist")
        lines.append("")

        # Items
        for item in items:
            title = item["title"]
            url = item.get("url")
            note = item.get("note", "")

            if url:
                # Linked item
                line = f"- [ ] [{title}]({url})"
            else:
                # Missing URL
                line = f"- [ ] {title}  **(URL not found)**"

            if note:
                line += f" — {note}"

            lines.append(line)

        # Footer with stats
        lines.append("")
        lines.append("---")

        total = len(items)
        found = sum(1 for i in items if i.get("url"))
        missing = total - found

        lines.append(f"Total: {total}")
        if missing > 0:
            lines.append(f"Missing URLs: {missing}")

        return "\n".join(lines)


class JSONFormatter:
    """Format reading list as JSON."""

    def format(
        self,
        name: str,
        description: str,
        items: List[Dict[str, Any]],
    ) -> str:
        """Format items as JSON.

        Args:
            name: List name
            description: List description
            items: List of matched items

        Returns:
            JSON formatted string
        """
        output = {
            "name": name,
            "description": description,
            "total": len(items),
            "found": sum(1 for i in items if i.get("url")),
            "missing": sum(1 for i in items if not i.get("url")),
            "items": [
                {
                    "title": item["title"],
                    "url": item.get("url"),
                    "confidence": item.get("confidence", 0.0),
                    "note": item.get("note", ""),
                    "found": item.get("url") is not None,
                }
                for item in items
            ],
        }

        return json.dumps(output, indent=2, ensure_ascii=False)
