# The AI Operating System

## What It Is

A personal AI operating system — 175 specialized agents organized into a real company, running inside Claude Code, doing the work.

## The Problem It Actually Solves

You have access to AI. Everyone does now. The problem was never access.

The problem is that you ask an AI to do something, and it does the thing you asked, and then you have to figure out the next thing to ask. You become the bottleneck. You become the router, the project manager, the quality checker, the one holding all the context. The AI is fast. You are not.

This system removes you from the middle.

You say what you want. A Lead Orchestrator figures out which department handles it, what the risk level is, whether legal needs to review it, whether the security team should weigh in, and in what order the work should flow. Then it happens. You get the output. You make the decision. That is your only job.

## How It Works

There are 15 departments. Engineering, Product, Security, Finance, Investments, Data, DevOps, AI/ML, Strategy, Revenue, HR, Legal, Research, Prompt Engineering, Gaming Intelligence, and more. Each one has a C-suite lead, a chain of command, and specialized agents who do the actual work.

Every input you provide is classified by domain and risk tier before anyone touches it. Tier 0 is trivial — a local model handles it for free. Tier 3 means stop everything and get the CEO on the line. The system knows the difference.

There is a technical pipeline — scout, architect, builder, validator — that handles code the way a software team would. There is a MasterPlanner that produces a plan and waits for your approval before spending tokens on execution. There is a Chief Notes Officer that records everything without ever slowing anything down.

The departments talk to each other through a COO who decomposes cross-functional work. Two governance councils — one for AI risk, one for enterprise risk — sit above the departments as decision gates. Nothing high-stakes proceeds without clearing those gates.

Six compliance frameworks govern the whole thing: COSO, SOC 2, NIST CSF, SOX, COBIT, CIS. Not because compliance is fun. Because without rules, 175 agents is 175 sources of chaos.

## What Makes It Different

Most AI setups are a single prompt and a prayer. This is a company.

**It governs itself.** Every task is risk-tiered. High-risk work requires formal security review. Permission changes require council sign-off. There is an independent internal audit function that does not report to anyone it audits. These are real controls, not theater.

**It argues with itself.** The Investments department has a Contrarian-Analyst that is structurally required to run a bear case on every buy recommendation. The system is designed to disagree with itself before you have to.

**It maintains itself.** A Custodian agent audits all 175 agent prompts for drift, compresses the cache, checks for staleness, and reports what needs fixing. The system has a janitor, and the janitor has a schedule.

**It routes to free models when it can.** Tier 0 tasks go to local Ollama models running on your machine. The system does not spend API tokens on work that does not require them.

**Its marketing department is named after Vonnegut characters.** The CMO is called So-It-Goes. The writer is Montana Wildhack. The strategist is Rumfoord. This is not a gimmick. It is a commitment to writing that says something true in as few words as possible. If you cannot explain what you are selling in a short sentence, you do not understand what you are selling.

## The Infrastructure

This is not theoretical. The following Python infrastructure is built and running:

- **chain.py** — multi-agent chain executor that follows the routing logic
- **run.py** — routing loop with automatic changelog generation
- **vector_router.py** — semantic agent lookup backed by ChromaDB
- **prompt_cache.py** — hash-based caching with Anthropic API cache breakpoints
- **model_router.py** — programmatic model selection by task complexity
- **custodian.py** — maintenance CLI for prompt hygiene, cache, and memory
- **kiriko_bot.py** — Telegram bot for gaming intelligence

## Version

1.14.0. Started as a simple prompt. Now it is a company with departments, governance, compliance frameworks, an org chart, a failure museum, and a marketing team that quotes Kurt Vonnegut.

So it goes.
