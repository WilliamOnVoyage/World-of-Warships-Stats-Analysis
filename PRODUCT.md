# World of Warships Stats Tracker - Product Document

## Overview
This document outlines the product requirements, features, and future milestones for the World of Warships Stats Tracker. The goal is to provide a premium, modern, and AI-native web application for viewing and analyzing player statistics.

## Milestones

| Milestone | Status | Goal | Features |
| :--- | :---: | :--- | :--- |
| **Milestone 1:** Modernization & Foundation | ✅ Done | Establish a solid, modern, and AI-friendly codebase. | ~~• Complete migration to FastAPI backend~~<br>~~• Complete migration to Next.js frontend with modern UI aesthetics~~<br>~~• Modernized PostgreSQL database setup~~<br>~~• Integration with official Wargaming API via async Python~~<br>~~• CI/CD and automated testing setup~~ |
| **Milestone 2:** Core Web Service & User Profiles | ✅ Done | Launch the core stats tracking features for individual players. | ~~• Player search functionality by username~~<br>~~• Detailed player profile page displaying overall stats~~<br>~~• Visualizations (charts/graphs) for Win Rate, Damage, and Battles~~<br>~~• Caching, rate-limiting, and daily snapshots to improve performance~~ |
| **Milestone 3:** Advanced Analytics & AI Integration | ⏳ Next | Re-integrate machine learning and add AI features. | • Re-implementation of the LSTM prediction model into the data pipeline.<br>• AI-driven "Playstyle Summaries" using LLMs to analyze a player's ship choices and write narratives.<br>• Leaderboards and top player tracking across the server. |

## Product Requirements
- **Performance:** Fast loading times on both frontend and backend.
- **Aesthetics:** "Wow factor" design—use dark mode, glassmorphism, smooth gradients, and interactive micro-animations. It should feel like a premium gaming companion app.
- **Reliability:** Graceful handling of Wargaming API rate limits and downtime.
- **AI-Native:** Codebase must strictly follow types, schemas, and documented patterns to ensure AI coding assistants (vibe coding) can easily iterate and add features.
