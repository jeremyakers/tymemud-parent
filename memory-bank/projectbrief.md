# Project Brief

## Purpose
A Moment in Tyme - Wheel of Time (WoT) themed Multi-User Dungeon (MUD)

## Technology Stack
- **Language:** C (GNU11/C11 standard)
- **Engine:** Based on MikkiMud / CircleMUD
- **Database:** MySQL/MariaDB with SQL-based character persistence

## Repository Structure
- **MM3/src/** - Stable branch (`svn/MM_3_Final`) - Production, bugfixes
- **MM32/src/** - Dev branch (`svn/MM_3-2_Start`) - New features, refactoring

## Workflow
**Rule:** Fix in Stable, Merge to Dev
- Bugfixes → Implement in MM3 first
- New features → Implement in MM32
- Merging → Use `MM32/src/merge-mm32` script (MM3 → MM32 only)

## Key Constraints
- All git operations must be run from within MM3/src or MM32/src directories
- Each branch has its own MANIFESTO.md with branch-specific rules
- Never merge from MM32 to MM3
