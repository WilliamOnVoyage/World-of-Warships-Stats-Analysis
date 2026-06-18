# World of Warships Stats Tracker - Product Document

## Overview
This document outlines the product requirements, features, and future milestones for the World of Warships Stats Tracker. The goal is to provide a premium, modern, and AI-native web application for viewing and analyzing player statistics.

## Milestones

### Milestone 1: Modernization & Foundation (Current)
- **Goal:** Establish a solid, modern, and AI-friendly codebase.
- **Features:**
  - Complete migration to FastAPI backend.
  - Complete migration to Next.js frontend with modern UI aesthetics (Tailwind CSS, dynamic interactions).
  - Modernized PostgreSQL database setup for storing player data.
  - Integration with the official Wargaming API using modern async Python (httpx, Pydantic).
  - Proper setup of "vibe coding" tooling (e.g., Cursor rules, linting, formatting, explicit typing).

### Milestone 2: Core Web Service & User Profiles
- **Goal:** Launch the core stats tracking features for individual players.
- **Features:**
  - Player search functionality (by username).
  - Detailed player profile page displaying overall, weekly, and monthly stats.
  - Visualizations (charts/graphs) for win rate, average damage, and survival rate over time.
  - Caching and rate-limiting for Wargaming API requests to improve performance.

### Milestone 3: Advanced Analytics & AI Integration
- **Goal:** Re-integrate machine learning and add AI features.
- **Features:**
  - Re-implementation of the LSTM prediction model into the data pipeline.
  - AI-driven "Playstyle Summaries" (e.g., using LLMs to analyze a player's ship choices and stats and write a brief narrative of their playstyle).
  - Leaderboards and top player tracking.

## Product Requirements
- **Performance:** Fast loading times on both frontend and backend.
- **Aesthetics:** "Wow factor" design—use dark mode, glassmorphism, smooth gradients, and interactive micro-animations. It should feel like a premium gaming companion app.
- **Reliability:** Graceful handling of Wargaming API rate limits and downtime.
- **AI-Native:** Codebase must strictly follow types, schemas, and documented patterns to ensure AI coding assistants (vibe coding) can easily iterate and add features.
