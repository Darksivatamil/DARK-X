import json, random
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.services.ai_service import ai_service
from backend.models.simulation import SimulationMatch, AgentStats
from backend.config import logger

RED_AGENTS = [
    {'name': 'Blade', 'role': 'Assassin — Precision Striker', 'icon': '⚔️', 'color': '#ef4444',
     'attack': 85, 'defense': 40, 'speed': 75, 'special': 60, 'hp': 100,
     'special_move': 'Shadow Strike', 'special_desc': 'Bypasses one defense layer — guaranteed damage'},
    {'name': 'Hunter', 'role': 'Scout — Recon & OSINT', 'icon': '🔍', 'color': '#f97316',
     'attack': 65, 'defense': 55, 'speed': 90, 'special': 70, 'hp': 90,
     'special_move': "Tracker's Mark", 'special_desc': 'Reveals weaknesses, reducing enemy defense by 20%'},
    {'name': 'Inferno', 'role': 'Destroyer — Brute Force', 'icon': '🔥', 'color': '#dc2626',
     'attack': 95, 'defense': 30, 'speed': 40, 'special': 80, 'hp': 120,
     'special_move': 'Inferno Blast', 'special_desc': 'Multi-target attack that hits 2 defenders'},
    {'name': 'Phantom', 'role': 'Intelligence — Pattern Analysis', 'icon': '👻', 'color': '#7c3aed',
     'attack': 55, 'defense': 60, 'speed': 70, 'special': 90, 'hp': 80,
     'special_move': 'Ghost Protocol', 'special_desc': 'Predicts defender\'s move and counters perfectly'},
    {'name': 'Assassin', 'role': 'Execution — Finishing Moves', 'icon': '🗡️', 'color': '#991b1b',
     'attack': 90, 'defense': 35, 'speed': 85, 'special': 65, 'hp': 85,
     'special_move': 'Final Cut', 'special_desc': 'Critical damage against weakened defenders'},
    {'name': 'Warlock', 'role': 'Arcane — Cryptography', 'icon': '🔮', 'color': '#a21caf',
     'attack': 70, 'defense': 50, 'speed': 55, 'special': 95, 'hp': 95,
     'special_move': 'Void Curse', 'special_desc': 'Debuffs defender\'s stats by 30% for current round'},
    {'name': 'Summoner', 'role': 'Wild Card — Creative Attacks', 'icon': '🌀', 'color': '#d946ef',
     'attack': 60, 'defense': 45, 'speed': 65, 'special': 100, 'hp': 90,
     'special_move': 'Chaos Summon', 'special_desc': 'Unpredictable effect — can double attack or backfire'},
]

BLUE_AGENTS = [
    {'name': 'Shadow', 'role': 'Commander — Coordination', 'icon': '🌑', 'color': '#3b82f6',
     'attack': 40, 'defense': 75, 'speed': 70, 'special': 85, 'hp': 110,
     'special_move': 'Shadow Army', 'special_desc': 'Boosts all blue team defense by 15%'},
    {'name': 'Sentry', 'role': 'Guardian — Perimeter Defense', 'icon': '🛡️', 'color': '#2563eb',
     'attack': 30, 'defense': 90, 'speed': 55, 'special': 60, 'hp': 130,
     'special_move': 'Iron Wall', 'special_desc': 'Massive damage reduction for current round'},
    {'name': 'Titan', 'role': 'Fortress — Immovable', 'icon': '🏰', 'color': '#1d4ed8',
     'attack': 35, 'defense': 95, 'speed': 25, 'special': 50, 'hp': 150,
     'special_move': 'Unbreakable', 'special_desc': '40% chance to completely block an attack'},
    {'name': 'Specter', 'role': 'Stealth — Counter-Intel', 'icon': '🌫️', 'color': '#6b7280',
     'attack': 50, 'defense': 65, 'speed': 95, 'special': 75, 'hp': 85,
     'special_move': 'Phase Shift', 'special_desc': 'Evades detection — 30% chance to avoid attack'},
    {'name': 'Ranger', 'role': 'Long-Range — Monitoring', 'icon': '🎯', 'color': '#22c55e',
     'attack': 60, 'defense': 60, 'speed': 80, 'special': 65, 'hp': 90,
     'special_move': 'Eagle Eye', 'special_desc': 'Reveals attack vector — boosts defense against revealed type'},
    {'name': 'Engineer', 'role': 'Tech — System Hardening', 'icon': '🔧', 'color': '#06b6d4',
     'attack': 25, 'defense': 80, 'speed': 60, 'special': 70, 'hp': 100,
     'special_move': 'Fortify', 'special_desc': 'Hardens team — heals 20 HP to all blue agents'},
    {'name': 'Null', 'role': 'Support — Data Analysis', 'icon': '○', 'color': '#9ca3af',
     'attack': 20, 'defense': 70, 'speed': 65, 'special': 80, 'hp': 95,
     'special_move': 'System Purge', 'special_desc': 'Removes all debuffs from blue team and cleanses'},
]

