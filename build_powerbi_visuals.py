"""
Build a single professional overview page for the cricket PBIP report.

The report model contains the matches table and the following measures:
Total Matches, Total Runs, Average Runs, Most Winning Team, and
Championship Count. All visuals below use those model objects.
"""
import json
import shutil
import uuid
from pathlib import Path


REPORT_ROOT = Path(__file__).parent
PAGES_ROOT = REPORT_ROOT / "Claude Power bi.Report" / "definition" / "pages"
PAGE_NAME = "page1_overview"


def to_pbir_properties(value):
    """Convert legacy solid-value formatting into PBIR expressions."""
    if isinstance(value, dict):
        if set(value) == {"value"}:
            return {"expr": {"Literal": {"Value": value["value"]}}}
        return {key: to_pbir_properties(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_pbir_properties(item) for item in value]
    return value


def field_ref(table, field, kind="column", aggregation=None):
    """Return a legacy semantic-query field expression and query reference."""
    source = {"SourceRef": {"Entity": table}}
    if kind == "measure":
        expression = {"Measure": {"Expression": source, "Property": field}}
    elif kind == "aggregation":
        expression = {
            "Aggregation": {
                "Expression": {
                    "Column": {"Expression": source, "Property": field}
                },
                "Function": aggregation if aggregation is not None else 0,
            }
        }
    else:
        expression = {"Column": {"Expression": source, "Property": field}}
    return {
        "expression": expression,
        "queryRef": f"{table}.{field}",
        "name": f"{table}.{field}",
    }


def create_visual_container(visual_config, query, x, y, width, height, z_index):
    """Create the PBIR visual-container format consumed by Power BI Desktop."""
    single_visual = visual_config["singleVisual"]
    visual_type = {
        "card": "cardVisual",
        "barChart": "clusteredBarChart",
        "clusteredColumnChart": "clusteredBarChart",
    }.get(single_visual["visualType"], single_visual["visualType"])
    query_state = {}
    selects = {
        item.get("Name"): item
        for item in query.get("Select", [])
        if item.get("Name")
    }
    for role, projections in single_visual.get("projections", {}).items():
        pbir_role = "Data" if visual_type == "cardVisual" and role == "Values" else role
        query_state[pbir_role] = {
            "projections": [
                {
                    "field": {
                        key: value
                        for key, value in selects[projection["queryRef"]].items()
                        if key != "Name"
                    },
                    "queryRef": projection["queryRef"],
                    "nativeQueryRef": projection["queryRef"].split(".", 1)[-1],
                    "active": True,
                }
                for projection in projections
                if projection["queryRef"] in selects
            ]
        }
    visual = {"visualType": visual_type}
    if query_state:
        visual["query"] = {"queryState": query_state}
    if single_visual.get("objects"):
        visual["objects"] = to_pbir_properties(single_visual["objects"])
    if single_visual.get("vcObjects"):
        visual["visualContainerObjects"] = to_pbir_properties(
            single_visual["vcObjects"]
        )
    if visual_type not in ("textbox",):
        visual["drillFilterOtherVisuals"] = True
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json",
        "name": uuid.uuid4().hex[:20],
        "position": {
            "x": x,
            "y": y,
            "z": z_index,
            "height": height,
            "width": width,
            "tabOrder": z_index,
        },
        "visual": visual,
    }


def title_visual(text, x, y, width, height, z_index, font_size=24):
    """Create a clean page title/subtitle text box."""
    config = {
        "name": f"text_{uuid.uuid4().hex[:12]}",
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontSize": f"{font_size}pt",
                                                "fontFamily": "Segoe UI",
                                                "color": "#1F2937",
                                            },
                                        }
                                    ],
                                    "horizontalTextAlignment": "left",
                                }
                            ]
                        }
                    }
                ]
            },
        },
    }
    return create_visual_container(config, {}, x, y, width, height, z_index)


def create_card_visual(measure_name, label, x, y, width, height, z_index):
    """Create a card bound to a real model measure."""
    value = field_ref("matches", measure_name, "measure")
    config = {
        "name": f"card_{uuid.uuid4().hex[:12]}",
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": value["queryRef"]}]},
            "vcObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"solid": {"value": "true"}},
                            "text": {"solid": {"value": f"'{label}'"}},
                            "fontSize": {"solid": {"value": "12"}},
                        }
                    }
                ],
                "labels": [
                    {
                        "properties": {
                            "fontSize": {"solid": {"value": "28"}},
                            "fontFamily": {"solid": {"value": "'Segoe UI'"}},
                        }
                    }
                ],
                "categoryLabels": [
                    {"properties": {"show": {"solid": {"value": "false"}}}}
                ],
            },
        },
    }
    query = {
        "Version": 2,
        "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
        "Select": [value["expression"] | {"Name": value["name"]}],
    }
    return create_visual_container(config, query, x, y, width, height, z_index)


def create_slicer_visual(field_name, label, x, y, width, height, z_index):
    """Create a slicer bound to a matches column."""
    value = field_ref("matches", field_name)
    config = {
        "name": f"slicer_{field_name}",
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": value["queryRef"]}]},
            "vcObjects": {
                "header": [
                    {
                        "properties": {
                            "show": {"solid": {"value": "true"}},
                            "title": {"solid": {"value": f"'{label}'"}},
                        }
                    }
                ]
            },
        },
    }
    query = {
        "Version": 2,
        "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
        "Select": [value["expression"] | {"Name": value["name"]}],
    }
    return create_visual_container(config, query, x, y, width, height, z_index)


