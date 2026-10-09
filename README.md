# Student-engagemnt
E
E
Mmbers of the team:
Ivanov Yaromir, Shtyrev Egor, Jbira Kareem

Comunication via Telegram

Project is made to adress the problem of low engagement during exams.

# Project brief

## User and situation
Who needs the system?
University instructors, teaching assistants, and course coordinators who administer exams (in-person, online, or hybrid) and want to understand how engaged students are during the exam.
What happens now?
Engagement is judged anecdotally or through post-exam surveys. Instructors notice students who leave early, stare at the ceiling, or rush through questions, but have no systematic way to identify disengagement patterns across a cohort. Online proctoring tools flag suspicious behavior but rarely measure positive engagement (focus, persistence, effort).
what should become better?
Instructors should get timely, interpretable signals about which students (or which exam sections/questions) show low engagement, so they can intervene (e.g., follow up, adjust exam design, offer support) and so exam results can be interpreted with context.
## What the system should do
- Input:
- Exam response logs (timestamps per question, answer changes, time-on-task
Student metadata (course, prior performance, accommodations – anonymized where possible)
Exam structure (question order, difficulty, point values)
Post-exam self-report (brief engagement survey)
- Useful output:
- Per-student engagement score or profile (e.g., sustained focus, disengagement episodes)
Per-question engagement metrics (e.g., unusually fast/slow responses, high skip rates)
Cohort-level dashboard highlighting at-risk segments
Alerts for extreme cases (e.g., student inactive for >X minutes)
Explanations: "Student 12 spent 8 seconds on 5 consecutive questions, then stopped revising."
- Action or decision after the output:
Instructor reaches out to disengaged students for support (not punishment)
Exam design is revised (e.g., unclear questions causing early abandonment)
Proctoring/ accommodation decisions are reviewed with human judgment
Engagement data is used formatively, not as sole evidence of misconduct
## Why AI may help
What pattern may need to be learned? What rules, interface, people, or review steps also belong to the system?
Patterns distinguishing productive struggle (long time on hard question) from disengagement (random guessing, rapid skipping, long inactivity). These patterns are noisy, individual, and context-dependent—hard to capture with simple thresholds.
## Initial data plan
- Where the data may come from:
LMS logs
Online exam platforms 
In-class clickers/tablets
Optional sensors with consent
Surveys and focus groups
- What we can access now:
Historical exam response timestamps from past semesters (de-identified)
Course grades and question-level scores
Basic LMS login/activity data
- What still needs confirmation:
Consent process for any video/audio or keystroke data
IRB approval status
Data-sharing agreements with platform vendors
Whether instructors will accept engagement metrics as valid
Baseline "normal" engagement ranges for different exam formats
## Three next actions
Run a pilot with 2–3 willing instructors using only existing LMS timestamp data to prototype engagement metrics and gather feedback.
Draft a consent and ethics plan covering any additional data (video, keystroke) and define strict limits on use (formative only, no discipline).
Build a simple dashboard mockup showing per-student and per-question engagement, then validate interpretations with instructors and a student focus group.