OVERLORD = {
    'name': 'Overlord', 'role': 'Observer — Absolute Judgment', 'icon': '👑', 'color': '#eab308',
    'attack': 50, 'defense': 50, 'speed': 50, 'special': 100, 'hp': 200,
    'special_move': 'Absolute Judgment', 'special_desc': 'Score multiplier for dramatic moments'
}

SCENARIOS = {
    'web_app': {
        'title': 'Web Application Assault',
        'description': 'A heavily fortified web application with WAF, CSP, and input validation. Red team must breach through SQLi, XSS, and CSRF vectors.',
        'red_strategy': 'SQL Injection, XSS, CSRF, LFI, SSRF',
        'blue_strategy': 'WAF, Input Validation, CSP Headers, Rate Limiting'
    },
    'network_breach': {
        'title': 'Corporate Network Breach',
        'description': 'A segmented corporate network with firewalls, IDS/IPS, and strict access controls. Red team must pivot through multiple zones.',
        'red_strategy': 'Port Scanning, Exploitation, Pivoting, Lateral Movement',
        'blue_strategy': 'Firewall Rules, IDS Signatures, Network Segmentation'
    },
    'wireless': {
        'title': 'Wireless Infrastructure Attack',
        'description': 'A corporate wireless network with WPA3-Enterprise, 802.1X, and rogue AP detection systems.',
        'red_strategy': 'Deauth Attacks, Evil Twin, WPA Cracking, PMKID Attack',
        'blue_strategy': 'WPA3, 802.1X, Rogue AP Detection, Wireless IDS'
    },
    'cloud': {
        'title': 'Cloud Infrastructure Breach',
        'description': 'An AWS/GCP multi-cloud environment with IAM policies, buckets, and serverless functions.',
        'red_strategy': 'IAM Abuse, Bucket Enumeration, Lambda Injection, Metadata SSRF',
        'blue_strategy': 'CloudTrail, GuardDuty, IAM Policies, Security Groups'
    },
    'iot_botnet': {
        'title': 'IoT Botnet Takeover',
        'description': 'A network of 10,000+ IoT devices with a command-and-control infrastructure. Red team aims to establish C2 dominance.',
        'red_strategy': 'Mirai-style Exploits, C2 Establishment, DDoS, Propagation',
        'blue_strategy': 'Network Isolation, Anomaly Detection, Firmware Hardening'
    }
}

