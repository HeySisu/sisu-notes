# Hebbia Engineering Guidelines

Got feedback? Submit it here!

## Individual Contributors

### Scope of Influence

| Level | Scope |
|-------|-------|
| P1 | Self & collaborate with peers |
| P2 | Team |
| P3 | Team + X-Fn |
| P4 | Team + X-Fn + Lead other eng |
| P5 | Cross-team |
| P6 | All Engineering + Industry |

---

## Performance

### Technical Execution - Software Engineering

Write clean code with increasing independence

#### P1 - Software Engineer I

Owns and delivers ticket-level work with guidance.

Writes high-quality, maintainable code that follows existing style guides, heavily leaning on direction from more senior team members and manager.

Solid programmer: technical changes are readable and the intended behavior is clear.

Reviews others' code of low complexity, or medium complexity with guidance. Uses source control, code review, testing, and other tools with minimal guidance.

Strong focus on improvement, becoming more independent across all areas. Still learning best practices and conventions for their squad's language/framework.

#### P2 - Software Engineer II

Drives multi-week projects autonomously, from technical design through successful production adoption

Strong programmer: ships correct and clean code, following best practices with minimal guidance. Breaks commits into appropriately-sized pieces with guidance. An active participant in code reviews.

Operates outside the bound of a sprint, planning execution multiple sprints into the future, and setting clear delivery expectations

Strives to take on new challenges, seeking opportunities to scale their impact

#### P3 - Senior Engineer

Independently writes modular, maintainable code that is easily testable and understandable by other developers. Fluently follows existing best practices for writing and testing code. Solves hard problems and commits code daily.

Provides detailed code reviews for teammates and helps document idioms and best practices.

Improves readability, maintainability, or performance of code they touch, even outside assigned scope.

Navigates multiple subdomains independently and incorporates business context into technical decisions

Shapes team implementation through ERD and code review feedback

Leads execution of a medium-complexity projects with another engineering within the team, starting at ideation through a safe, coordinated rollout

#### P4 - Staff Engineer

Applies learnings from relevant industry trends to improve team practices or system design.

Is a proven team subject matter expert, both within the team and across the organization

Leads execution of a complex project with multiple other engineers within the team, starting at ideation through a safe, coordinated rollout

#### P5 - Senior Staff Engineer

P5+ are built on P4 technical execution across continuously larger projects

#### P6 - Principal Engineer

P4+ are built on P3 technical execution across continuously larger projects

---

### Software Architecture & Design

Ensure well-designed systems that scale

#### P1 - Software Engineer I

Designs components with an awareness of overall architecture, avoiding duplication across codebases and interface-breaking changes.

Needs the solution design, project expectations, and other software requirements to be well-defined by more senior engineers.

Starts understanding domain-level concerns around the codebase that they work with.

Reads all technical documents produced by their team.

#### P2 - Software Engineer II

Owns design of entire features at the class/module level, ensuring they fit well within the system design.

Code is modular and maintainable, following architectural design guidance from more senior engineers.

Develops sufficient domain understanding to sanity check and ensure the quality of their output.

Thoughtful reviewer of team members' technical designs.

Specializes in a component of the team's codebase as the SME

#### P3 - Senior Engineer

Active contributor in one or more systems. Technical owner of one or more non-critical systems.

Designs features and systems that demonstrate sound abstraction boundaries, sensible layering, and attention to scalability and extensibility.

Independently drives team consensus around tradeoffs, advocating for maintainable and performant system designs.

Begins to define new reusable patterns (not just follow existing ones), making tradeoffs that balance performance, readability, and future growth.

Develops deep understanding of systems near their projects and proactively expands expertise across the team's codebase.

Demonstrates fluency in their team's architecture architecture, and anticipates downstream effects of design decisions on adjacent systems or future features.

Collaborates effectively with adjacent teams and stakeholders while maintaining focus on core project delivery.

#### P4 - Staff Engineer

An expert in their squad's domain; has detailed knowledge of team's architecture and technologies and a high-level understanding of coupled peer teams. Incorporates domain knowledge into technical decisions with the product in mind and starts lending their expertise to others.

Owns architecture, quality, and long-term health of mulitples systems, with clear mechanisms to detect and prevent regressions.

