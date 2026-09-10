"""
Power BI Report Page Builder
Creates visual definitions for PBIP format
"""
import json
import uuid
from pathlib import Path

def create_visual_container(visual_type, x, y, width, height, z_index, config):
    """Create a visual container with proper Power BI structure"""
    container_id = str(uuid.uuid4())

    return {
        "x": x,
        "y": y,
        "z": z_index,
        "width": width,
        "height": height,
        "config": json.dumps(config),
        "filters": "[]",
        "query": json.dumps({
            "Commands": [{
                "SemanticQueryDataShapeCommand": {
                    "Query": config.get("query", {}),
                    "Binding": config.get("binding", {})
                }
            }]
        })
    }

def create_card_visual(measure_name, x, y, width, height, z_index):
    """Create a KPI card visual"""
    config = {
        "name": f"card_{measure_name.replace(' ', '_').lower()}",
        "singleVisual": {
            "visualType": "card",
            "projections": {
                "Values": [{
                    "queryRef": f"matches.{measure_name}"
                }]
            },
            "vcObjects": {
                "labels": [{
                    "properties": {
                        "fontSize": {"solid": {"value": "48"}},
                        "fontFamily": {"solid": {"value": "'Segoe UI'"}}
                    }
                }],
                "categoryLabels": [{
                    "properties": {
                        "show": {"solid": {"value": "true"}},
                        "fontSize": {"solid": {"value": "14"}}
                    }
                }]
            }
        },
        "query": {
            "Version": 2,
            "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
            "Select": [{
                "Measure": {
                    "Expression": {"SourceRef": {"Source": "m"}},
                    "Property": measure_name
                },
                "Name": f"matches.{measure_name}"
            }]
        }
    }

    return create_visual_container("card", x, y, width, height, z_index, config)

def create_slicer_visual(field_name, label, x, y, width, height, z_index, mode="Basic"):
    """Create a slicer visual"""
    config = {
        "name": f"slicer_{field_name}",
        "singleVisual": {
            "visualType": "slicer",
            "projections": {
                "Values": [{
                    "queryRef": f"matches.{field_name}"
                }]
            },
            "vcObjects": {
                "data": [{
                    "properties": {
                        "mode": {"solid": {"value": f"'{mode}'"}}
                    }
                }],
                "header": [{
                    "properties": {
                        "show": {"solid": {"value": "true"}},
                        "title": {"solid": {"value": f"'{label}'"}}
                    }
                }]
            }
        },
        "query": {
            "Version": 2,
            "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
            "Select": [{
                "Column": {
                    "Expression": {"SourceRef": {"Source": "m"}},
                    "Property": field_name
                },
                "Name": f"matches.{field_name}"
            }]
        }
    }

    return create_visual_container("slicer", x, y, width, height, z_index, config)

def create_chart_visual(chart_type, category_field, value_fields, title, x, y, width, height, z_index):
    """Create a chart visual"""

    projections = {
        "Category": [{
            "queryRef": f"matches.{category_field}"
        }]
    }

    if chart_type in ["clusteredColumnChart", "barChart"]:
        projections["Y"] = [{"queryRef": f"matches.{vf}"} for vf in value_fields]
    elif chart_type == "pieChart":
        projections["Values"] = [{"queryRef": f"matches.{vf}"} for vf in value_fields]

    config = {
        "name": f"chart_{title.replace(' ', '_').lower()}",
        "singleVisual": {
            "visualType": chart_type,
            "projections": projections,
            "vcObjects": {
                "title": [{
                    "properties": {
                        "show": {"solid": {"value": "true"}},
                        "text": {"solid": {"value": f"'{title}'"}},
                        "fontSize": {"solid": {"value": "14"}},
                        "fontFamily": {"solid": {"value": "'Segoe UI'"}}
                    }
                }]
            }
        },
        "query": {
            "Version": 2,
            "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
            "Select": [
                {
                    "Column": {
                        "Expression": {"SourceRef": {"Source": "m"}},
                        "Property": category_field
                    },
                    "Name": f"matches.{category_field}"
                }
            ] + [
                {
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "m"}},
                        "Property": vf
                    },
                    "Name": f"matches.{vf}"
                } for vf in value_fields
            ]
        }
    }

    return create_visual_container(chart_type, x, y, width, height, z_index, config)

