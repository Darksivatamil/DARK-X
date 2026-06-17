import json, random, hashlib
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.task import DailyTask, TaskSubmission
from backend.models.progress import UserProgress
from backend.services.ai_service import ai_service
from backend.services.gamification import gamification_service
from backend.services.memory_service import memory_service
from backend.config import logger

TRACK_NAMES = {
    'python': {'name': 'Python Engineering', 'icon': '🐍'},
    'kali': {'name': 'Kali Linux Mastery', 'icon': '🐉'},
    'ai': {'name': 'AI & Machine Learning', 'icon': '🧠'},
    'skill': {'name': 'Industry Skill Upgrader', 'icon': '🚀'},
}

DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced', 'Expert', 'Master']
EASE_RATINGS = ['Very Easy', 'Easy', 'Medium', 'Hard', 'Very Hard']

FALLBACK_TASKS = [
    {
        'track': 'python',
        'difficulty': 'Intermediate',
        'difficulty_score': 5,
        'title': 'Subdomain Enumeration Tool',
        'description': 'Build a Python subdomain enumerator using DNS resolution with threading.',
        'full_question': 'Write a Python script that takes a domain name as input, reads a wordlist of subdomains, and performs DNS A-record lookups concurrently. Output only valid subdomains with their resolved IPs. Use threading for speed, handle DNS timeouts gracefully, and display results in a formatted table.',
        'what_wanted': 'A working CLI tool for subdomain enumeration with thread pool, timeout handling, and clean output formatting.',
        'what_we_learn': 'DNS resolution, threading, socket programming, CLI tool design',
        'time_estimate': '30 min',
        'ease_rating': 'Medium',
        'xp_reward': 150,
        'powers_reward': 'Shadow Sight',
        'tags': ['dns', 'enumeration', 'threading', 'python'],
    },
    {
        'track': 'kali',
        'difficulty': 'Intermediate',
        'difficulty_score': 5,
        'title': 'Network Traffic Capture Analysis',
        'description': 'Use tcpdump and Wireshark CLI to capture and analyze suspicious traffic.',
        'full_question': 'Simulate a network capture session: capture 100 packets on an interface, filter for HTTP traffic, extract all unique IP pairs, identify any port scanning behavior (multiple ports from single IP in <1s), and generate a summary report of suspicious activities.',
        'what_wanted': 'A command sequence and analysis report showing captured packets, identified scan patterns, and suspicious connections.',
        'what_we_learn': 'tcpdump syntax, PCAP analysis, traffic pattern detection, reporting',
        'time_estimate': '45 min',
        'ease_rating': 'Medium',
        'xp_reward': 200,
        'powers_reward': 'Echo Memory',
        'tags': ['tcpdump', 'wireshark', 'network', 'forensics'],
    },
    {
        'track': 'ai',
        'difficulty': 'Advanced',
        'difficulty_score': 7,
        'title': 'ML-Based Email Classifier',
        'description': 'Train a machine learning model to classify emails as phishing or legitimate.',
        'full_question': 'Build and train a text classification model using scikit-learn that distinguishes phishing emails from legitimate ones. Extract features: presence of urgency words, suspicious links count, sender reputation score. Compare Logistic Regression vs Random Forest. Report precision, recall, F1-score.',
        'what_wanted': 'A Jupyter notebook or Python script with feature extraction, model training, evaluation metrics, and comparison visualization.',
        'what_we_learn': 'NLP feature extraction, text classification, model evaluation, scikit-learn',
        'time_estimate': '60 min',
        'ease_rating': 'Hard',
        'xp_reward': 300,
        'powers_reward': 'Binary Whisper',
        'tags': ['nlp', 'machine-learning', 'phishing', 'classification'],
    },
    {
        'track': 'skill',
        'difficulty': 'Beginner',
        'difficulty_score': 3,
        'title': 'Personal Security Audit Checklist',
        'description': 'Create a comprehensive personal digital security audit checklist.',
        'full_question': 'Design a personal digital security audit framework covering: password hygiene (manager usage, complexity, reuse), 2FA adoption, browser security (extensions, update status), social media privacy settings, device encryption status, and backup strategy. Score each category and provide improvement recommendations.',
        'what_wanted': 'A self-assessment checklist with scoring rubric, current status evaluation, and prioritized action items.',
        'what_we_learn': 'Security best practices, risk assessment, privacy hardening, audit methodology',
        'time_estimate': '25 min',
        'ease_rating': 'Easy',
        'xp_reward': 100,
        'powers_reward': 'Ghost Ping',
        'tags': ['security', 'audit', 'privacy', 'best-practices'],
    },
]

