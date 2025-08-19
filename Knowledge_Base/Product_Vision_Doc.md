# Product Vision Doc

Link: 

[https://docs.google.com/document/d/1htufsoCIBPCykVOfgoh1MU68dfudgvzywbP89GH6EbE/preview?tab=t.0#heading=h.pcfhkulozzf9](https://docs.google.com/document/d/1htufsoCIBPCykVOfgoh1MU68dfudgvzywbP89GH6EbE/preview?tab=t.0#heading=h.pcfhkulozzf9)

Words:

- information retrieval: find info at doc level
- search: find info at chunk level within the doc
- limiting factors:
- libeling’s law of the minimum: growth rate is limited by the scarcest resource

Related doc listing pain points from Jan 2024:

- Retrieval precision
- Retrieval recall

What’s not the problem:

- intelligence of model is not the limiting factor;
- amount of inference computer is not the limiting factor;
- vertical UI/UX is no longer the limiting factor;

Limiting factor: context engineering, or information retrieval.

IR unlocks the Agentic OS-applications, APIs, agents, smarter doc editors, and more-which we will tackle, often in parallel to IR challenges, this year.

## Customers feedback
* normal customers: ease of use, simple onboarding, agent on demand, etc.
* power users: Matrix is not easily usable by a broad range of personas.
* users today: juniors, the early adopters, and the back office. 
  * Basically, folks getting from a point A to point B.
  * They experience the pain of **doing** it.
* Target for: the long tail, the late adopters, the non technical, non repeatable workflows. The ones who don't yet have a point A.
  * They are teh ones who are **discovering** it.
  * Basically turn information into knowledge.
* immediate feedbacks:
  * enterprise features: BYOK, better security, advanced permissioning, API, etc.
  * better workflow: grouped row synthesis, end-to-end doc drafting, multi-user collaboration, etc.
* as a company, we will prioritize IR **prior** to investment in enterprise and workflow features.

## Company 
what does IR means?
* For Producet and Engineering:
  * Speed: time to value
  * Accuracy: returning correct documents. Preindexed golden answers with golden prompts.
* For Engagement:
  * Upsells: increase number of personas Hebbia can provide value for.
  * Efficiency (Seats/EM): lighter onboarding, easy to use.
  * W1 Retention: removing the need to build matrics. 
* For Design:
  * Simplicity: agent bar.
* For Marketing:
  * PLG: 
* For Sales:
  * Value based pricing. read-only (search) vs. build (index / customize matrices). read-only is perfect for free-tier.
  * CAC reduction: reduce CAC.
  * Competitive differentiation

## Strategy
* Why US (Positioning)
  * DNA is an IR company.
  * existing disparate products are perfect primitives for a unified IR solution
    * browse to ingest and index
    * matrix to show the index
    * chat to synthesize over the retrived context

## Differentiation (How to approach IR differently)
* Matrix Agent
  * information retrieval 3 core primitives: 1) keyword matching content; 2) semantic similarity of content; 3) metadata operations / logic.
  * our IR differentiator: 1) producing and indexing high quality metadata; 2) allowing for ephemeral metadata on the fly; 3) searching over these fields with keyword and semantic search.
* A simple analogy:
  * problem: search over billions of doc. take forever.
  * solution: 
    * 1) basic lables (genre or topic) to pre-filter the doc. so billions -> 100 millions.
    * 2) new, smarter labels created on the fly (ephemeral metadata), so 100M -> 10M
    * 2.5) keep creating new labels, so 10M -> 10
    * 3) read 10 docs in full, pulling related chunks, and answer the question
  * displays in matrics:
    * col 1: basic lables you used (pre indexed)
    * col 2: smart labels you created on the fly
    * col 3: actual chunks used for the answer
* others: speed, multi-hop, multi-source, cross-source search, API sources.

## Product Dev Philosophy
* 

## Questions:
* what's our status now? what are the metrics we used to evaluate our IR?
  * how to define time to value?
  * how to define correct documents?
* what is PLG? CAC?
* Matrics Agent? what's our indexed column looks like? embedding database? what's the rare "on the fly columns" looks like?

