# MCP Tooling Guide

This is the canonical detailed reference for MCP-tool selection in this repo.

## Purpose

Use this guide for operational questions such as:

- which MCP to use for a given task
- how to scope MCP queries correctly
- what to do when an MCP call fails or returns weak results

## General Selection Rules

- **grepai**: semantic code search, call tracing, repo exploration
- **tymemud-builder**: project-specific builder/editor/world-data operations
- **context7**: external library/framework documentation
- **other remote MCPs**: external-reference or service-specific lookups

## grepai MCP Guidance

Use grepai MCP tools when you need semantic understanding of the local codebase.

Important practices:

- set the correct `workspace`
- narrow to the correct `project` when possible
- use the tightest practical `path`
- prefer semantic search for intent questions
- prefer exact-match tools when the query is an exact string/pattern question

## tymemud-builder MCP Guidance

Use `tymemud-builder_*` tools for project-specific builderport/editor operations rather than trying to simulate those flows through unrelated shell commands.

Use it for:

- builderport-backed reads/writes
- world/editor data operations
- project-specific structured operations already exposed by the MCP

## context7 Guidance

Use `context7` when the question is about external package/framework behavior and you need current docs rather than local repo search.

## Failure Handling

If an MCP tool call fails:

1. report the failure clearly
2. check whether scope/parameters are wrong
3. retry with narrower or corrected arguments
4. only then fall back to another tool path

Do not silently abandon MCP because the first call was weak.

## Local vs Remote MCPs

- Local MCPs depend on the current project/worktree and are sensitive to path/scope selection.
- Remote MCPs are usually for documentation or external services and are less tied to local repo layout.