Designs and delivers technically significant system improvements with moderate ambiguity and multiple constraints.

Improves team designs by identifying risks and recommending simplifications, reuse, or security improvements during design review.

Regularly defines new abstractions or refactors existing ones to simplify future development.

Drives adoption of improved design patterns or practices across multiple projects.

#### P5 - Senior Staff Engineer

Designs systems that solve problems of high technical complexity, or replaces existing technology with simpler and/or more robust alternatives.

Designs for scale and reliability across multiple squads, anticipating future technical challenges. Explores alternatives and makes well-reasoned technical tradeoffs, including cost-benefit analyses of new technologies. Helps create alignment around our architectural and design principles/vision across multiple squads to strategically tackle technical debt.

Elevates peer designs through deep, constructive feedback and proactively redirects unproductive technical approaches.

Acts as an expert in their domain area. Understands and maps dependencies from adjacent domains. Serves as a partner to product.

Excels at defining the vision for and design of large business-impacting projects with multiple constraints

Owns architectural documentation and design reviews for key systems that support multiple teams.

Owns the full lifecycle of critical systems: design, stability, long-term evolution

Owns the architecture and delivery of cross-cutting features that span multiple systems or teams.

#### P6 - Principal Engineer

Drives the architectural quality bar across org-wide systems by setting standards, coaching staff engineers, and resolving complex tradeoffs.

Defines and evangelizes architectural vision to scale product and platform. Designs systems that shift technical direction of core infrastructure

Deconstructs monoliths or entangled systems into modular components with team ownership boundaries

Designs the next generation of our most critical systems—high ambiguity, high complexity work that shapes the platform for years.

Partners with senior leadership to align org-wide technical strategy with business goals, ensuring the long-term health of EPD systems and teams.

Establishes organization-wide architectural standards and ensures adoption through influence, not authority.

---

## Quality Focus

### Execution & Quality

Testing, production and operational awareness

#### P1 - Software Engineer I

Writes code with testability, readability, edge cases, and errors in mind, with guidance from senior engineers. Maintains comprehensive unit test coverage and data quality assertions with guidance through code reviews.

Debugs production issues caused by one's code changes, with the help of others.

Improves team documentation.

May start participating in the team's on-call and/or support rotation.

#### P2 - Software Engineer II

Writes tests across the testing pyramid

Always writes tests to handle expected edge cases and errors gracefully, as well as happy paths.

Looks for an appropriate level of testing when peer-reviewing code.

Balances identifying and prioritizing technical debt

Owns the quality of the outcome they ship. Only pushes code to production when it meets the product & design spec, deployed code is performant, and doesn't introduce regression in funtionality

Maintains steady and predictable delivery of scoped tasks of projects

#### P3 - Senior Engineer

Code is consistently easily testable, easily understood by other developers, and accounts for non-functional requirements including observability, security, and maintainability.

Improves observability and monitoring in owned systems by adding alerts, setting thresholds, and refining dashboards.

Delivers software that meets SLAs for reliability and performance, and remains stable under changing load or usage, and remains durable as the organization changes

Leads triage of inbound issues, efficiently root-causing and resolving bugs or regressions in team-owned systems.

Identifies and eliminates recurring issues in workflows, tools, or code to improve team velocity.

Delivers complex features or systems at a consistent, sustainable pace, independently managing scope and ambiguity, and maintains momentum across multi-week efforts

#### P4 - Staff Engineer

Contributes to and aligns work with organization-level testing strategy, identifying gaps and improving coverage.

Develops code that reduces future operational burden (e.g. by adding feature flags, appropriate exception handling, high levels of alerting/monitoring/logging, reducing alert noise, etc.).

Leads process improvements after incidents (e.g., via retros, runbooks, or automation) to reduce recurrence and improve response.

Delivers high-impact projects with excellence—whether by hitting tight, high-stakes deadlines, quickly mastering ambiguous contexts to bring clarity, or substantially elevating the quality of existing systems.

Initiates performance or reliability projects that raise the bar for the whole service, not just their code path

#### P5 - Senior Staff Engineer

Promotes technical best practices across the org

Ensures high-quality code reviews, design reviews, unit/automated test creation, and documentation.

