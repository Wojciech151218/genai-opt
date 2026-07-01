# Development Process Guide

## Purpose

This document defines the development workflow for this project.

The goal is to maintain:
- Professional open-source development practices
- Good academic integrity
- Clear collaboration between team members
- A maintainable and documented codebase

---

# 1. Project Development Philosophy

This project is developed as both:

1. A software engineering project
2. An academic assignment

Therefore, we care about:

- Working software
- Code quality
- Documentation
- Testing
- Transparent development history
- Proper attribution of external resources
- Responsible use of AI tools

The objective is not to build every possible feature, but to create a useful, reliable, and well-engineered first release.

---

# 2. Development Stages

## Stage 1 — Planning

Before writing code:

Define:

- The problem being solved
- Target users
- Project scope
- Main features
- Limitations

Create:

- Requirements document
- Initial project structure
- Task breakdown

Example:

Problem:
> Create a Python library that solves a specific developer problem.

Requirements:

Functional:
- Feature A works
- Feature B works

Non-functional:
- Python 3.x support
- Tests included
- Documentation provided

---

# Stage 2 — Prototype

The prototype phase is for experimentation.

Goals:

- Test ideas quickly
- Discover technical challenges
- Validate the concept

Rules:

- Code does not need to be perfect
- Throw away bad approaches
- Do not build unnecessary features

The prototype should eventually become the foundation of the real library.

---

# Stage 3 — Library Development

Convert the prototype into a proper package.

Recommended structure:

project/

    src/
        library_name/
            __init__.py
            module1.py
            module2.py

    tests/

    docs/

    README.md
    LICENSE
    CHANGELOG.md
    DEVELOPMENT_LOG.md
    pyproject.toml

---

# 3. Git Workflow

## Main Branch

`main` always contains:

- Working code
- Tested features
- Release-ready versions

Do not directly commit to main.

---

# Branching

Each feature gets its own branch.

Example:

feature/parser

feature/testing

feature/documentation


Create a branch:

git checkout -b feature/parser


---

# Commits

Commits should represent one logical change.

Good:

- Add parser implementation
- Fix validation bug
- Add unit tests
- Improve documentation


Bad:

- Update
- Stuff
- Changes
- Final version

---

# Pull Requests

All changes enter main through pull requests.

Every PR should include:

## Description

What changed?

Why was it needed?

How can it be tested?


## Checklist

- [ ] Code works
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No unnecessary dependencies
- [ ] Code reviewed by another member

---

# Code Review

Reviewers should check:

## Correctness

Does it work?

## Maintainability

Is it understandable?

## Design

Does it fit the project architecture?

## Testing

Are important cases covered?

## Security

Are there obvious risks?

---

# 4. Testing Process

Tests are required for important functionality.

Tests should cover:

- Normal usage
- Invalid input
- Edge cases
- Previously fixed bugs

Example:

If a bug is fixed:

1. Add a test reproducing it
2. Fix the code
3. Ensure the test passes

---

# 5. Documentation

Documentation is part of the project.

Required files:

## README.md

For users.

Contains:

- Project description
- Installation
- Usage examples
- Basic API explanation


## CHANGELOG.md

For users.

Contains:

- Released changes
- New features
- Bug fixes


Example:

## [0.2.0]

Added:
- New parser feature

Fixed:
- Input validation issue


## DEVELOPMENT_LOG.md

For developers and academic evaluation.

Contains:

- Development history
- Decisions
- Problems
- Solutions

Example entry:

Date:
2026-07-01

Goal:
Implement parser module

Completed:
Created tokenizer and tests

Problem:
Original design mixed parsing and validation

Solution:
Separated responsibilities into different modules

---

# 6. Versioning

Use semantic versioning.

Format:

MAJOR.MINOR.PATCH


Example:

0.1.0

First public version


0.2.0

New features


0.2.1

Bug fixes


1.0.0

Stable release


---

# 7. Open Source Practices

The project should include:

## LICENSE

Defines how others can use the code.

Common choices:

- MIT
- Apache-2.0
- GPL


## CONTRIBUTING.md

Explains:

- How to report bugs
- How to propose features
- How to submit changes


## Issue Tracking

Tasks should be recorded as issues.

Example:

Title:
Add configuration support

Description:
Implement configuration loading.

Acceptance criteria:

- Configuration file loads
- Invalid files produce errors
- Tests included

---

# 8. Academic Integrity Rules

This project must represent the team's work.

## External Resources

If using:

- Articles
- Tutorials
- Algorithms
- Code examples
- Libraries

Document them.

Do not copy code without understanding or attribution.

---

# 9. AI Tool Usage

AI tools may be used as development assistants.

Allowed uses:

- Explaining concepts
- Suggesting solutions
- Helping debug
- Generating examples
- Improving documentation

Generated code must be:

- Reviewed
- Understood
- Tested
- Modified if necessary


Do not:

- Generate the entire project and submit it
- Use code nobody understands
- Hide AI-generated contributions

---

# AI Usage Log

Keep a record of significant AI assistance.

Example:

Date:
2026-07-01

Tool:
AI assistant

Used for:
Understanding pytest fixtures

Result:
Implemented tests manually after reviewing suggestions

---

# 10. Team Responsibilities

Each member should:

- Own assigned tasks
- Review others' code
- Communicate blockers
- Update documentation
- Maintain quality


Possible roles:

Developer:
- Implements features

Tester:
- Maintains tests

Documentation:
- Maintains guides

Release manager:
- Handles versions/releases


Roles may rotate.

---

# 11. Release Process

Before releasing:

Check:

- Tests pass
- Documentation updated
- Changelog updated
- Version increased
- Code reviewed


Create release:

Version tag:

v0.1.0


---

# 12. Final Project Evaluation Criteria

The project should demonstrate:

## Technical Quality

- Clean architecture
- Working features
- Good testing

## Engineering Process

- Git history
- Reviews
- Issue tracking
- Documentation

## Academic Quality

- Original work
- Proper citations
- Transparent AI usage

---

# Summary

Our workflow:

Plan
→ Prototype
→ Implement
→ Test
→ Review
→ Document
→ Release
→ Improve

A successful project is not only code that works, but code that can be understood, maintained, and trusted.