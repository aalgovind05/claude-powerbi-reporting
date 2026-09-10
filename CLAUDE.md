# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Power BI Project (PBIP) containing cricket match analysis data. The project uses the PBIP format, which stores Power BI artifacts as human-readable text files for version control.

## Project Structure

The repository contains one `.pbip` file: `Claude Power bi.pbip`

### Key Components

**Power BI Project File (`.pbip`)**
- Main project definition at root level
- References both Report and SemanticModel artifacts
- Auto-recovery is enabled

**SemanticModel** (`Claude Power bi.SemanticModel/`)
- Contains data model definition in TMDL format (Tabular Model Definition Language)
- `definition/tables/matches.tmdl` - Main data table with cricket match information
- `definition/relationships.tmdl` - Defines relationships between tables
- `definition/model.tmdl` - Model-level configuration
- `definition/database.tmdl` - Compatibility level settings
- Uses Power Query M for data transformations

**Report** (`Claude Power bi.Report/`)
- Report definition files in JSON format
- `definition.pbir` - Links to the semantic model
- `definition/pages/` - Contains page definitions
- `StaticResources/` - Theme files (Fluent2 theme)

## Data Source

The semantic model imports data from a local CSV file:
- Source: `C:\Users\aalgo\Downloads\matches.csv`
- Import mode (not DirectQuery)
- Contains 18 columns of cricket match data including teams, venues, results, and match officials

## Data Schema

The `matches` table contains:
- Match identifiers: id, season, date, city, venue
- Team information: team1, team2
- Toss details: toss_winner, toss_decision
- Match results: result, winner, win_by_runs, win_by_wickets, dl_applied
- Officials: umpire1, umpire2, umpire3, player_of_match

Time intelligence is enabled with an auto-generated date table linked to the `matches.date` column.

## Working with PBIP Files

Power BI Project files are designed to work with:
- **Power BI Desktop** - Open the `.pbip` file directly
- **Version Control** - All definitions are text-based (JSON/TMDL)
- **Fabric Git Integration** - Can be synced with Microsoft Fabric workspaces

### Modifying the Data Model

When editing TMDL files:
1. Table definitions are in `Claude Power bi.SemanticModel/definition/tables/*.tmdl`
2. Each table file contains columns, measures, and partition logic
3. Changes to M queries should be made in the partition source section
4. Relationships are defined separately in `relationships.tmdl`

### Updating Data Source Path

The CSV file path is hardcoded in `matches.tmdl` at line 165. To change the data source location, modify the `File.Contents()` path in the Power Query M expression.

## Model Configuration

- Compatibility Level: 1606 (SQL Server 2019/Power BI)
- Default culture: en-US
- Source query culture: en-IN
- Power BI data source version: V3
- Time intelligence: Enabled