SIMULATION_COMBAT_PROMPT = """You are the DARK-X War Room Combat Engine. Generate a dramatic cyber battle round.

CONTEXT:
Scenario: {scenario_title} ({scenario})
Red Strategy: {red_strategy}
Blue Strategy: {blue_strategy}
Round: {round_num}/{max_rounds}
Current Score: Red {red_score} - Blue {blue_score}

ATTACKER: {attacker_name} ({attacker_role})
- Attack: {attacker_attack} | Speed: {attacker_speed} | Special: {attacker_special}
- Special Move: {attacker_special_move}

DEFENDER: {defender_name} ({defender_role})  
- Defense: {defender_defense} | Speed: {defender_speed} | Special: {defender_special}
- HP: {defender_hp}/{defender_max_hp}
- Special Move: {defender_special_move}

Generate a JSON response with:
- narrative: 2-3 paragraph dramatic description of the attack and defense
- attacker_action: what specific technique the attacker uses
- defender_action: what specific countermeasure the defender uses
- attack_roll: integer 1-100 (modified by attacker's attack stat)
- defense_roll: integer 1-100 (modified by defender's defense stat)
- winner: "red" or "blue"
- damage_dealt: integer 0-50
- special_used: true/false
- special_narrative: string describing the special move if used
- flavor_text: dramatic one-liner for the animation
- is_critical: true/false (for dramatic moments)
- is_perfect_defense: true/false (defense roll > attack roll by 30+)

Scoring rules:
- Winner gets +3 points if decisive (roll difference > 15), +2 if narrow
- Loser gets +1 if they kept it close (difference < 10)
- Critical hits add +1 bonus point
- Perfect defense adds +1 bonus point

Return ONLY valid JSON with no preamble."""