def create_table_visual(columns, title, x, y, width, height, z_index):
    """Create a table visual"""
    config = {
        "name": f"table_{title.replace(' ', '_').lower()}",
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {
                "Values": [{"queryRef": f"matches.{col}"} for col in columns]
            },
            "vcObjects": {
                "title": [{
                    "properties": {
                        "show": {"solid": {"value": "true"}},
                        "text": {"solid": {"value": f"'{title}'"}},
                        "fontSize": {"solid": {"value": "14"}}
                    }
                }],
                "grid": [{
                    "properties": {
                        "gridVertical": {"solid": {"value": "true"}},
                        "gridHorizontal": {"solid": {"value": "true"}}
                    }
                }]
            }
        },
        "query": {
            "Version": 2,
            "From": [{"Name": "m", "Entity": "matches", "Type": 0}],
            "Select": [{
                "Column": {
                    "Expression": {"SourceRef": {"Source": "m"}},
                    "Property": col
                },
                "Name": f"matches.{col}"
            } for col in columns]
        }
    }

    return create_visual_container("tableEx", x, y, width, height, z_index, config)

def build_page1_overview():
    """Build Match Overview page"""
    visuals = []

    # Slicers
    visuals.append(create_slicer_visual("season", "Season", 40, 120, 250, 150, 900))
    visuals.append(create_slicer_visual("city", "City", 310, 120, 250, 150, 899, "Dropdown"))
    visuals.append(create_slicer_visual("winner", "Team", 580, 120, 250, 150, 898, "Dropdown"))

    # KPI Cards
    visuals.append(create_card_visual("Total Matches", 40, 300, 350, 180, 800))
    visuals.append(create_card_visual("Total Runs", 410, 300, 350, 180, 799))
    visuals.append(create_card_visual("Average Runs", 780, 300, 350, 180, 798))

    # Charts
    visuals.append(create_chart_visual("clusteredColumnChart", "season", ["Total Matches"],
                                      "Matches by Season", 40, 510, 550, 520, 700))
    visuals.append(create_chart_visual("barChart", "winner", ["Championship Count"],
                                      "Top Winning Teams", 610, 510, 550, 520, 699))

    # Table
    visuals.append(create_table_visual(["season", "winner", "Total Matches", "venue"],
                                      "Match Details", 1180, 300, 700, 730, 650))

    return visuals

def build_page2_performance():
    """Build Team Performance page"""
    visuals = []

    # Slicers
    visuals.append(create_slicer_visual("winner", "Select Team", 40, 120, 280, 150, 900, "Dropdown"))
    visuals.append(create_slicer_visual("venue", "Venue", 340, 120, 280, 150, 899, "Dropdown"))
    visuals.append(create_slicer_visual("toss_decision", "Toss Decision", 640, 120, 280, 150, 898, "Dropdown"))

    # KPI Cards
    visuals.append(create_card_visual("Championship Count", 40, 300, 420, 180, 800))
    visuals.append(create_card_visual("Most Winning Team", 480, 300, 420, 180, 799))

    # Charts
    visuals.append(create_chart_visual("clusteredColumnChart", "winner", ["Total Runs", "win_by_wickets"],
                                      "Win Margins by Team", 40, 510, 550, 520, 700))
    visuals.append(create_chart_visual("pieChart", "toss_decision", ["Total Matches"],
                                      "Toss Decision Impact", 610, 510, 550, 520, 699))
    visuals.append(create_chart_visual("barChart", "venue", ["Total Matches"],
                                      "Top 10 Venues", 1180, 300, 700, 380, 650))

    # Table
    visuals.append(create_table_visual(["player_of_match", "Total Matches"],
                                      "Top Players", 1180, 700, 700, 330, 649))

    return visuals

def update_page_file(page_path, visuals):
    """Update page.json file with visual containers"""
    page_file = Path(page_path) / "page.json"

    with open(page_file, 'r') as f:
        page_data = json.load(f)

    page_data["visualContainers"] = visuals

    with open(page_file, 'w') as f:
        json.dump(page_data, f, indent=2)

    print(f"Updated {page_file} with {len(visuals)} visuals")

if __name__ == "__main__":
    base_path = Path(r"Claude Power bi.Report\definition\pages")

    # Build Page 1
    page1_visuals = build_page1_overview()
    update_page_file(base_path / "page1_overview", page1_visuals)

    # Build Page 2
    page2_visuals = build_page2_performance()
    update_page_file(base_path / "page2_performance", page2_visuals)

    print("Successfully created visual definitions for both pages!")