RANDOM_EVENTS = [
    {"name": "System Breach Alert", "desc": "Anomalous traffic detected! Trace the intrusion source.", "xp": 500, "power": "Neural Link"},
    {"name": "Dark Web Signal", "desc": "A hidden marketplace leaks credentials. Decrypt and analyze.", "xp": 400, "power": "Cipher Eye"},
    {"name": "Zero-Day Race", "desc": "A critical CVE drops. Build a detection rule before attackers exploit it.", "xp": 600, "power": "Dragon Eye"},
    {"name": "Ghost in the Machine", "desc": "An AI agent goes rogue. Debug and neutralize the anomaly.", "xp": 350, "power": "Iron Code"},
    {"name": "Quantum Anomaly", "desc": "Unusual quantum signatures detected. Investigate the encrypted channel.", "xp": 450, "power": "Quantum Leap"},
    {"name": "Shadow Protocol", "desc": "A classified document fragment is found. Reconstruct and verify.", "xp": 500, "power": "Stealth Mode"},
    {"name": "Botnet Uprising", "desc": "5000 IoT devices are compromised. Coordinate a takedown strategy.", "xp": 550, "power": "Shadow Army"},
    {"name": "Crypto Heist", "desc": "A DeFi protocol is under attack. Trace the transaction chain.", "xp": 400, "power": "Omega Compile"},
]


def _date_seed(user_id: int) -> str:
    today = date.today().isoformat()
    return hashlib.md5(f"{user_id}-{today}".encode()).hexdigest()


def _pick_by_seed(items: list, seed: str, count: int = 1):
    rng = random.Random(seed)
    return rng.sample(items, min(count, len(items)))


