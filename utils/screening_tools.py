def get_srq20_questions():
    """Get SRQ-20 questions"""
    return [
        "Do you often have headaches?",
        "Is your appetite poor?",
        "Do you sleep badly?",
        "Are you easily frightened?",
        "Do your hands shake?",
        "Do you feel nervous, tense or worried?",
        "Is your digestion poor?",
        "Do you have trouble thinking clearly?",
        "Do you feel unhappy?",
        "Do you cry more than usual?",
        "Do you find it difficult to enjoy your daily activities?",
        "Do you find it difficult to make decisions?",
        "Is your daily work suffering?",
        "Are you unable to play a useful part in life?",
        "Have you lost interest in things?",
        "Do you feel that you are a worthless person?",
        "Has the thought of ending your life been on your mind?",
        "Do you feel tired all the time?",
        "Do you have uncomfortable feelings in your stomach?",
        "Are you easily tired?"
    ]

def get_srq29_questions():
    """Get SRQ-29 WHO questions - Includes psychotic symptoms and alcohol use"""
    # First 20 questions are the same as SRQ-20
    srq20 = get_srq20_questions()
    
    # Additional 9 questions for the SRQ-29 WHO version
    additional_questions = [
        # Psychotic symptoms (21-24)
        "Do you feel that somebody has been trying to harm you in some way?",
        "Are you a much more important person than most people think?",
        "Have you noticed any interference or anything unusual in your thinking?",
        "Do you ever hear voices without knowing where they come from or which other people cannot hear?",
        
        # Epileptic seizures (25)
        "Have you ever had convulsions or seizures?",
        
        # Alcohol use (26-29)
        "Do you find it difficult to stop drinking once you start?",
        "Has a friend or family member ever told you about things you said or did while drinking that you could not remember?",
        "Do you ever feel you need to cut down on your drinking?",
        "Do you ever feel bad or guilty about your drinking?"
    ]
    
    # Combine SRQ-20 with additional questions for SRQ-29
    return srq20 + additional_questions

def calculate_srq20_score(answers):
    """Calculate SRQ-20 score from answers"""
    # Count 'Yes' responses (True values)
    return sum(1 for key, value in answers.items() if value and key.startswith("srq_") and int(key.split("_")[1]) <= 20)

def calculate_srq29_score(answers):
    """Calculate SRQ-29 score from answers"""
    # Count 'Yes' responses (True values)
    return sum(1 for key, value in answers.items() if value)

def get_srq29_subscale_scores(answers):
    """Get subscale scores for SRQ-29"""
    # Anxiety/depression (1-20)
    anxiety_depression = sum(1 for key, value in answers.items() if value and key.startswith("srq_") and 1 <= int(key.split("_")[1]) <= 20)
    
    # Psychotic symptoms (21-24)
    psychotic = sum(1 for key, value in answers.items() if value and key.startswith("srq_") and 21 <= int(key.split("_")[1]) <= 24)
    
    # Epileptic seizures (25)
    epileptic = 1 if answers.get("srq_25", False) else 0
    
    # Alcohol use (26-29)
    alcohol = sum(1 for key, value in answers.items() if value and key.startswith("srq_") and 26 <= int(key.split("_")[1]) <= 29)
    
    return {
        "anxiety_depression": anxiety_depression,
        "psychotic": psychotic,
        "epileptic": epileptic,
        "alcohol": alcohol
    }

def get_dass42_questions():
    """Get DASS-42 questions with their categories (depression, anxiety, stress)"""
    return [
        # Depression items (D)
        ("Depression", "I couldn't seem to experience any positive feeling at all"),
        ("Depression", "I found it difficult to work up the initiative to do things"),
        ("Depression", "I felt that I had nothing to look forward to"),
        ("Depression", "I felt sad and depressed"),
        ("Depression", "I was unable to become enthusiastic about anything"),
        ("Depression", "I felt I wasn't worth much as a person"),
        ("Depression", "I felt that life was meaningless"),
        ("Depression", "I couldn't seem to get any enjoyment out of the things I did"),
        ("Depression", "I felt down-hearted and blue"),
        ("Depression", "I was unable to become enthusiastic about anything"),
        ("Depression", "I felt I wasn't worth much as a person"),
        ("Depression", "I felt that life wasn't worthwhile"),
        ("Depression", "I couldn't seem to experience any positive feeling at all"),
        ("Depression", "I was unable to experience any positive feeling at all"),
        
        # Anxiety items (A)
        ("Anxiety", "I was aware of dryness of my mouth"),
        ("Anxiety", "I experienced breathing difficulty"),
        ("Anxiety", "I experienced trembling (e.g., in the hands)"),
        ("Anxiety", "I was worried about situations in which I might panic and make a fool of myself"),
        ("Anxiety", "I felt I was close to panic"),
        ("Anxiety", "I was aware of the action of my heart in the absence of physical exertion"),
        ("Anxiety", "I felt scared without any good reason"),
        ("Anxiety", "I had a feeling of shakiness"),
        ("Anxiety", "I was worried about situations in which I might panic"),
        ("Anxiety", "I found myself in situations that made me so anxious I was most relieved when they ended"),
        ("Anxiety", "I felt terrified"),
        ("Anxiety", "I felt afraid that I would be 'thrown' by some trivial but unfamiliar task"),
        ("Anxiety", "I felt afraid"),
        ("Anxiety", "I had feelings of panic"),
        
        # Stress items (S)
        ("Stress", "I found it hard to wind down"),
        ("Stress", "I tended to over-react to situations"),
        ("Stress", "I felt that I was using a lot of nervous energy"),
        ("Stress", "I found myself getting agitated"),
        ("Stress", "I found it difficult to relax"),
        ("Stress", "I was intolerant of anything that kept me from getting on with what I was doing"),
        ("Stress", "I felt that I was rather touchy"),
        ("Stress", "I found myself getting upset by quite trivial things"),
        ("Stress", "I found it hard to calm down after something upset me"),
        ("Stress", "I found it difficult to tolerate interruptions to what I was doing"),
        ("Stress", "I was in a state of nervous tension"),
        ("Stress", "I was unable to become patient when I was being delayed"),
        ("Stress", "I found myself getting upset rather easily"),
        ("Stress", "I found myself getting impatient when I was delayed in any way")
    ]

def calculate_dass42_scores(answers):
    """Calculate DASS-42 scores for depression, anxiety, and stress"""
    depression_score = 0
    anxiety_score = 0
    stress_score = 0
    
    # Categorize questions by their index positions
    # DASS-42 has 14 questions for each scale
    depression_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    anxiety_indices = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    stress_indices = [28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41]
    
    for i in range(1, 43):
        key = f"dass_{i}"
        score = answers.get(key, 0)
        
        # Adjust index to be 0-based for our lists
        idx = i - 1
        
        if idx in depression_indices:
            depression_score += score
        elif idx in anxiety_indices:
            anxiety_score += score
        elif idx in stress_indices:
            stress_score += score
    
    return depression_score, anxiety_score, stress_score
