BASELINE_QUESTIONS = [
    {
        "id": "b1",
        "text": "When you face a new problem, what do you naturally do first?",
        "trait": "thinking_style",
        "options": [
            {"id": "logic", "label": "Break it into steps", "weights": {"analytical": 2, "structured": 1}},
            {"id": "visual", "label": "Imagine how it looks", "weights": {"visual": 2, "creative": 1}},
            {"id": "people", "label": "Ask people and discuss", "weights": {"social": 2, "communication": 1}},
            {"id": "hands", "label": "Try something practical", "weights": {"hands_on": 2, "experimental": 1}},
        ],
    },
    {
        "id": "b2",
        "text": "Which kind of school or college work feels easiest to start?",
        "trait": "motivation",
        "options": [
            {"id": "numbers", "label": "Numbers, data, or patterns", "weights": {"analytical": 2, "data": 2}},
            {"id": "design", "label": "Drawing, designing, or improving ideas", "weights": {"creative": 2, "visual": 1}},
            {"id": "organize", "label": "Planning, leading, or arranging work", "weights": {"leadership": 2, "structured": 1}},
            {"id": "tools", "label": "Using tools, machines, or devices", "weights": {"hands_on": 2, "technical": 1}},
        ],
    },
    {
        "id": "b3",
        "text": "How do you feel about working with many people?",
        "trait": "social_energy",
        "options": [
            {"id": "energized", "label": "It gives me energy", "weights": {"social": 2, "communication": 2}},
            {"id": "small_team", "label": "I like small teams", "weights": {"social": 1, "structured": 1}},
            {"id": "solo", "label": "I prefer quiet solo work", "weights": {"independent": 2, "analytical": 1}},
            {"id": "depends", "label": "It depends on the task", "weights": {"adaptable": 2}},
        ],
    },
    {
        "id": "b4",
        "text": "Which sentence sounds most like you?",
        "trait": "work_style",
        "options": [
            {"id": "accuracy", "label": "I like being accurate", "weights": {"detail": 2, "structured": 1}},
            {"id": "ideas", "label": "I like creating new ideas", "weights": {"creative": 2, "experimental": 1}},
            {"id": "impact", "label": "I like helping people", "weights": {"social": 1, "service": 2}},
            {"id": "systems", "label": "I like understanding systems", "weights": {"technical": 2, "analytical": 1}},
        ],
    },
    {
        "id": "b5",
        "text": "When something is difficult, what keeps you going?",
        "trait": "resilience",
        "options": [
            {"id": "clear_goal", "label": "A clear target", "weights": {"structured": 2, "leadership": 1}},
            {"id": "curiosity", "label": "Curiosity", "weights": {"experimental": 2, "analytical": 1}},
            {"id": "support", "label": "Support from others", "weights": {"social": 1, "communication": 1}},
            {"id": "challenge", "label": "The challenge itself", "weights": {"technical": 1, "independent": 1}},
        ],
    },
]


