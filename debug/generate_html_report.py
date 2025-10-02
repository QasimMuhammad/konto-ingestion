#!/usr/bin/env python3
"""
Generate HTML report for Silver layer data visualization.
Creates an interactive web page to explore the processed legal sections.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.utils import log


def generate_html_report(
    silver_file: Path, output_file: Path, sample_size: int = 100
) -> None:
    """Generate an HTML report for Silver data visualization."""

    # Load data
    with open(silver_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Sample data for performance
    sample_data = data[:sample_size] if len(data) > sample_size else data

    # Generate statistics
    domains = Counter(section.get("domain", "unknown") for section in data)
    source_types = Counter(section.get("source_type", "unknown") for section in data)
    publishers = Counter(section.get("publisher", "unknown") for section in data)

    # Calculate token stats
    token_counts = [section.get("token_count", 0) for section in data]
    total_tokens = sum(token_counts)
    avg_tokens = total_tokens / len(data) if data else 0

    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Silver Layer Data Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .section-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            background: #fafafa;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .section-id {{
            font-weight: bold;
            color: #007bff;
        }}
        .section-meta {{
            font-size: 0.9em;
            color: #666;
        }}
        .section-text {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border-left: 3px solid #28a745;
            max-height: 200px;
            overflow-y: auto;
        }}
        .tag {{
            display: inline-block;
            background: #e9ecef;
            color: #495057;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }}
        .domain-tax {{ background: #d4edda; color: #155724; }}
        .domain-accounting {{ background: #cce5ff; color: #004085; }}
        .domain-reporting {{ background: #fff3cd; color: #856404; }}
        .domain-unknown {{ background: #f8d7da; color: #721c24; }}
        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .search-box {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Silver Layer Data Report</h1>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{len(data):,}</div>
                <div class="stat-label">Total Sections</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_tokens:,}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{avg_tokens:.0f}</div>
                <div class="stat-label">Avg Tokens/Section</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(domains)}</div>
                <div class="stat-label">Domains</div>
            </div>
        </div>
        
        <h2>📈 Data Distribution</h2>
        <div class="chart-container">
            <h3>By Domain</h3>
            {_generate_domain_chart(domains)}
            
            <h3>By Source Type</h3>
            {_generate_source_type_chart(source_types)}
            
            <h3>By Publisher</h3>
            {_generate_publisher_chart(publishers)}
        </div>
        
        <h2>🔍 Sample Sections</h2>
        <input type="text" class="search-box" placeholder="Search sections..." id="searchBox" onkeyup="filterSections()">
        
        <div id="sections">
            {_generate_sections_html(sample_data)}
        </div>
    </div>
    
    <script>
        function filterSections() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const sections = document.querySelectorAll('.section-card');
            
            sections.forEach(section => {{
                const text = section.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    section.classList.remove('hidden');
                }} else {{
                    section.classList.add('hidden');
                }}
            }});
        }}
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    log.info(f"Generated HTML report: {output_file}")


def _generate_domain_chart(domains: Counter) -> str:
    """Generate HTML for domain distribution chart."""
    total = sum(domains.values())
    html = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>"

    for domain, count in domains.most_common():
        percentage = (count / total) * 100
        html += f"""
        <div style="flex: 1; min-width: 200px; background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span class="tag domain-{domain}">{domain}</span>
                <span style="font-weight: bold;">{count:,}</span>
            </div>
            <div style="background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: #007bff; height: 100%; width: {percentage}%;"></div>
            </div>
            <div style="font-size: 0.8em; color: #666; margin-top: 5px;">{percentage:.1f}%</div>
        </div>
        """

    html += "</div>"
    return html


def _generate_source_type_chart(source_types: Counter) -> str:
    """Generate HTML for source type distribution chart."""
    total = sum(source_types.values())
    html = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>"

    for stype, count in source_types.most_common():
        percentage = (count / total) * 100
        html += f"""
        <div style="flex: 1; min-width: 150px; background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{stype}</span>
                <span style="font-weight: bold;">{count:,}</span>
            </div>
            <div style="background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: #28a745; height: 100%; width: {percentage}%;"></div>
            </div>
            <div style="font-size: 0.8em; color: #666; margin-top: 5px;">{percentage:.1f}%</div>
        </div>
        """

    html += "</div>"
    return html


def _generate_publisher_chart(publishers: Counter) -> str:
    """Generate HTML for publisher distribution chart."""
    total = sum(publishers.values())
    html = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>"

    for publisher, count in publishers.most_common():
        percentage = (count / total) * 100
        html += f"""
        <div style="flex: 1; min-width: 150px; background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{publisher}</span>
                <span style="font-weight: bold;">{count:,}</span>
            </div>
            <div style="background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: #ffc107; height: 100%; width: {percentage}%;"></div>
            </div>
            <div style="font-size: 0.8em; color: #666; margin-top: 5px;">{percentage:.1f}%</div>
        </div>
        """

    html += "</div>"
    return html


def _generate_sections_html(sections: List[Dict[str, Any]]) -> str:
    """Generate HTML for sections display."""
    html = ""

    for i, section in enumerate(sections):
        domain = section.get("domain", "unknown")
        text_preview = (
            section.get("text_plain", "")[:300] + "..."
            if len(section.get("text_plain", "")) > 300
            else section.get("text_plain", "")
        )

        html += f"""
        <div class="section-card">
            <div class="section-header">
                <div>
                    <span class="section-id">{section.get("section_id", "N/A")}</span>
                    <span class="tag domain-{domain}">{domain}</span>
                    <span class="tag">{section.get("source_type", "N/A")}</span>
                </div>
                <div class="section-meta">
                    {section.get("token_count", 0)} tokens | {section.get("publisher", "N/A")}
                </div>
            </div>
            
            <div><strong>Path:</strong> {section.get("path", "N/A")}</div>
            <div><strong>Heading:</strong> {section.get("heading", "N/A")}</div>
            <div><strong>Law ID:</strong> {section.get("law_id", "N/A")}</div>
            
            <div class="section-text">
                {text_preview}
            </div>
        </div>
        """

    return html


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Generate HTML report for Silver data")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("data/silver/law_sections.json"),
        help="Input Silver JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("debug/silver_report.html"),
        help="Output HTML file",
    )
    parser.add_argument(
        "--sample-size",
        "-s",
        type=int,
        default=100,
        help="Number of sections to include in sample",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file {args.input} not found")
        sys.exit(1)

    generate_html_report(args.input, args.output, args.sample_size)


if __name__ == "__main__":
    main()