Known as a go-to person in their area for debugging unusual or complex errors. Solves challenging cross-system issues in production.

Promotes excellence in their projects by ensuring that SLAs, monitoring, on-call rotation and high-quality playbooks are appropriately put into place.

Owns the long-term health of critical systems by defining test strategy, leading quality reviews, and holding teams to a high standard.

Formalizes runbooks or observability standards across multiple systems

Partners with product to quantify impact of reliability or tech debt

#### P6 - Principal Engineer

Drives development and continuous improvement of department-wide testing strategy and key quality metrics.

Leads operational improvements across org-critical systems and drives adoption of reliability best practices.

Introduces new ways to measure and communicate impact to customers through metrics, logging, or reporting.

Sets the standard of engineering excellence and defines quality expectations through org-wide processes and culture.

Scales a culture of reliability through mechanisms, not heroics

---

### Product Sense

Business domain and customer focus: User scenarios, workflows, customer empathy, customer experience, problems we're trying to solve for the customer

#### P1 - Software Engineer I

Understands product area of focus, how it fits into the overall business, and occasionally suggests improvements for it.

#### P2 - Software Engineer II

Thoroughly understands the business model in relation to their current product focus area. Looks for opportunities to simplify technical design.

Understands the users of the software they build, and develops engineering designs that yield a great user experience.

#### P3 - Senior Engineer

Applies domain knowledge to ask clarifying questions and provide actionable feedback on product and technical specs.

Defines success metrics for features and ensures shipped work measurably improves the customer experience.

Makes technical decisions aligned with future product vision by grounding choices in data and roadmap context.

Identifies, advocates for, and completes high-leverage roadmap items

Proactively flags misaligned product decisions based on system constraints or user impact

#### P4 - Staff Engineer

Applies deep understanding of team and adjacent domains to drive impactful tradeoffs and propose product improvements.

Advocates for users of their team's software, consistently pushing to improve user experience.

Owns outcome metrics (KPIs/OKRs) for their systems and contributes to broader product success metrics.

Evangelizes for engineering-led roadmap items based on system constraints or user feedback.

#### P5 - Senior Staff Engineer

Shapes product direction through architectural insight or pattern selection that unlocks future capabilities.

Aligns technical work across squads to business and market trends, identifying opportunities to improve product outcomes through reusable infrastructure or platform enhancements.

Shapes technical roadmaps that drive key product outcomes (reliability, latency, customization, etc.)

Bridges product/tech tradeoffs between teams, advocating for strategic product bets

#### P6 - Principal Engineer

Pushes on requirements and technical designs organization-wide to maximize the customer experience.

Drives org-defining product innovations by identifying long-term customer needs and leading the delivery of new technical capabilities.

Influences the product roadmap through customer insight and technical possibility

Translates high-level product ideas into concrete, scoped engineering projects

---

## Behavior

### Collaboration

Build together, influence, and build consensus

#### P1 - Software Engineer I

Learning to build software as part of a team.

Communicate status of own work with clarity.

Actively participates in team discussions, including sprint ceremonies, project retros, and technical discussions.

Respects others by listening to their ideas and suggestions.

Builds relationships with teammates and manager.

#### P2 - Software Engineer II

Refining skills as a team-oriented software engineer.

Actively participates in team discussions, including sprint ceremonies, project retros, and technical discussions.

Often works on larger group projects with other engineers on the team.

Feels comfortable negotiating Negotiates the division of labor with other teammates.

Practices attribution and gives credit to teammates.

#### P3 - Senior Engineer

Collaborates closely with engineers, PMs, and designers to align on scope, unblock teammates, and resolve ambiguity.

Leads team-wide technical discussions and discovery efforts, aligning the team on architectural direction.

Preemptively reaches out to peers to support short term tasking as well as more general engineering growth.

Gives and shares credit where due.

Leads large team projects by breaking down work, coordinating execution, and guiding junior engineers toward success.

#### P4 - Staff Engineer

Inclusive facilitator in team conversations. Doesn't let one voice (including their own) dominate.

Surfaces and resolves misalignment between stakeholders by identifying shared goals and constraints

Maintains a reputation for approachability and support, actively mentoring and guiding peers.

Drives cross-team consensus for critical features & knows when to disagree and commit