def _difficulty_for_level(level: int) -> tuple:
    idx = min(level // 20, 4)
    return DIFFICULTIES[idx], EASE_RATINGS[idx], max(1, round(level / 10, 1))


class TaskService:
    async def generate_daily_tasks(self, db: Session, user_id: int = None) -> List[DailyTask]:
        """Generate today's tasks — AI-generated if available, fallback templates otherwise."""
        db.query(DailyTask).filter(DailyTask.is_random_event == False).delete()

        user_level = 1
        user_xp = 0
        completed_tasks = []
        if user_id:
            progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
            if progress:
                user_level = progress.overall_level
                user_xp = progress.total_xp
                subs = db.query(TaskSubmission).filter(TaskSubmission.user_id == user_id).all()
                completed_tasks = [s.task_id for s in subs]

        difficulty, ease, diff_score = _difficulty_for_level(user_level)
        date_str = date.today().isoformat()
        seed = _date_seed(user_id or 1)

        tracks = ['python', 'kali', 'ai', 'skill']
        generated = []

        for track in tracks:
            track_name = TRACK_NAMES[track]['name']
            task = None

            if ai_service.is_available():
                ai_task_data = await ai_service.generate_task_for_track(track, track_name, user_level, date_str)
                if ai_task_data and 'title' in ai_task_data:
                    task = self._task_from_ai_data(ai_task_data, track, user_level, seed)
                else:
                    task = self._fallback_task(track, user_level, seed)
            else:
                task = self._fallback_task(track, user_level, seed)

            if task:
                db.add(task)
                generated.append(task)

        db.commit()
        logger.info(f"Generated {len(generated)} daily tasks for user {user_id}")
        return generated

    def _task_from_ai_data(self, data: dict, track: str, user_level: int, seed: str) -> DailyTask:
        difficulty = data.get('difficulty', DIFFICULTIES[min(user_level // 20, 4)])
        diff_score = data.get('difficulty_score', max(1, round(user_level / 10, 1)))
        ease = data.get('ease_rating', EASE_RATINGS[min(user_level // 20, 4)])
        rng = random.Random(seed + track)
        xp = data.get('xp_reward', user_level * 50 + rng.randint(50, 150))
        powers = ["Shadow Sight", "Echo Memory", "Binary Whisper", "Ghost Ping", "Data Leech",
                  "Neural Link", "Cipher Eye", "Dragon Eye", "Iron Code", "Stealth Mode"]
        return DailyTask(
            track=track,
            difficulty=difficulty,
            difficulty_score=diff_score,
            title=data.get('title', 'Security Challenge'),
            description=data.get('description', 'Complete this challenge to earn XP.'),
            based_on=data.get('based_on', 'AI-Generated Challenge'),
            full_question=data.get('full_question', 'Use your skills to complete this task.'),
            what_wanted=data.get('what_wanted', 'Submit your working solution.'),
            what_we_learn=data.get('what_we_learn', 'Security concepts, problem solving'),
            time_estimate=data.get('time_estimate', '30 min'),
            ease_rating=ease,
            powers_reward=f"Unlocks: {rng.choice(powers)}",
            xp_reward=xp,
            learning_objectives=data.get('what_we_learn', 'Security skills'),
            tags=data.get('tags', [track]),
            is_random_event=False,
        )

    def _fallback_task(self, track: str, user_level: int, seed: str) -> DailyTask:
        rng = random.Random(seed + track)
        template = rng.choice([t for t in FALLBACK_TASKS if t['track'] == track])
        difficulty, ease, diff_score = _difficulty_for_level(user_level)
        xp = template['xp_reward'] + user_level * 10
        return DailyTask(
            track=track,
            difficulty=difficulty,
            difficulty_score=diff_score,
            title=template['title'],
            description=template['description'],
            based_on='Built-in Challenge',
            full_question=template['full_question'],
            what_wanted=template['what_wanted'],
            what_we_learn=template['what_we_learn'],
            time_estimate=template['time_estimate'],
            ease_rating=ease,
            powers_reward=template['powers_reward'],
            xp_reward=xp,
            learning_objectives=template['what_we_learn'],
            tags=template['tags'],
            is_random_event=False,
        )

    async def generate_random_event_task(self, db: Session, user_id: int = None) -> Optional[DailyTask]:
        """Generate a random event task on login or tasks tab visit (25% chance)."""
        if random.random() > 0.25:
            return None

        event = random.choice(RANDOM_EVENTS)
        user_level = 1
        if user_id:
            progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
            if progress:
                user_level = progress.overall_level

        xp = event['xp'] + user_level * 20
        task = DailyTask(
            track='event',
            difficulty='Expert',
            difficulty_score=min(10, user_level / 5 + 3),
            title=f"⚡ RANDOM EVENT: {event['name']}",
            description=f"⚠️ URGENT: {event['desc']}",
            based_on='Live Security Event',
            full_question=event['desc'],
            what_wanted='Complete the challenge to earn bonus XP and rare power',
            what_we_learn='Real-world incident response, adaptive thinking, crisis management',
            time_estimate='45 min',
            ease_rating='Hard',
            powers_reward=f'Unlocks: {event["power"]}',
            xp_reward=xp,
            learning_objectives='Incident response, crisis management',
            tags=['event', 'random', 'bonus'],
            is_random_event=True,
            event_name=event['name'],
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(task)
        db.commit()
        logger.info(f"Random event '{event['name']}' generated for user {user_id}")
        return task

    async def grade_submission(self, db: Session, user_id: int, task_id: int, code: str) -> dict:
        task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
        if not task:
            return {"error": "Task not found"}

        if ai_service.is_available():
            result = await ai_service.grade_submission(
                task.title, task.track, task.difficulty,
                task.full_question, task.what_wanted, code
            )
        else:
            result = {
                "score": random.randint(60, 100),
                "feedback": "Submission received. AI grading unavailable — assigned estimated score.",
                "is_correct": True,
                "strengths": ["Submitted on time"],
                "improvements": ["Configure AI API keys for detailed feedback"]
            }

        try:
            score = min(100, max(0, result.get("score", 85)))
            feedback = result.get("feedback", "Good effort!")
            xp_earned = int(task.xp_reward * (score / 100))

            submission = TaskSubmission(
                user_id=user_id,
                task_id=task_id,
                submitted_code=code,
                score=score,
                feedback=feedback,
                xp_earned=xp_earned
            )
            db.add(submission)
            db.commit()

            result_data = gamification_service.add_xp(db, user_id, xp_earned)
            await memory_service.add_to_working_memory(user_id, 'task_master', 'assistant',
                f"User completed task '{task.title}' with score {score}/100, earned {xp_earned} XP")

            return {
                "score": score,
                "feedback": feedback,
                "xp_earned": xp_earned,
                "is_correct": result.get("is_correct", score > 60),
                "strengths": result.get("strengths", []),
                "improvements": result.get("improvements", []),
                "leveled_up": result_data.get("leveled_up", False),
                "new_level": result_data.get("new_level"),
                "new_power": result_data.get("new_power"),
            }
        except Exception as e:
            return {"error": f"Grading failed: {e}"}

    def check_and_expire_tasks(self, db: Session):
        now = datetime.utcnow()
        expired = db.query(DailyTask).filter(
            DailyTask.expires_at.isnot(None),
            DailyTask.expires_at < now
        ).all()
        for t in expired:
            db.delete(t)
        db.commit()
        if expired:
            logger.info(f"Expired {len(expired)} random event tasks")

task_service = TaskService()