ADAPTIVE_QUESTION_BANK = [
    {
        "id": "a_data_1",
        "text": "Would you enjoy finding the reason behind a rise or fall in marks, sales, or views?",
        "tags": ["analytical", "data"],
        "options": [
            {"id": "yes", "label": "Yes, I like finding reasons", "weights": {"data": 2, "analytical": 1}},
            {"id": "maybe", "label": "Maybe, if it is useful", "weights": {"data": 1}},
            {"id": "no", "label": "No, that sounds boring", "weights": {"creative": 1}},
        ],
    },
    {
        "id": "a_data_2",
        "text": "If given a table of student results, what would you prefer to do?",
        "tags": ["analytical", "data"],
        "options": [
            {"id": "patterns", "label": "Find patterns", "weights": {"data": 2}},
            {"id": "report", "label": "Explain it in simple words", "weights": {"communication": 2, "data": 1}},
            {"id": "avoid", "label": "Avoid tables", "weights": {"hands_on": 1, "creative": 1}},
        ],
    },
    {
        "id": "a_code_1",
        "text": "Would you like building an app that solves a real problem?",
        "tags": ["technical", "structured"],
        "options": [
            {"id": "build", "label": "Yes, building sounds exciting", "weights": {"technical": 2, "experimental": 1}},
            {"id": "plan", "label": "I would rather plan it", "weights": {"structured": 2}},
            {"id": "explain", "label": "I would rather explain it", "weights": {"communication": 2}},
        ],
    },
    {
        "id": "a_code_2",
        "text": "When a phone app fails, what are you most likely to do?",
        "tags": ["technical", "detail"],
        "options": [
            {"id": "debug", "label": "Try settings and find the cause", "weights": {"technical": 2, "detail": 1}},
            {"id": "search", "label": "Search for a fix", "weights": {"analytical": 1, "independent": 1}},
            {"id": "ask", "label": "Ask someone else", "weights": {"social": 1}},
        ],
    },
    {
        "id": "a_design_1",
        "text": "Would you enjoy improving how a website or poster looks?",
        "tags": ["creative", "visual"],
        "options": [
            {"id": "yes", "label": "Yes, I notice design", "weights": {"creative": 2, "visual": 2}},
            {"id": "content", "label": "Only the message matters to me", "weights": {"communication": 2}},
            {"id": "no", "label": "No, I prefer function", "weights": {"technical": 1, "structured": 1}},
        ],
    },
    {
        "id": "a_design_2",
        "text": "If a room is messy, what would you most want to improve?",
        "tags": ["visual", "structured"],
        "options": [
            {"id": "layout", "label": "The layout and look", "weights": {"visual": 2, "creative": 1}},
            {"id": "system", "label": "The storage system", "weights": {"structured": 2}},
            {"id": "tools", "label": "The tools used there", "weights": {"hands_on": 1}},
        ],
    },
    {
        "id": "a_people_1",
        "text": "Would you enjoy guiding a junior student who is confused?",
        "tags": ["social", "communication", "service"],
        "options": [
            {"id": "guide", "label": "Yes, I like guiding", "weights": {"service": 2, "communication": 1}},
            {"id": "short", "label": "Only for a short time", "weights": {"social": 1}},
            {"id": "no", "label": "No, I prefer task work", "weights": {"independent": 2}},
        ],
    },
    {
        "id": "a_people_2",
        "text": "In a team project, which role do you naturally take?",
        "tags": ["social", "leadership", "communication"],
        "options": [
            {"id": "leader", "label": "Organize everyone", "weights": {"leadership": 2, "communication": 1}},
            {"id": "maker", "label": "Do the main work quietly", "weights": {"independent": 1, "technical": 1}},
            {"id": "presenter", "label": "Present or explain", "weights": {"communication": 2}},
        ],
    },
    {
        "id": "a_hands_1",
        "text": "Would you rather repair a device than write about it?",
        "tags": ["hands_on", "technical"],
        "options": [
            {"id": "repair", "label": "Yes, I like practical work", "weights": {"hands_on": 2, "technical": 1}},
            {"id": "both", "label": "I can do both", "weights": {"adaptable": 2}},
            {"id": "write", "label": "I would rather write", "weights": {"communication": 2}},
        ],
    },
    {
        "id": "a_hands_2",
        "text": "Which activity sounds most satisfying?",
        "tags": ["hands_on", "visual", "technical"],
        "options": [
            {"id": "machine", "label": "Making a machine work", "weights": {"hands_on": 2, "technical": 2}},
            {"id": "model", "label": "Making a neat model", "weights": {"visual": 2, "creative": 1}},
            {"id": "guide", "label": "Teaching someone the process", "weights": {"communication": 2}},
        ],
    },
    {
        "id": "a_business_1",
        "text": "Would you like deciding how a small shop can attract more customers?",
        "tags": ["leadership", "communication", "structured"],
        "options": [
            {"id": "strategy", "label": "Yes, strategy is interesting", "weights": {"leadership": 2, "communication": 1}},
            {"id": "numbers", "label": "Only if I can use numbers", "weights": {"data": 2}},
            {"id": "no", "label": "No, not my area", "weights": {"technical": 1}},
        ],
    },
    {
        "id": "a_detail_1",
        "text": "Can you patiently check many small details for mistakes?",
        "tags": ["detail", "structured"],
        "options": [
            {"id": "yes", "label": "Yes, I can focus", "weights": {"detail": 2, "structured": 1}},
            {"id": "sometimes", "label": "Sometimes", "weights": {"detail": 1}},
            {"id": "no", "label": "No, I lose interest", "weights": {"creative": 1, "experimental": 1}},
        ],
    },
    {
        "id": "a_science_1",
        "text": "Would you enjoy testing why something happens in nature or health?",
        "tags": ["analytical", "service", "detail"],
        "options": [
            {"id": "test", "label": "Yes, experiments interest me", "weights": {"analytical": 2, "detail": 1}},
            {"id": "help", "label": "Only if it helps people", "weights": {"service": 2}},
            {"id": "no", "label": "No, I prefer other topics", "weights": {"creative": 1}},
        ],
    },
]