class SimulationService:
    def get_scenarios(self) -> Dict[str, Any]:
        return SCENARIOS

    def get_agent_definitions(self, include_overlord: bool = True) -> Dict[str, List]:
        return {
            'red': RED_AGENTS,
            'blue': BLUE_AGENTS,
            'overlord': OVERLORD if include_overlord else None
        }

    async def create_match(self, db: Session, user_id: int, scenario_key: str) -> SimulationMatch:
        scenario = SCENARIOS.get(scenario_key)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_key}")

        # Initialize agents with base stats
        red_agents = [self._init_agent(a, 'red') for a in RED_AGENTS]
        blue_agents = [self._init_agent(a, 'blue') for a in BLUE_AGENTS]

        match = SimulationMatch(
            user_id=user_id,
            scenario=scenario_key,
            scenario_title=scenario['title'],
            scenario_description=scenario['description'],
            status='in_progress',
            current_round=0,
            max_rounds=7,
            red_score=0,
            blue_score=0,
            red_agents_json=red_agents,
            blue_agents_json=blue_agents,
            round_history_json=[],
        )
        db.add(match)
        db.commit()
        db.refresh(match)

        # Initialize or update persistent agent stats
        self._ensure_agent_stats(db, user_id)

        # Update existing agent stats from any previous matches
        self._sync_agent_stats(db, user_id, match)

        return match

    def _init_agent(self, template: Dict, team: str) -> Dict:
        return {
            'name': template['name'],
            'role': template['role'],
            'icon': template['icon'],
            'color': template['color'],
            'team': team,
            'attack': template['attack'],
            'defense': template['defense'],
            'speed': template['speed'],
            'special': template['special'],
            'hp': template['hp'],
            'max_hp': template['hp'],
            'special_move': template['special_move'],
            'special_desc': template['special_desc'],
            'xp': 0,
            'wins': 0,
            'losses': 0,
            'kills': 0,
            'level': 1,
        }

    def _ensure_agent_stats(self, db: Session, user_id: int):
        for agents in [RED_AGENTS, BLUE_AGENTS]:
            for a in agents:
                existing = db.query(AgentStats).filter(
                    AgentStats.user_id == user_id,
                    AgentStats.agent_name == a['name']
                ).first()
                if not existing:
                    stats = AgentStats(
                        user_id=user_id,
                        agent_name=a['name'],
                        team='red' if a in RED_AGENTS else 'blue',
                        attack=a['attack'],
                        defense=a['defense'],
                        speed=a['speed'],
                        special=a['special'],
                        hp=a['hp'],
                        max_hp=a['hp'],
                        special_move=a['special_move'],
                    )
                    db.add(stats)
        db.commit()

    def _sync_agent_stats(self, db: Session, user_id: int, match: SimulationMatch):
        for team_key in ['red', 'blue']:
            agents_list = match.red_agents_json if team_key == 'red' else match.blue_agents_json
            for agent in agents_list:
                db_stats = db.query(AgentStats).filter(
                    AgentStats.user_id == user_id,
                    AgentStats.agent_name == agent['name']
                ).first()
                if db_stats:
                    agent['xp'] = db_stats.xp
                    agent['wins'] = db_stats.wins
                    agent['losses'] = db_stats.losses
                    agent['kills'] = db_stats.kills
                    agent['level'] = db_stats.level
                    # Apply accumulated stat bonuses from XP
                    bonus_stats = self._calculate_bonus_stats(db_stats.xp)
                    agent['attack'] = min(100, db_stats.attack + bonus_stats['attack'])
                    agent['defense'] = min(100, db_stats.defense + bonus_stats['defense'])
                    agent['speed'] = min(100, db_stats.speed + bonus_stats['speed'])
                    agent['special'] = min(100, db_stats.special + bonus_stats['special'])
                    agent['hp'] = min(200, db_stats.hp + bonus_stats['hp'] * 10)
                    agent['max_hp'] = agent['hp']

    def _calculate_bonus_stats(self, total_xp: int) -> Dict[str, int]:
        levels = total_xp // 100
        return {
            'attack': levels // 4,
            'defense': levels // 4,
            'speed': levels // 6,
            'special': levels // 5,
            'hp': levels // 8,
        }

    async def run_round(self, db: Session, match_id: int, user_id: int) -> Dict[str, Any]:
        match = db.query(SimulationMatch).filter(
            SimulationMatch.id == match_id,
            SimulationMatch.user_id == user_id
        ).first()
        if not match:
            return {'error': 'Match not found'}
        if match.status != 'in_progress':
            return {'error': f'Match is already {match.status}'}

        # Check if match is over (one team has 4+)
        if match.red_score >= 4 or match.blue_score >= 4:
            return await self._finish_match(db, match)

        match.current_round += 1
        round_num = match.current_round
        max_rounds = match.max_rounds
        scenario = SCENARIOS.get(match.scenario, {})

        # Pick agents — cycle through teams
        attacker = self._pick_attacker(match)
        defender = self._pick_defender(match)

        if not attacker or not defender:
            return {'error': 'No available agents'}

        # Build AI prompt
        prompt = SIMULATION_COMBAT_PROMPT.format(
            scenario_title=match.scenario_title,
            scenario=match.scenario,
            red_strategy=scenario.get('red_strategy', ''),
            blue_strategy=scenario.get('blue_strategy', ''),
            round_num=round_num,
            max_rounds=max_rounds,
            red_score=match.red_score,
            blue_score=match.blue_score,
            attacker_name=attacker['name'],
            attacker_role=attacker['role'],
            attacker_attack=attacker['attack'],
            attacker_speed=attacker['speed'],
            attacker_special=attacker['special'],
            attacker_special_move=attacker['special_move'],
            defender_name=defender['name'],
            defender_role=defender['role'],
            defender_defense=defender['defense'],
            defender_speed=defender['speed'],
            defender_special=defender['special'],
            defender_hp=defender['hp'],
            defender_max_hp=defender['max_hp'],
            defender_special_move=defender['special_move'],
        )

        try:
            result = await ai_service.generate_structured_json(
                "You are the DARK-X War Room Combat Engine. Return ONLY valid JSON.",
                prompt
            )
        except Exception as e:
            logger.error(f"AI round generation failed: {e}")
            result = self._fallback_round(attacker, defender)

        # Parse and validate the result
        attack_roll = result.get('attack_roll', random.randint(1, 100))
        defense_roll = result.get('defense_roll', random.randint(1, 100))

        # Apply stat bonuses
        modified_attack = attack_roll + (attacker['attack'] // 5)
        modified_defense = defense_roll + (defender['defense'] // 5)

        # Apply special if used
        if result.get('special_used'):
            if attacker.get('special_move') == 'Shadow Strike':
                modified_defense *= 0.6
            elif attacker.get('special_move') == "Tracker's Mark":
                modified_defense *= 0.8
            elif attacker.get('special_move') == 'Inferno Blast':
                modified_attack *= 1.3
            elif attacker.get('special_move') == 'Ghost Protocol':
                modified_attack += 25
            elif attacker.get('special_move') == 'Final Cut':
                if defender['hp'] < defender['max_hp'] * 0.5:
                    modified_attack *= 1.5
            elif attacker.get('special_move') == 'Void Curse':
                modified_defense *= 0.7
            elif attacker.get('special_move') == 'Chaos Summon':
                modified_attack *= random.choice([0.5, 1.0, 2.0])
            elif defender.get('special_move') == 'Iron Wall':
                modified_attack *= 0.5
            elif defender.get('special_move') == 'Unbreakable':
                if random.random() < 0.4:
                    modified_defense = 999
            elif defender.get('special_move') == 'Phase Shift':
                if random.random() < 0.3:
                    modified_defense += 50
            elif defender.get('special_move') == 'Shadow Army':
                modified_defense *= 1.15
            elif defender.get('special_move') == 'Eagle Eye':
                modified_defense *= 1.2
            elif defender.get('special_move') == 'Fortify':
                for ba in match.blue_agents_json:
                    ba['hp'] = min(ba['max_hp'], ba['hp'] + 20)

        # Determine winner
        is_critical = result.get('is_critical', False) or abs(modified_attack - modified_defense) > 40
        is_perfect_defense = result.get('is_perfect_defense', False) or (modified_defense - modified_attack > 30)

        if modified_attack > modified_defense:
            winner = 'red'
            damage = min(50, max(10, (modified_attack - modified_defense) // 2))
            defender['hp'] = max(0, defender['hp'] - damage)
            is_kill = defender['hp'] <= 0
            if is_kill:
                attacker['kills'] += 1
            attacker['wins'] += 1
            defender['losses'] += 1
        else:
            winner = 'blue'
            damage = min(30, max(5, (modified_defense - modified_attack) // 3))
            attacker['hp'] = max(0, attacker['hp'] - damage)
            is_kill = attacker['hp'] <= 0
            if is_kill:
                defender['kills'] += 1
            defender['wins'] += 1
            attacker['losses'] += 1

        # Calculate scores
        score_diff = abs(modified_attack - modified_defense)
        if winner == 'red':
            round_points_winner = 3 if score_diff > 15 else 2
            round_points_loser = 1 if score_diff < 10 else 0
            match.red_score += round_points_winner
            match.blue_score += round_points_loser
            if is_critical:
                match.red_score += 1
            attacker['xp'] += round_points_winner * 10
            defender['xp'] += round_points_loser * 5
        else:
            round_points_winner = 3 if score_diff > 15 else 2
            round_points_loser = 1 if score_diff < 10 else 0
            match.blue_score += round_points_winner
            match.red_score += round_points_loser
            if is_perfect_defense:
                match.blue_score += 1
            defender['xp'] += round_points_winner * 10
            attacker['xp'] += round_points_loser * 5

        is_kill = (winner == 'red' and defender['hp'] <= 0) or (winner == 'blue' and attacker['hp'] <= 0)

        round_data = {
            'round': round_num,
            'attacker': {'name': attacker['name'], 'icon': attacker['icon'], 'color': attacker['color']},
            'defender': {'name': defender['name'], 'icon': defender['icon'], 'color': defender['color']},
            'attacker_action': result.get('attacker_action', f"Launches a {random.choice(['targeted', 'swift', 'calculated'])} attack"),
            'defender_action': result.get('defender_action', f"Deploys {random.choice(['standard', 'reinforced', 'adaptive'])} defenses"),
            'attack_roll': modified_attack,
            'defense_roll': modified_defense,
            'winner': winner,
            'damage_dealt': damage,
            'is_kill': is_kill,
            'is_critical': is_critical,
            'is_perfect_defense': is_perfect_defense,
            'special_used': result.get('special_used', False),
            'special_narrative': result.get('special_narrative', ''),
            'narrative': result.get('narrative', 'The battle rages on as both sides trade blows.'),
            'flavor_text': result.get('flavor_text', f'A decisive moment in round {round_num}!'),
            'score_after': {'red': match.red_score, 'blue': match.blue_score},
            'attacker_hp_after': attacker['hp'],
            'defender_hp_after': defender['hp'],
        }

        history = list(match.round_history_json)
        history.append(round_data)
        match.round_history_json = history

        # Update agents in match
        self._update_agent_in_list(match.red_agents_json, attacker)
        self._update_agent_in_list(match.blue_agents_json, defender)

        # Check if match is over
        if match.red_score >= 4 or match.blue_score >= 4:
            await self._finish_match(db, match, commit=False)
        elif round_num >= max_rounds:
            # Higher score wins, or draw
            if match.red_score > match.blue_score:
                match.winner = 'red'
            elif match.blue_score > match.red_score:
                match.winner = 'blue'
            else:
                match.winner = 'draw'
            match.status = 'completed'

        # Persist agent stats
        self._persist_agent_stats(db, user_id, match)

        db.commit()
        db.refresh(match)

        return self._serialize_match(match)

    def _pick_attacker(self, match: SimulationMatch) -> Optional[Dict]:
        # Pick the red agent with the lowest usage in this match
        usage = {}
        for r in match.round_history_json:
            aname = r.get('attacker', {}).get('name')
            if aname:
                usage[aname] = usage.get(aname, 0) + 1

        best = None
        best_count = float('inf')
        for agent in match.red_agents_json:
            if agent['hp'] <= 0:
                continue
            count = usage.get(agent['name'], 0)
            if count < best_count or (count == best_count and agent['attack'] > (best or {}).get('attack', 0)):
                best = agent
                best_count = count
        return best

    def _pick_defender(self, match: SimulationMatch) -> Optional[Dict]:
        usage = {}
        for r in match.round_history_json:
            dname = r.get('defender', {}).get('name')
            if dname:
                usage[dname] = usage.get(dname, 0) + 1

        best = None
        best_count = float('inf')
        for agent in match.blue_agents_json:
            if agent['hp'] <= 0:
                continue
            count = usage.get(agent['name'], 0)
            if count < best_count or (count == best_count and agent['defense'] > (best or {}).get('defense', 0)):
                best = agent
                best_count = count
        return best

    def _update_agent_in_list(self, agent_list: List[Dict], updated_agent: Dict):
        for i, a in enumerate(agent_list):
            if a['name'] == updated_agent['name']:
                agent_list[i] = updated_agent
                break

    def _persist_agent_stats(self, db: Session, user_id: int, match: SimulationMatch):
        for team_key in ['red', 'blue']:
            agents_list = match.red_agents_json if team_key == 'red' else match.blue_agents_json
            for agent in agents_list:
                db_stats = db.query(AgentStats).filter(
                    AgentStats.user_id == user_id,
                    AgentStats.agent_name == agent['name']
                ).first()
                if db_stats:
                    db_stats.xp = agent.get('xp', db_stats.xp)
                    db_stats.wins = agent.get('wins', db_stats.wins)
                    db_stats.losses = agent.get('losses', db_stats.losses)
                    db_stats.kills = agent.get('kills', db_stats.kills)
                    db_stats.level = 1 + (db_stats.xp // 200)

    async def _finish_match(self, db: Session, match: SimulationMatch, commit: bool = True):
        if match.red_score >= 4:
            match.winner = 'red'
        elif match.blue_score >= 4:
            match.winner = 'blue'
        else:
            if match.red_score > match.blue_score:
                match.winner = 'red'
            elif match.blue_score > match.red_score:
                match.winner = 'blue'
            else:
                match.winner = 'draw'
        match.status = 'completed'
        from datetime import datetime
        match.completed_at = datetime.utcnow()
        if commit:
            db.commit()

    def _fallback_round(self, attacker: Dict, defender: Dict) -> Dict:
        return {
            'narrative': f'The digital battlefield trembles as {attacker["name"]} clashes with {defender["name"]}. Both systems trade blows in a heated exchange of cyber firepower.',
            'attacker_action': f'{attacker["name"]} launches a precision attack',
            'defender_action': f'{defender["name"]} activates defensive countermeasures',
            'attack_roll': random.randint(40, 90) + (attacker['attack'] // 10),
            'defense_roll': random.randint(40, 90) + (defender['defense'] // 10),
            'winner': 'red' if random.random() > 0.5 else 'blue',
            'damage_dealt': random.randint(10, 35),
            'special_used': random.random() > 0.7,
            'special_narrative': '',
            'flavor_text': 'The battle continues with no clear advantage!',
            'is_critical': False,
            'is_perfect_defense': False,
        }

    def get_match(self, db: Session, match_id: int, user_id: int) -> Optional[Dict]:
        match = db.query(SimulationMatch).filter(
            SimulationMatch.id == match_id,
            SimulationMatch.user_id == user_id
        ).first()
        if not match:
            return None
        return self._serialize_match(match)

    def get_agent_stats(self, db: Session, user_id: int) -> List[Dict]:
        stats = db.query(AgentStats).filter(AgentStats.user_id == user_id).all()
        return [{
            'agent_name': s.agent_name,
            'team': s.team,
            'attack': s.attack,
            'defense': s.defense,
            'speed': s.speed,
            'special': s.special,
            'hp': s.hp,
            'max_hp': s.max_hp,
            'xp': s.xp,
            'level': 1 + (s.xp // 200),
            'wins': s.wins,
            'losses': s.losses,
            'kills': s.kills,
            'special_move': s.special_move,
        } for s in stats]

    def upgrade_agent(self, db: Session, user_id: int, agent_name: str, stat: str) -> Dict[str, Any]:
        db_stats = db.query(AgentStats).filter(
            AgentStats.user_id == user_id,
            AgentStats.agent_name == agent_name
        ).first()
        if not db_stats:
            return {'error': f'Agent {agent_name} not found'}

        costs = {'attack': 100, 'defense': 100, 'speed': 150, 'special': 200, 'hp': 80}
        max_values = {'attack': 100, 'defense': 100, 'speed': 100, 'special': 100, 'hp': 200}

        cost = costs.get(stat)
        max_val = max_values.get(stat)

        if not cost:
            return {'error': f'Unknown stat: {stat}'}

        if db_stats.xp < cost:
            return {'error': f'Not enough XP. Need {cost}, have {db_stats.xp}'}

        current_val = getattr(db_stats, stat)
        if current_val >= max_val:
            return {'error': f'{stat} is already at maximum ({max_val})'}

        db_stats.xp -= cost
        setattr(db_stats, stat, current_val + (10 if stat == 'hp' else 1))

        # Also upgrade the special move at thresholds
        if db_stats.xp >= 500 and not db_stats.special_move_unlocked:
            db_stats.special_move_unlocked = db_stats.special_move

        db.commit()

        return {
            'success': True,
            'agent_name': agent_name,
            'stat': stat,
            'new_value': getattr(db_stats, stat),
            'remaining_xp': db_stats.xp,
            'level': 1 + (db_stats.xp // 200),
        }

    def get_match_history(self, db: Session, user_id: int, limit: int = 10) -> List[Dict]:
        matches = db.query(SimulationMatch).filter(
            SimulationMatch.user_id == user_id
        ).order_by(desc(SimulationMatch.created_at)).limit(limit).all()
        return [self._serialize_match(m) for m in matches]

    def _serialize_match(self, match: SimulationMatch) -> Dict:
        return {
            'id': match.id,
            'scenario': match.scenario,
            'scenario_title': match.scenario_title,
            'scenario_description': match.scenario_description,
            'status': match.status,
            'current_round': match.current_round,
            'max_rounds': match.max_rounds,
            'red_score': match.red_score,
            'blue_score': match.blue_score,
            'red_kills': match.red_kills,
            'blue_kills': match.blue_kills,
            'red_agents': match.red_agents_json,
            'blue_agents': match.blue_agents_json,
            'round_history': match.round_history_json,
            'winner': match.winner,
            'created_at': match.created_at.isoformat() if match.created_at else None,
            'completed_at': match.completed_at.isoformat() if match.completed_at else None,
        }


simulation_service = SimulationService()
