# Hebbia System Design Interview Guidelines

*DRI: Sisu Xi, Status: Draft*

---

## Overview

System design interviews evaluate architectural thinking, technical depth, and collaborative problem-solving through practical system design challenges.

## Scope

| Candidate Level | Interview Required | Interviewer Level |
|---|---|---|
| P1 | - | - |
| P2 | Optional | P3+ |
| P3-P6 | ✓ | P4+ preferred |

## Interview Structure (60 minutes)

| Phase | Duration | Focus |
|---|---|---|
| Introduction | 5 min | Format and expectations |
| Problem Presentation | 5 min | Requirements and constraints |
| **Design Discussion** | **45 min** | **Architecture → Implementation → Scale** |
| - High-level design | 15 min | Components, data flow, technology choices |
| - Detailed design | 20 min | Database schema, APIs, caching strategy |
| - Scale & trade-offs | 10 min | Bottlenecks, failure modes, monitoring |
| Candidate Questions | 5 min | Role and team questions |

*Time allocations are flexible. Adjust based on discussion flow and candidate progress.*

## Evaluation Criteria

### Rating Scale

Use numeric ratings 1-4 for each dimension:
- **4 - Strong Yes**: Exceptional performance
- **3 - Yes**: Meets expectations
- **2 - No**: Below expectations
- **1 - Strong No**: Significant concerns

| Dimension | 4 - Strong Yes | 3 - Yes | 2 - No | 1 - Strong No |
|---|---|---|---|---|
| **Technical Architecture** | Elegant, scalable solutions with deep systems knowledge | Functional solutions meeting requirements | Incomplete or flawed solutions | Cannot design coherent solution |
| **Problem-Solving** | Methodical approach, insightful questions, adapts quickly | Logical progression, incorporates feedback | Disorganized, struggles with feedback | Random approach, cannot break down problems |
| **Communication** | Clear explanations with excellent visuals | Clear explanations, effective diagrams | Unclear explanations, poor visuals | Cannot explain concepts |
| **Collaboration** | Actively collaborative, demonstrates Hebbia values | Works well with interviewer | Defensive or dismissive of feedback | Closed to input |

## Level-Specific Expectations

All candidates evaluated using same criteria with level-specific calibration:

- **P2-P3**: Focus on fundamentals and clear reasoning over complex architecture
- **P4-P6**: Expect sophisticated solutions with deep distributed systems knowledge

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

## Interviewer Requirements

| Requirement | Details |
|---|---|
| **Experience** | 3+ years system design experience, distributed systems knowledge |
| **Training** | Shadow 2 interviews → Reverse shadow 1 interview |

## Best Practices

### Do's
- Create collaborative atmosphere
- Allow thinking time
- Ask probing questions ("How would this scale to 10x?")
- Observe Hebbia values
- Document reasoning process
- Provide hints when appropriate

### Don'ts
- Lead to specific solution
- Test memorization
- Rush candidate
- Create adversarial tone

## Follow-up Questions

| Area | Sample Questions |
|---|---|
| **Scale** | "How would this handle 10x traffic?" "What breaks first at scale?" |
| **Reliability** | "What happens if this component fails?" "How do you detect issues?" |
| **Trade-offs** | "Why did you choose X over Y?" "What are the downsides of this approach?" |
| **Operations** | "How would you deploy this?" "What operational concerns exist?" |

## Positive Signals & Red Flags

| Category | Positive Signals | Red Flags |
|---|---|---|
| **Technical** | Thoughtful trade-offs, considers failures, clear reasoning | Over-engineering, ignores consistency, vague technology choices |
| **Communication** | Clear explanations, logical flow, appropriate detail | Cannot explain decisions, jumps between topics, relies on buzzwords |
| **Collaboration** | Asks insightful questions, incorporates feedback, growth mindset | Works in isolation, dismisses feedback, lacks curiosity |

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|---------|
| 1.0 | 2025-09-05 | Initial creation aligned with interview process overview | Sisu Xi |