#### P5 - Senior Staff Engineer

Coordinates execution across multiple teams and functions, resolving ambiguity and surfacing blockers early.

Consistently helps teammates overcome obstacles and shepherd projects across the finish line through pairing, code review, project management, and meeting facilitation.

Works with engineers, engineering leadership, and other stakeholders to identify and solve problems that span multiple teams.

Prioritizes team success over personal credit, taking on unglamorous or tedious tasks when needed.

Resolves conflicts across teams or functions by aligning on shared goals

Leads working groups or cross-functional initiatives, building lasting collaboration patterns (rituals, shared docs, templates)

Builds strong cross-functional relationships within and beyond R&D, modeling proactive and inclusive collaboration.

#### P6 - Principal Engineer

Builds consensus around technical decisions that span the entire organization.

Facilitates and leads engineering-wide discussions that create alignment around engineering principles and priorities. Makes compelling arguments for technical direction without being abrassive or condescending.

Identifies and aligns high-leverage opportunities across orgs, even when they fall outside formal ownership.

Anticipates cross-org challenges and steers technical direction to address them, and drives alignment even admid disagreement

Shapes org culture by participating in hiring, calibration, and bar-setting conversations across EPD.

Defuses org-level conflict through reframing and shared-context building

---

### Mentorship & Knowledge Sharing

Disseminate knowledge to help individuals and the business grow

#### P1 - Software Engineer I

Seeks out mentorship to level-up and learn new skills.

Documents their work clearly.

Eager to both receive and give constructive, respectful, and empathetic feedback, including in code reviews.

Demos their work in show and tell sessions.

Serves as onboarding buddy for interns and other early-career new hires.

#### P2 - Software Engineer II

Seeks out mentorship to grow their own experience.

Ensures that important information is documented and shared for future reference.

Eager to both receive and give constructive, respectful, and empathetic feedback.

Participates in engineering lunch n learns.

Mentors interns and early-career new hires.

#### P3 - Senior Engineer

Mentors more junior engineers on the team through pairing and technical discussion.

Shares knowledge at org lunch n learns, knowledge shares, and show and tells.

Adept at both receiving and giving constructive, respectful, and empathetic feedback. Asks meaningful questions about performance and feedback to support ongoing development. Able to provide effective upward feedback to manager.

Uses code and RFC reviews to guide teammates toward clearer, simpler, or more scalable solutions.

Contributes to engineering-wide initiatives like revamping an interview module or organizing recurring brown bag sessions to spread knowledge

Documents key knowledge in areas they own to support onboarding and continuity

#### P4 - Staff Engineer

Anchors the team technically by mentoring others and owning decisions that support long-term growth.

Go-to person on their team to answer questions and technically help new team members.

Promotes the adoption of best practices within their team, sharing their knowledge of coding standards, design principles, and development methodologies.

Learning to delegate, coach, and mentor members of the team so that the overall impact of the team is greater than their individual impact.

Partners with manager to shape team culture; seen as both a technical leader and a team stabilizer.

#### P5 - Senior Staff Engineer

Champions cross-team knowledge sharing via documentation, tech talks, and reusable examples.

Proactively identifies and closes gaps in system and domain knowledge across teams.

A go-to resource outside of the engineering team, who is highly approachable and regularly receives requests for help or guidance.

Helps teammates think through problems without immediately providing answers or pushing their own opinion.

Occasionally contributes to the engineering community outside of Hebbia in the form of OSS, technical blog posts, conference talks, etc.

Mentors senior engineers on cross-team thinking, systems ownership, or architecture

#### P6 - Principal Engineer

Expert teacher and mentor and a go-to resource for senior+ engineers and engineering leadership.

Leverages their expertise to help engineers of all levels learn and grow, catering communication levels appropriately and accessibly.

Seeks high-leverage forms of knowledge sharing, such as internal knowledge sharing portals (as applicable), Office Hours, technical documentation, blog posts, etc

Recognized expert in their field and contributes regularly to the wider tech community by owning or maintaining OSS, speaking regularly at conferences, etc.

Establishes mentorship culture by mentoring mentors

Distills insights from incidents, migrations, or major launches into reusable lessons and patterns that level up the entire org.
