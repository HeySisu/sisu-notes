# Product Vision Doc

## Link

[Product Vision Document](https://docs.google.com/document/d/1htufsoCIBPCykVOfgoh1MU68dfudgvzywbP89GH6EbE/preview?tab=t.0#heading=h.pcfhkulozzf9)

## Vision

Most capable AI platform.

## Key Concepts

- **Information retrieval**: find info at doc level
- **Search**: find info at chunk level within the doc
- **Limiting factors**:
  - Liebig's law of the minimum: growth rate is limited by the scarcest resource

## Pain Points (Jan 2024)

- Retrieval precision
- Retrieval recall

## What's Not the Problem

- Intelligence of model is not the limiting factor
- Amount of inference compute is not the limiting factor
- Vertical UI/UX is no longer the limiting factor

**Limiting factor**: context engineering, or information retrieval.

IR unlocks the Agentic OS-applications, APIs, agents, smarter doc editors, and more—which we will tackle, often in parallel to IR challenges, this year.

## Customer Feedback

### Normal Customers

- Ease of use, simple onboarding, agent on demand, etc.

### Power Users

- Matrix is not easily usable by a broad range of personas

### Current Users

- Juniors, the early adopters, and the back office
- Basically, folks getting from a point A to point B
- They experience the pain of **doing** it

### Target Users

- The long tail, the late adopters, the non-technical, non-repeatable workflows
- The ones who don't yet have a point A
- They are the ones who are **discovering** it
- Basically turn information into knowledge

### Immediate Feedback

- **Enterprise features**: BYOK, better security, advanced permissioning, API, etc.
- **Better workflow**: grouped row synthesis, end-to-end doc drafting, multi-user collaboration, etc.

**Note**: As a company, we will prioritize IR **prior** to investment in enterprise and workflow features.

## Company Impact

### What does IR mean

#### For Product and Engineering

- **Speed**: time to value
- **Accuracy**: returning correct documents. Pre-indexed golden answers with golden prompts

#### For Engagement

- **Upsells**: increase number of personas Hebbia can provide value for
- **Efficiency (Seats/EM)**: lighter onboarding, easy to use
- **W1 Retention**: removing the need to build matrices

#### For Design

- **Simplicity**: agent bar

#### For Marketing

- **PLG**: Product-led growth

#### For Sales

- **Value-based pricing**: read-only (search) vs. build (index/customize matrices). Read-only is perfect for free-tier
- **CAC reduction**: reduce Customer Acquisition Cost
- **Competitive differentiation**

## Strategy

### Why US (Positioning)

- DNA is an IR company
- Existing disparate products are perfect primitives for a unified IR solution
  - Browse to ingest and index
  - Matrix to show the index
  - Chat to synthesize over the retrieved context

## Differentiation (How to approach IR differently)

### Matrix Agent

- Information retrieval 3 core primitives:
  1. Keyword matching content
  2. Semantic similarity of content
  3. Metadata operations/logic

- Our IR differentiator:
  1. Producing and indexing high quality metadata
  2. Allowing for ephemeral metadata on the fly
  3. Searching over these fields with keyword and semantic search

### A Simple Analogy

- **Problem**: search over billions of docs takes forever
- **Solution**:
  1. Basic labels (genre or topic) to pre-filter the docs. So billions → 100 millions
  2. New, smarter labels created on the fly (ephemeral metadata), so 100M → 10M
  3. Keep creating new labels, so 10M → 10
  4. Read 10 docs in full, pulling related chunks, and answer the question

- **Displays in matrices**:
  - Col 1: basic labels you used (pre-indexed)
  - Col 2: smart labels you created on the fly
  - Col 3: actual chunks used for the answer

- **Others**: speed, multi-hop, multi-source, cross-source search, API sources

## Product Dev Philosophy

- Investing in the future vs. satisfying customers now
- Open to radical changes
- Connect the docs beyond the data from a limited customer base. So data matters, but reasons might matter more

### Priority Levels

- **P0**: IR mission + unlocks revenue
- **P1**: IR mission + doesn't unlock revenue
- **P2**: non-IR mission + unlocks revenue
- **P3**: non-IR mission + doesn't unlock revenue

## Roadmap

- **User story 1**: public company agent
- **User story 2**: public company watchlist (continuous IR over public data)
- **User story 3**: private company agent, auto-label documents
- **User story 4**: IR synthesis over multiple sources

**Mocks in Figma**: [User Stories 2025](https://www.figma.com/proto/wxxDWrCWCEaCv1iLmxfCOY/User-Stories-2025?node-id=4045-16495&t=16Kc4NHFSTjQytpX-1&scaling=min-zoom&content-scaling=fixed&page-id=1%3A16&starting-point-node-id=4045%3A16495&show-proto-sidebar=1)

## Links

- **Company all hands**: [Recording](https://drive.google.com/file/d/16WP64CxjFT2lUw-B3ykjCSayKdedh2jA/view)
- **Product vision**: [GTM focused](https://drive.google.com/file/d/13YIjhkru8T7C492k40IZETlGhSQErAY1/view)

## Questions

- What's our status now? What are the metrics we use to evaluate our IR?
  - How to define time to value?
  - How to define correct documents? Aka, accuracy?
  - 2nd read to create on-the-fly labels, won't that require reading the whole doc?
- What is browse?
- What are a common set of labels? Aka, taxonomy?
- What is PLG? CAC?
- Matrix Agent? What do our indexed columns look like? Embedding database? What do the rare "on the fly columns" look like?
- From the mock, user story 2 seems like a trivial feature?