def create_chart_visual(
    chart_type, category_field, value_fields, title, x, y, width, height, z_index
):
    """Create a chart with a category column and real measures."""
    category = field_ref("matches", category_field)
    values = [field_ref("matches", name, "measure") for name in value_fields]
    value_role = "Y" if chart_type == "barChart" else "Y"
    projections = {
        "Category": [{"queryRef": category["queryRef"]}],
        value_role: [{"queryRef": value["queryRef"]} for value in values],
    }
    config = {
        "name": f"chart_{uuid.uuid4().hex[:12]}",
        "singleVisual": {
            "visualType": chart_type,
            "projections": projections,
            "vcObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"solid": {"value": "true"}},
                            "text": {"solid": {"value": f"'{title}'"}},
                            "fontSize": {"solid": {"value": "14"}},
                            "fontFamily": {"solid": {"value": "'Segoe UI'"}},
                        }
                    }
                ]
            },
        },
    }
    query = {
        "Version": 2,
        "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
        "Select": [
            category["expression"] | {"Name": category["name"]},
            *[
                value["expression"] | {"Name": value["name"]}
                for value in values
            ],
        ],
    }
    return create_visual_container(config, query, x, y, width, height, z_index)


def create_table_visual(columns, title, x, y, width, height, z_index):
    """Create a detail table using columns only (no invalid measure-as-column refs)."""
    fields = [field_ref("matches", column) for column in columns]
    config = {
        "name": f"table_{uuid.uuid4().hex[:12]}",
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {
                "Values": [{"queryRef": field["queryRef"]} for field in fields]
            },
            "vcObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"solid": {"value": "true"}},
                            "text": {"solid": {"value": f"'{title}'"}},
                            "fontSize": {"solid": {"value": "14"}},
                        }
                    }
                ]
            },
        },
    }
    query = {
        "Version": 2,
        "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
        "Select": [
            field["expression"] | {"Name": field["name"]} for field in fields
        ],
    }
    return create_visual_container(config, query, x, y, width, height, z_index)


def build_page1_overview():
    """Build one executive-style cricket overview page."""
    visuals = [
        title_visual("Cricket Match Overview", 40, 20, 1000, 46, 1000, 24),
        title_visual(
            "Use the filters to compare seasons, teams, locations, and toss choices",
            40,
            68,
            1200,
            28,
            999,
            11,
        ),
        create_slicer_visual("season", "Season", 40, 112, 430, 82, 900),
        create_slicer_visual("city", "City", 490, 112, 430, 82, 899),
        create_slicer_visual("winner", "Winning team", 940, 112, 430, 82, 898),
        create_slicer_visual(
            "toss_decision", "Toss decision", 1390, 112, 490, 82, 897
        ),
        create_card_visual("Total Matches", "Total matches", 40, 230, 430, 140, 800),
        create_card_visual("Total Runs", "Total runs won by", 490, 230, 430, 140, 799),
        create_card_visual("Average Runs", "Average winning margin", 940, 230, 430, 140, 798),
        create_card_visual(
            "Most Winning Team", "Most winning team", 1390, 230, 490, 140, 797
        ),
        create_chart_visual(
            "clusteredColumnChart",
            "season",
            ["Total Matches"],
            "Matches by season",
            40,
            410,
            600,
            300,
            700,
        ),
        create_chart_visual(
            "barChart",
            "winner",
            ["Championship Count"],
            "Winning teams",
            660,
            410,
            600,
            300,
            699,
        ),
        create_chart_visual(
            "barChart",
            "toss_decision",
            ["Total Matches"],
            "Matches by toss decision",
            1280,
            410,
            600,
            300,
            698,
        ),
        create_table_visual(
            ["season", "date", "winner", "venue", "player_of_match"],
            "Match details",
            40,
            750,
            1840,
            290,
            600,
        ),
    ]
    return visuals


def update_page_file(page_path, visuals):
    """Update page.json with the generated visual containers."""
    page_file = Path(page_path) / "page.json"
    with page_file.open("r", encoding="utf-8") as file:
        page_data = json.load(file)
    page_data["displayName"] = "Cricket Match Overview"
    page_data["displayOption"] = "FitToPage"
    page_data["height"] = 1080
    page_data["width"] = 1920
    page_data.pop("visualContainers", None)
    with page_file.open("w", encoding="utf-8") as file:
        json.dump(page_data, file, indent=2)
        file.write("\n")
    visuals_dir = Path(page_path) / "visuals"
    if visuals_dir.exists():
        shutil.rmtree(visuals_dir)
    visuals_dir.mkdir()
    for visual in visuals:
        visual_dir = visuals_dir / visual["name"]
        visual_dir.mkdir()
        with (visual_dir / "visual.json").open("w", encoding="utf-8") as file:
            json.dump(visual, file, indent=2)
            file.write("\n")
    print(f"Updated {page_file} with {len(visuals)} visuals")


def update_page_metadata():
    """Expose only the requested single page in the report navigation."""
    pages_file = PAGES_ROOT / "pages.json"
    with pages_file.open("r", encoding="utf-8") as file:
        pages_data = json.load(file)
    pages_data["pageOrder"] = [PAGE_NAME]
    pages_data["activePageName"] = PAGE_NAME
    with pages_file.open("w", encoding="utf-8") as file:
        json.dump(pages_data, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    update_page_file(PAGES_ROOT / PAGE_NAME, build_page1_overview())
    update_page_metadata()
    print("Successfully created the single-page overview report.")
