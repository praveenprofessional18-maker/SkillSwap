from .models import LearningLesson, LearningModule, LearningPath, LearningQuizQuestion


def _lesson(
    slug, title, objectives, explanation, steps, practical, language, code, exercise, questions,
):
    return {
        "slug": slug,
        "title": title,
        "objectives": objectives,
        "explanation": explanation,
        "tutorial_steps": steps,
        "practical_example": practical,
        "code_examples": [{"language": language, "title": "Example", "code": code}],
        "exercise_prompt": exercise,
        "questions": questions,
    }


CURRICULUM = (
    {
        "slug": "web-development",
        "title": "Web Development",
        "description": "Build accessible, responsive web pages and add useful browser interactions.",
        "difficulty": "Beginner",
        "estimated_minutes": 60,
        "modules": (
            {
                "slug": "web-foundations",
                "title": "Web Foundations",
                "description": "Structure pages with semantic HTML and style them with CSS.",
                "lessons": (
                    _lesson(
                        "web-semantic-html", "Structure a page with semantic HTML",
                        ["Choose elements by meaning, not appearance.", "Connect labels and controls for accessible forms."],
                        "HTML describes the content and its structure. Semantic elements such as `main`, `nav`, and `article` communicate purpose to browsers and assistive technology. A page should have one clear main region and a logical heading order.\n\nForms need explicit labels. Native buttons and links already support keyboard interaction, so use them instead of clickable generic containers.",
                        ["Create a document with a title and one `main` element.", "Add a heading followed by a short article.", "Add a labeled text input and a submit button."],
                        "A contact form with a visible label remains understandable when read by a screen reader and can be completed using only a keyboard.",
                        "html", "<main>\n  <h1>Learning journal</h1>\n  <article>\n    <h2>Today</h2>\n    <p>I practiced semantic HTML.</p>\n  </article>\n</main>",
                        "Sketch a small page outline and write semantic markup for a navigation area, main article, and labeled form field.",
                        [
                            ("What is the main purpose of semantic HTML?", ["To communicate the meaning and structure of content", "To make every page look identical"], 0),
                            ("What should a form label do?", ["Describe the associated control", "Replace the page heading"], 0),
                        ],
                    ),
                    _lesson(
                        "web-responsive-css", "Style a responsive layout",
                        ["Explain the CSS box model.", "Use flexible layout rules for narrow and wide screens."],
                        "CSS applies visual rules to HTML. In the box model, an element's size is affected by its content, padding, border, and margin. `box-sizing: border-box` makes declared widths include padding and border, which is easier to reason about.\n\nFlexbox and Grid adapt to available space. Prefer fluid widths and a small number of breakpoints over fixed pixel layouts that overflow on phones.",
                        ["Set a readable base font and `box-sizing` rule.", "Use Grid or Flexbox for a group of cards.", "Add a breakpoint only when the layout needs to change."],
                        "A two-column card layout can become a single column on a small screen without changing the markup.",
                        "css", "*, *::before, *::after { box-sizing: border-box; }\n.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1rem; }",
                        "Create CSS for a card group that has a consistent gap and never becomes narrower than 16rem.",
                        [
                            ("Which properties are included by `border-box` sizing?", ["Content, padding, and border", "Margin only"], 0),
                            ("Why use a fluid layout?", ["It can adapt to different available widths", "It guarantees every screen has the same width"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "browser-interaction",
                "title": "Browser Interaction",
                "description": "Make a page respond to user actions with JavaScript.",
                "lessons": (
                    _lesson(
                        "web-dom-events", "Respond to a button click",
                        ["Select an element safely.", "Handle a user event and update the page."],
                        "The Document Object Model (DOM) is the browser's structured representation of a page. JavaScript can select an element and attach an event listener. Keep behavior in event handlers rather than inline HTML attributes.\n\nWhen displaying user-provided text, assign it through `textContent` instead of `innerHTML`. This treats the value as text and avoids interpreting it as markup.",
                        ["Give the button and status message stable IDs.", "Find both elements with `getElementById`.", "Register a click handler that updates `textContent`."],
                        "A save button can update a status message to confirm that the page received the click.",
                        "javascript", "const button = document.getElementById(\"save\");\nconst status = document.getElementById(\"status\");\nbutton.addEventListener(\"click\", () => {\n  status.textContent = \"Saved\";\n});",
                        "Add a button that changes a nearby status message from `Not started` to `In progress`.",
                        [
                            ("Which property treats a value as plain text?", ["textContent", "innerHTML"], 0),
                            ("Where should click behavior be attached?", ["An event listener", "A heading's text"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
    {
        "slug": "python-programming",
        "title": "Python Programming",
        "description": "Practice Python fundamentals, reusable functions, and clear data handling.",
        "difficulty": "Beginner",
        "estimated_minutes": 55,
        "modules": (
            {
                "slug": "python-fundamentals",
                "title": "Python Fundamentals",
                "description": "Work with values, conditions, and collections.",
                "lessons": (
                    _lesson(
                        "python-values-and-conditions", "Use values and conditions",
                        ["Recognize common Python value types.", "Branch with clear boolean conditions."],
                        "Python values have types such as strings, integers, floats, and booleans. A variable name refers to a value; choose names that describe what the value represents.\n\nAn `if` statement runs a block only when its condition is true. Use `elif` for another mutually exclusive case and `else` for the remaining case. Indentation defines the block.",
                        ["Assign a string and an integer to descriptive names.", "Build a boolean condition from those values.", "Add `if` and `else` branches with consistent indentation."],
                        "A program can categorize a temperature as cold or warm using a numeric comparison.",
                        "python", "temperature_c = 18\nif temperature_c < 20:\n    message = \"Bring a layer\"\nelse:\n    message = \"Light clothing is fine\"\nprint(message)",
                        "Write a condition that labels a score as `pass` when it is at least 60 and `retry` otherwise.",
                        [
                            ("What defines a Python code block?", ["Indentation", "Curly braces"], 0),
                            ("Which operator checks whether a value is at least 60?", [">=", "<"], 0),
                        ],
                    ),
                    _lesson(
                        "python-collections", "Organize data in collections",
                        ["Choose between a list and a dictionary.", "Iterate over a collection."],
                        "A list stores an ordered sequence of values. A dictionary maps keys to values, making it useful when each value has a named meaning. Both can be iterated with `for`.\n\nUse a dictionary lookup with a key that exists, or use `.get()` when a key may be missing. Small, well-named collections make transformations easier to understand.",
                        ["Create a list of three items.", "Create a dictionary with a named field.", "Loop through the list and print each item."],
                        "A reading list can store titles in order, while a dictionary can store one book's title and page count.",
                        "python", "topics = [\"lists\", \"dictionaries\", \"loops\"]\nbook = {\"title\": \"Small Steps\", \"pages\": 120}\nfor topic in topics:\n    print(topic)\nprint(book.get(\"title\"))",
                        "Create a dictionary for a learning task with `title` and `done` fields, then print its title.",
                        [
                            ("Which collection maps keys to values?", ["Dictionary", "List"], 0),
                            ("What does a `for` loop do here?", ["Visits each item in a sequence", "Changes every item automatically"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "python-reusable-code",
                "title": "Reusable Python Code",
                "description": "Write functions with clear inputs and outputs.",
                "lessons": (
                    _lesson(
                        "python-functions", "Write a reusable function",
                        ["Define a function with parameters.", "Return a value and call the function."],
                        "A function groups a named operation so it can be reused. Parameters are the inputs; `return` sends a result back to the caller. A function should ideally do one clearly described job.\n\nThe `return` statement ends that call. Printing is useful for display, but returning is better when another part of a program needs to use the result.",
                        ["Choose a descriptive function name.", "Add parameters for the values it needs.", "Return the result and test it with a call."],
                        "A `minutes_to_seconds` function can be reused anywhere a duration needs conversion.",
                        "python", "def minutes_to_seconds(minutes):\n    return minutes * 60\n\nstudy_seconds = minutes_to_seconds(25)\nprint(study_seconds)",
                        "Write a function that accepts a person's name and returns a short greeting.",
                        [
                            ("What does `return` do?", ["Sends a result to the caller", "Displays a value only"], 0),
                            ("What is a function parameter?", ["An input named in the function definition", "A comment after the function"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
    {
        "slug": "java-programming",
        "title": "Java Programming",
        "description": "Learn Java types, methods, classes, and responsible object-oriented design.",
        "difficulty": "Beginner",
        "estimated_minutes": 55,
        "modules": (
            {
                "slug": "java-language-basics",
                "title": "Java Language Basics",
                "description": "Declare typed values and use methods.",
                "lessons": (
                    _lesson(
                        "java-types-and-conditions", "Use types and conditions",
                        ["Declare variables with explicit types.", "Use a conditional to select behavior."],
                        "Java is statically typed: a variable declaration includes a type, and the compiler checks many mistakes before a program runs. Use `int` for whole numbers and `String` for text.\n\nA boolean expression can control an `if`/`else` statement. Braces make the block boundaries explicit and should be used consistently.",
                        ["Declare an integer with a descriptive name.", "Compare it to a threshold.", "Assign a message in both branches."],
                        "A learning app can display a different message depending on whether a quiz score meets its target.",
                        "java", "int score = 82;\nString result;\nif (score >= 70) {\n    result = \"Passed\";\n} else {\n    result = \"Try again\";\n}\nSystem.out.println(result);",
                        "Write a condition that assigns `Ready` when `completed` is true and `Continue` otherwise.",
                        [
                            ("What does Java's static typing help check?", ["Whether values fit declared types", "Whether a screen has good colors"], 0),
                            ("Which value type is used for true/false?", ["boolean", "String"], 0),
                        ],
                    ),
                    _lesson(
                        "java-methods", "Create a small method",
                        ["Define a method with a return type.", "Call a method using an argument."],
                        "A Java method has a return type, name, parameters, and a body. The return type describes the value the method sends back; use `void` when it returns no value.\n\nKeep method responsibilities small and describe them with clear names. Parameters let one method work with different input values.",
                        ["Choose a method name that describes its result.", "Declare a parameter and return type.", "Call the method and use its returned value."],
                        "A method that converts minutes to seconds can be used by more than one screen or feature.",
                        "java", "static int toSeconds(int minutes) {\n    return minutes * 60;\n}\n\nint duration = toSeconds(25);",
                        "Write a method signature and body that takes a price and returns it with a 10% discount.",
                        [
                            ("What does a method return type describe?", ["The kind of value returned", "The number of method calls"], 0),
                            ("How can a method work with different values?", ["Accept parameters", "Use one fixed global value"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "java-objects",
                "title": "Objects and Collections",
                "description": "Model related data and store ordered values.",
                "lessons": (
                    _lesson(
                        "java-classes-and-objects", "Model a simple class",
                        ["Describe a class as a type definition.", "Create an object with initialized fields."],
                        "A class defines a type with fields and methods. An object is one instance of that class. Encapsulation keeps an object's state controlled; private fields with purposeful methods are safer than exposing every field for arbitrary changes.\n\nConstructors establish a valid initial state. Use one object to represent one domain concept rather than grouping unrelated values.",
                        ["Identify the data one concept needs.", "Declare private fields and a constructor.", "Create an instance and call a method."],
                        "A `Lesson` object might keep a title and a completion flag together.",
                        "java", "class Lesson {\n    private final String title;\n    Lesson(String title) { this.title = title; }\n    String title() { return title; }\n}\nLesson lesson = new Lesson(\"Methods\");",
                        "Design a small `Book` class with a private title and a constructor that sets it.",
                        [
                            ("What does a class define?", ["A type and its behavior", "A running server"], 0),
                            ("What is an object?", ["An instance of a class", "A Java keyword for comments"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
    {
        "slug": "cybersecurity",
        "title": "Cybersecurity",
        "description": "Build safe habits around accounts, data, and defensive web security.",
        "difficulty": "Beginner",
        "estimated_minutes": 50,
        "modules": (
            {
                "slug": "security-foundations",
                "title": "Security Foundations",
                "description": "Protect accounts and reduce unnecessary access.",
                "lessons": (
                    _lesson(
                        "cyber-account-safety", "Protect accounts and sessions",
                        ["Use unique passwords and a password manager.", "Explain multi-factor authentication and session logout."],
                        "Account security starts with unique passwords. Reusing one password lets a breach on one service put other accounts at risk. A reputable password manager can create and store distinct passwords.\n\nMulti-factor authentication adds a second proof of identity. Sign out on shared devices, keep recovery options current, and never share one-time codes with someone who contacts you unexpectedly.",
                        ["Use a unique password for each account.", "Enable multi-factor authentication where available.", "Review active sessions and revoke ones you do not recognize."],
                        "If a laptop is lost, revoking its active session can stop that device from using the account token.",
                        "text", "Account safety checklist:\n- Unique password\n- Multi-factor authentication\n- Review active sessions\n- Revoke unknown sessions",
                        "Write a short account-safety checklist for a service you use. Do not include real passwords, codes, or account details.",
                        [
                            ("Why use a unique password for each service?", ["A breach at one service should not unlock others", "It makes every password easier to guess"], 0),
                            ("What should you do with an unexpected one-time-code request?", ["Never share the code", "Send the code to verify your identity"], 0),
                        ],
                    ),
                    _lesson(
                        "cyber-least-privilege", "Apply least privilege",
                        ["Explain why access should be limited.", "Identify a safe response to an access request."],
                        "Least privilege means granting only the access needed for a task, for only as long as it is needed. It limits accidental changes and reduces the impact of a compromised account.\n\nReview permissions when responsibilities change. Prefer separate accounts for separate roles and avoid sharing credentials; an audit trail is useful only when actions can be attributed to individual accounts.",
                        ["Name the task an account must perform.", "Grant only the required resource and action.", "Remove access when the task or role ends."],
                        "A read-only reporting account should not also be able to delete customer records.",
                        "text", "Access review:\n1. Identify the task.\n2. Grant the minimum required permission.\n3. Set an owner and review date.\n4. Remove access when it is no longer needed.",
                        "Describe the minimum permissions a volunteer needs to view a public event schedule, and name one permission they should not receive.",
                        [
                            ("What is the goal of least privilege?", ["Limit access to what a task requires", "Give every account administrator access"], 0),
                            ("When should unneeded access be removed?", ["When its task or role ends", "Only after an incident"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "secure-web-basics",
                "title": "Secure Web Basics",
                "description": "Use safe defaults when handling browser data.",
                "lessons": (
                    _lesson(
                        "cyber-safe-output", "Treat user input as data",
                        ["Distinguish text from executable markup.", "Choose safe DOM output APIs."],
                        "User input should be treated as untrusted data. A browser can interpret strings inserted as HTML, so directly combining input with markup may create script injection risks.\n\nUse framework escaping or DOM APIs such as `textContent` for plain text. Validate inputs for product rules on the server as well as the client; client-side checks improve usability but are not an authorization boundary.",
                        ["Identify which values come from users or external sources.", "Render plain text with text-safe APIs.", "Repeat important validation and access checks on the server."],
                        "A comment should appear as text even if it contains characters that resemble HTML.",
                        "javascript", "const message = document.createElement(\"p\");\nmessage.textContent = commentFromUser;\ncontainer.append(message);",
                        "Describe how you would display a member's profile biography as text without asking the browser to parse it as HTML.",
                        [
                            ("Which side must enforce access control?", ["The server", "The visual state of a button"], 0),
                            ("What does `textContent` do with a string?", ["Displays it as text", "Parses it as HTML"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
    {
        "slug": "cloud-computing",
        "title": "Cloud Computing",
        "description": "Understand cloud service models, reliability, and secure configuration.",
        "difficulty": "Beginner",
        "estimated_minutes": 45,
        "modules": (
            {
                "slug": "cloud-concepts",
                "title": "Cloud Concepts",
                "description": "Compare service models and plan for failure.",
                "lessons": (
                    _lesson(
                        "cloud-service-models", "Compare cloud service models",
                        ["Distinguish infrastructure, platform, and software services.", "Recognize shared responsibility."],
                        "Infrastructure as a Service offers configurable compute and networking. Platform as a Service manages more of the runtime, while Software as a Service provides a complete application. More managed services can reduce operational work but do not remove the need to secure accounts and data.\n\nCloud security is shared: providers secure parts of the underlying service, while customers remain responsible for their configuration, identities, and data handling.",
                        ["List what your application team currently manages.", "Compare that list across IaaS, PaaS, and SaaS.", "Record which security responsibilities remain yours."],
                        "A small team may prefer a managed database so it can focus on the application while still controlling database identities and data access.",
                        "text", "IaaS: manage operating system and application\nPaaS: manage application and data\nSaaS: configure users, settings, and data",
                        "Choose a service model for a small team email service and name one responsibility the team still has.",
                        [
                            ("Which model typically provides a complete application?", ["SaaS", "IaaS"], 0),
                            ("Does a managed service remove customer security responsibilities?", ["No", "Yes, all responsibility transfers"], 0),
                        ],
                    ),
                    _lesson(
                        "cloud-resilience", "Plan for service interruptions",
                        ["Describe redundancy and backups.", "Choose a recovery objective for a service."],
                        "Reliability planning starts with understanding what users need. Redundancy can reduce downtime when a component fails; backups help recover data after accidental deletion or corruption. They address different failure modes.\n\nA recovery time objective describes how quickly a service should return. A recovery point objective describes how much recent data loss is acceptable. Test recovery procedures rather than assuming a backup is usable.",
                        ["Identify likely failures and user impact.", "Set recovery time and data-loss targets.", "Test a restore using a recent backup."],
                        "A learning journal may tolerate a short outage but should restore a recent copy of a learner's saved progress.",
                        "text", "Recovery plan:\n- Service: learning journal\n- Recovery time target: 4 hours\n- Recovery point target: 1 hour\n- Restore test: quarterly",
                        "Write a simple recovery time and recovery point objective for a personal project, then describe one restore test.",
                        [
                            ("What does a recovery point objective describe?", ["Acceptable data loss measured in time", "The number of servers"], 0),
                            ("Why test a backup restore?", ["To confirm the data can actually be recovered", "To make the backup larger"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "cloud-safety",
                "title": "Cloud Safety",
                "description": "Keep identities and configuration under control.",
                "lessons": (
                    _lesson(
                        "cloud-identity-basics", "Secure cloud identities",
                        ["Apply role-based permissions.", "Protect and rotate credentials safely."],
                        "Cloud accounts can control infrastructure and sensitive data. Use named identities, multi-factor authentication, and roles that grant only the actions needed. Avoid sharing long-lived credentials among people or storing secrets in source code.\n\nReview access regularly and revoke unused credentials. Use the provider's managed identity or secret store where available, and monitor for unusual access activity.",
                        ["Create an identity for a specific task.", "Assign a narrow role rather than broad administrator rights.", "Review usage and remove unused credentials."],
                        "A deployment process should use a dedicated identity that can publish one application, not manage unrelated billing or user accounts.",
                        "text", "Deployment identity:\n- Scope: one application\n- Permissions: publish a release\n- Credential: managed secret store\n- Review: remove when pipeline is retired",
                        "Design a least-privilege deployment identity for a single project and list one permission it should not have.",
                        [
                            ("Where should long-lived secrets be stored?", ["A managed secret store", "A public source repository"], 0),
                            ("Why use a dedicated deployment identity?", ["To limit and audit its permissions", "To share one password with the whole team"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
    {
        "slug": "ui-ux-design",
        "title": "UI/UX Design",
        "description": "Research user needs and design clear, inclusive interfaces.",
        "difficulty": "Beginner",
        "estimated_minutes": 50,
        "modules": (
            {
                "slug": "design-research",
                "title": "Design Research",
                "description": "Understand user goals before choosing a solution.",
                "lessons": (
                    _lesson(
                        "ux-user-interviews", "Learn from user interviews",
                        ["Ask open, neutral questions.", "Separate observed behavior from assumptions."],
                        "User research helps teams understand goals, context, and friction. Open questions invite participants to describe what they do in their own words. Leading questions can bias answers toward the researcher's preferred solution.\n\nAsk about recent real experiences rather than hypothetical preferences. Record observations separately from interpretations, and avoid collecting personal data that is not needed.",
                        ["Define one research question.", "Ask about a recent task and its context.", "Summarize what was observed before proposing a design."],
                        "Instead of asking whether someone likes a new menu, ask them how they found a specific feature last time.",
                        "text", "Neutral prompt: \"Tell me about the last time you tried to find a lesson.\"\nFollow-up: \"What did you expect to happen next?\"",
                        "Write two neutral questions to understand how someone currently tracks learning progress.",
                        [
                            ("Which question is less leading?", ["Tell me how you last found a lesson", "You like the new menu, right?"], 0),
                            ("What should be separated in research notes?", ["Observed behavior and interpretation", "Questions and punctuation"], 0),
                        ],
                    ),
                    _lesson(
                        "ux-accessible-hierarchy", "Create clear visual hierarchy",
                        ["Use headings and spacing to show structure.", "Check readability and keyboard focus."],
                        "Visual hierarchy helps people find the most important information first. Size, contrast, spacing, and alignment can communicate relationships, but color should not be the only signal. Consistent headings make a page easier to scan.\n\nAccessible design also includes readable contrast, meaningful labels, visible keyboard focus, and controls that can be used without a mouse. Test the actual interface at different zoom levels and viewport sizes.",
                        ["Order content by user priority.", "Use consistent heading styles and spacing.", "Check contrast, focus visibility, and a narrow viewport."],
                        "A form error should identify the field and explain how to fix it, rather than only turning the field border red.",
                        "text", "Form feedback:\nEmail address\n[ field ]\nError: Enter an email address such as name@example.com",
                        "Sketch a sign-in form and describe its heading, field labels, primary action, and accessible error message.",
                        [
                            ("Why should color not be the only signal?", ["Some users may not perceive the color difference", "Color makes text too short"], 0),
                            ("What makes keyboard focus easier to use?", ["A visible focus indicator", "Removing outlines from every control"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "design-prototyping",
                "title": "Prototyping",
                "description": "Turn a user flow into a testable interface.",
                "lessons": (
                    _lesson(
                        "ux-prototype-and-test", "Prototype and test a user flow",
                        ["Map a task into steps.", "Use a prototype to observe usability."],
                        "A user flow describes the steps someone takes to complete a task. A prototype makes the flow tangible before implementation. It can be a paper sketch or a clickable model; it should answer a specific design question rather than imitate every production detail.\n\nIn a usability session, give a realistic task and let the participant think aloud. Observe confusion and recovery without immediately coaching them.",
                        ["Name the user's goal.", "Draw the smallest flow that supports the goal.", "Test it with a participant and record friction points."],
                        "A clickable prototype can reveal that learners cannot find the next lesson before the team builds a complete course player.",
                        "text", "Goal: resume a course\nDashboard → Learning Paths → Course → Continue lesson",
                        "Map a three-step flow for finding and resuming a saved learning path.",
                        [
                            ("What is a prototype useful for?", ["Testing a design idea before full implementation", "Proving a design has no issues"], 0),
                            ("What should a facilitator do during a usability task?", ["Observe and avoid coaching", "Tell the participant every next step"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
    {
        "slug": "data-science",
        "title": "Data Science",
        "description": "Clean small datasets, summarize patterns, and communicate uncertainty.",
        "difficulty": "Beginner",
        "estimated_minutes": 55,
        "modules": (
            {
                "slug": "data-foundations",
                "title": "Data Foundations",
                "description": "Inspect data quality and calculate useful summaries.",
                "lessons": (
                    _lesson(
                        "data-cleaning", "Inspect and clean a dataset",
                        ["Identify missing and inconsistent values.", "Keep a reproducible record of cleaning decisions."],
                        "Data cleaning makes a dataset more consistent, but every change should preserve meaning. Inspect column types, missing values, duplicates, and unexpected categories before analysis.\n\nDo not silently remove records or infer sensitive facts. Record transformations so another person can understand what changed and reproduce the result.",
                        ["Inspect a small sample and column types.", "Count missing and duplicate values.", "Document each correction and its reason."],
                        "A date column containing two formats should be normalized only after confirming which formats are valid.",
                        "python", "records = [{\"hours\": 2}, {\"hours\": None}, {\"hours\": 3}]\nmissing = sum(row[\"hours\"] is None for row in records)\nprint(f\"Missing hours: {missing}\")",
                        "List three checks you would make before analyzing a dataset of study-session durations.",
                        [
                            ("Why record data-cleaning decisions?", ["So the work can be reviewed and reproduced", "So the original data can be forgotten"], 0),
                            ("What should you do with a missing value?", ["Inspect and document how it should be handled", "Always replace it with zero"], 0),
                        ],
                    ),
                    _lesson(
                        "data-summary-statistics", "Summarize a numeric measure",
                        ["Calculate a mean and median.", "Explain why one summary may not tell the whole story."],
                        "The mean is the sum divided by the number of observations. The median is the middle value after sorting. A few extreme values can pull the mean, while the median is often more representative of a skewed distribution.\n\nAlways include units and sample size. A summary describes the data collected; it does not by itself establish why a pattern occurred.",
                        ["Sort the observed values.", "Compute the mean and identify the middle value.", "Compare the summaries and inspect unusual values."],
                        "For study durations of 10, 12, 14, and 90 minutes, the median better reflects a typical short session than the mean.",
                        "python", "durations = [10, 12, 14, 90]\nmean = sum(durations) / len(durations)\nordered = sorted(durations)\nmedian = (ordered[1] + ordered[2]) / 2\nprint(mean, median)",
                        "For a small list of five measurements, calculate the median and explain whether an unusually large value changes your conclusion.",
                        [
                            ("Which statistic is more affected by an extreme value?", ["Mean", "Median"], 0),
                            ("What should accompany a reported statistic?", ["Units and sample size", "A claim of causation"], 0),
                        ],
                    ),
                ),
            },
            {
                "slug": "data-communication",
                "title": "Data Communication",
                "description": "Choose a clear chart and state what the data can support.",
                "lessons": (
                    _lesson(
                        "data-chart-selection", "Choose a chart for the question",
                        ["Match a chart to the data relationship.", "Label axes and avoid misleading scales."],
                        "A bar chart compares categories, while a line chart is useful for ordered time points. A scatter plot shows the relationship between two numeric variables. The chart should answer the question without hiding important context.\n\nLabel axes with units and include the time period or population represented. Truncated axes and inconsistent intervals can exaggerate differences.",
                        ["Write the question the chart should answer.", "Identify whether values are categories, time, or paired numbers.", "Choose a chart and label its scales and units."],
                        "A line chart can show monthly lesson completions, while a bar chart compares completions by course.",
                        "text", "Question: How did completions change each month?\nData: month and completion count\nChart: line chart\nLabels: Month; Completions (learners)",
                        "Choose a chart for comparing completion counts across four courses and write descriptive axis labels.",
                        [
                            ("Which chart is a common choice for values over time?", ["Line chart", "Unlabeled pie chart"], 0),
                            ("Why label a numeric axis with units?", ["To make the measurement interpretable", "To hide the data source"], 0),
                        ],
                    ),
                ),
            },
        ),
    },
)


def initialize_learning_catalog(db):
    for path_position, path_data in enumerate(CURRICULUM):
        path = db.query(LearningPath).filter(LearningPath.slug == path_data["slug"]).first()
        if path is None:
            path = LearningPath(slug=path_data["slug"])
            db.add(path)
        for field in ("title", "description", "difficulty", "estimated_minutes"):
            setattr(path, field, path_data[field])
        path.position = path_position
        db.flush()

        for module_position, module_data in enumerate(path_data["modules"]):
            module = db.query(LearningModule).filter(
                LearningModule.path_id == path.id,
                LearningModule.slug == module_data["slug"],
            ).first()
            if module is None:
                module = LearningModule(path_id=path.id, slug=module_data["slug"])
                db.add(module)
            for field in ("title", "description"):
                setattr(module, field, module_data[field])
            module.position = module_position
            db.flush()

            for lesson_position, lesson_data in enumerate(module_data["lessons"]):
                lesson = db.query(LearningLesson).filter(
                    LearningLesson.slug == lesson_data["slug"]
                ).first()
                if lesson is None:
                    lesson = LearningLesson(module_id=module.id, slug=lesson_data["slug"])
                    db.add(lesson)
                for field in (
                    "title", "objectives", "explanation", "tutorial_steps",
                    "practical_example", "code_examples", "exercise_prompt",
                ):
                    setattr(lesson, field, lesson_data[field])
                lesson.module_id = module.id
                lesson.position = lesson_position
                db.flush()

                existing = {
                    question.position: question
                    for question in db.query(LearningQuizQuestion).filter(
                        LearningQuizQuestion.lesson_id == lesson.id
                    ).all()
                }
                for question_position, (text, choices, correct_option) in enumerate(lesson_data["questions"]):
                    question = existing.pop(question_position, None)
                    if question is None:
                        question = LearningQuizQuestion(
                            lesson_id=lesson.id, position=question_position
                        )
                        db.add(question)
                    question.question = text
                    question.choices = choices
                    question.correct_option = correct_option
                for obsolete in existing.values():
                    db.delete(obsolete)
    db.commit()
