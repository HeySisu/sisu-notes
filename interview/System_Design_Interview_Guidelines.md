# Hebbia System Design Interview Guidelines

*DRI: Sisu Xi, Status: Draft*

---

## Overview

System design interviews evaluate candidates' ability to architect scalable, maintainable systems while demonstrating technical depth, problem-solving skills, and collaborative communication.

## Scope

| Candidate Level | Interview Required | Interviewer Level |
|---|---|---|
| P1 | ❌ Not recommended | - |
| P2 | 🔄 Optional (manager discretion) | P3+ |
| P3+ | ✅ Required | P4+ preferred |

## Interview Structure (60 minutes) - Recommended

| Phase | Duration | Focus |
|---|---|---|
| Introduction | 5 min | Rapport, format overview |
| Problem Presentation | 5 min | Requirements, constraints, Q&A |
| **Deep Dive Discussion** | **45 min** | **Architecture → Details → Scale** |
| - High-level design | 15 min | Components, data flow, tech stack |
| - Detailed design | 20 min | Database, APIs, caching |
| - Scale & trade-offs | 10 min | Bottlenecks, failures, monitoring |
| Candidate Questions | 5 min | Role/company questions |

*Note: These time allocations are recommendations. Adjust based on candidate progress and natural conversation flow.*

## Evaluation Criteria

### Rating Scale

| Dimension | Strong Yes | Yes | No | Strong No |
|---|---|---|---|---|
| **Technical Architecture** | Elegant, scalable solutions with deep systems knowledge | Functional solutions meeting requirements | Incomplete/flawed solutions | Cannot design coherent solution |
| **Problem-Solving** | Methodical approach, insightful questions, adapts quickly | Logical progression, incorporates feedback | Disorganized, struggles with feedback | Random approach, cannot break down problems |
| **Communication** | Crystal clear explanations, excellent visuals | Clear explanations, effective diagrams | Unclear explanations, poor visuals | Cannot explain concepts clearly |
| **Collaboration** | Genuinely collaborative, shows Hebbia values | Works well in team setting | Defensive, dismissive of feedback | Hostile, completely closed to input |

## Level-Specific Expectations

**All candidates should be evaluated using the same criteria and rating scale.** However, during hiring discussions and final decisions, we can apply different expectations:

- **P2-P3**: Can be more lenient on system complexity. Strong fundamentals and clear reasoning may outweigh simpler architectural solutions
- **P4-P6**: Expect sophisticated solutions with deep systems thinking. Less tolerance for gaps in distributed systems knowledge

## Question Bank

TODO: Add specific system design questions as separate markdown files. Each question should include:

- **Question requirements** (copy/paste ready for interviewer)
- **Target level and focus areas**
- **Example solutions and architectures**
- **Recommended follow-up questions**
- **Question-specific evaluation criteria** (if applicable)

### Deep Dive Areas
- **Database**: Schema design, indexing, optimization
- **Security**: Auth, encryption, threat modeling
- **Monitoring**: Metrics, logging, distributed tracing
- **Performance**: Load testing, bottlenecks, optimization

## Interviewer Qualifications & Training

| Requirement | Details |
|---|---|
| **Experience** | 3+ years system design experience, distributed systems knowledge |
| **Training** | Shadow 2 interviews → Reverse shadow 1 interview |

## Best Practices

### Do's
- ✅ Create welcoming, collaborative atmosphere
- ✅ Give candidates time to think - comfortable silences are OK
- ✅ Ask follow-up questions for depth ("How would this scale to 10x?")
- ✅ Watch for Hebbia values in action
- ✅ Take detailed notes on reasoning and thought process
- ✅ Provide hints if needed - we want to see their best work

### Don'ts
- ❌ Lead candidate to specific solution
- ❌ Focus on memorized knowledge over reasoning
- ❌ Rush through sections - depth > coverage
- ❌ Make it adversarial or try to "stump" them

## Example Follow-up Questions for Depth

| Area | Sample Questions |
|---|---|
| **Scale** | "How would this handle 10x traffic?" "What breaks first at scale?" |
| **Reliability** | "What happens if this component fails?" "How do you detect issues?" |
| **Trade-offs** | "Why did you choose X over Y?" "What are the downsides of this approach?" |
| **Real-world** | "How would you deploy this?" "What operational concerns exist?" |

## Positive Signals & Red Flags

| Category | ✅ Positive Signals | 🚩 Red Flags |
|---|---|---|
| **Technical** | Thoughtful trade-offs, considers failures, explains reasoning | Over-engineering, ignores consistency, vague tech choices |
| **Communication** | Clear explanations, logical progression, appropriate detail | Cannot explain decisions, jumps topics, uses buzzwords |
| **Collaboration** | Asks insightful questions, adapts to feedback, shows growth mindset | Works in isolation, dismisses feedback, no curiosity |

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|---------|
| 1.0 | 2025-01-27 | Initial creation | Sisu Xi |
