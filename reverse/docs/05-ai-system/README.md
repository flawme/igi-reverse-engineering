# 05 - AI System

## Architecture (Inferred)

**Confidence:** LOW - The AI system architecture is inferred from string analysis and standard game patterns. The actual implementation may differ significantly.

The game appears to use an event-driven AI system. The term "behavior trees" is used in previous documentation, but this is an assumption based on common game AI patterns. The actual implementation could be state machines, rule-based systems, or other patterns.

## Events (22 total)

**Confidence:** MEDIUM - Event names extracted from string analysis, but event parameters and behavior are unknown.

| Event | Description | Confidence | Method |
|-------|-------------|------------|--------|
| AIEVENT_CREATE | Entity created | MEDIUM | String analysis |
| AIEVENT_DELETE | Entity destroyed | MEDIUM | String analysis |
| AIEVENT_IDLE | Idle state | MEDIUM | String analysis |
| AIEVENT_WALK | Walking | MEDIUM | String analysis |
| AIEVENT_COMBAT | In combat | MEDIUM | String analysis |
| AIEVENT_DEAD | Entity dead | MEDIUM | String analysis |
| AIEVENT_GUNSHOT | Gunshot heard | MEDIUM | String analysis |
| AIEVENT_GUNSHOTMISS | Missed shot heard | MEDIUM | String analysis |
| AIEVENT_EXPLOSION | Explosion heard | MEDIUM | String analysis |
| AIEVENT_TAKINGDAMAGE | Taking damage | MEDIUM | String analysis |
| AIEVENT_ENEMYDETECTION | Enemy detected | MEDIUM | String analysis |
| AIEVENT_FRIENDLYDETECTION | Friendly detected | MEDIUM | String analysis |
| AIEVENT_ALERT | Alert state | MEDIUM | String analysis |
| AIEVENT_ALERT_RESPONSE | Response to alert | MEDIUM | String analysis |
| AIEVENT_ALARMON | Alarm activated | MEDIUM | String analysis |
| AIEVENT_ALARMOFF | Alarm deactivated | MEDIUM | String analysis |
| AIEVENT_FLASHBANG | Flashbang effect | MEDIUM | String analysis |
| AIEVENT_GRENADETHROWN | Grenade thrown | MEDIUM | String analysis |
| AIEVENT_GRENADELAND | Grenade landed | MEDIUM | String analysis |
| AIEVENT_GROUNDIMPACT | Ground impact | MEDIUM | String analysis |
| AIEVENT_DOOR | Door interaction | MEDIUM | String analysis |
| AIEVENT_FENCE | Fence interaction | MEDIUM | String analysis |
| AIEVENT_LADDER | Ladder interaction | MEDIUM | String analysis |
| AIEVENT_ANIMATION | Animation event | MEDIUM | String analysis |

## Actions (17 total)

**Confidence:** MEDIUM - Action names extracted from string analysis, but action parameters and behavior are unknown.

| Action | Description | Confidence | Method |
|--------|-------------|------------|--------|
| AIAction_Idle | Do nothing | MEDIUM | String analysis |
| AIAction_WalkToNode | Walk to waypoint | MEDIUM | String analysis |
| AIAction_RunToNode | Run to waypoint | MEDIUM | String analysis |
| AIAction_MoveToEvent | Move to event location | MEDIUM | String analysis |
| AIAction_FireAtNode | Fire at waypoint | MEDIUM | String analysis |
| AIAction_FireAtTask | Fire at target entity | MEDIUM | String analysis |
| AIAction_Combat | Enter combat mode | MEDIUM | String analysis |
| AIAction_SetCombat | Set combat state | MEDIUM | String analysis |
| AIAction_Die | Die | MEDIUM | String analysis |
| AIAction_FallFlat | Fall down | MEDIUM | String analysis |
| AIAction_Stunned | Stunned state | MEDIUM | String analysis |
| AIAction_Patrol | Patrol area | MEDIUM | String analysis |
| AIAction_PlayAnimation | Play animation | MEDIUM | String analysis |
| AIAction_PlaySound | Play sound | MEDIUM | String analysis |
| AIAction_RunPanicking | Run in panic | MEDIUM | String analysis |
| AIAction_KickGrenade | Kick grenade away | MEDIUM | String analysis |
| AIAction_LookAtEvent | Look at event | MEDIUM | String analysis |
| AIAction_Activate | Activate object | MEDIUM | String analysis |

## Behavior Tree Node Types (Guessed)

**Confidence:** LOW - These node types are assumed from standard behavior tree patterns.

| Type | Description | Confidence |
|------|-------------|------------|
| Sequence | Execute children in order | LOW - Assumed |
| Selector | Execute children until one succeeds | LOW - Assumed |
| Condition | Check if condition is true | LOW - Assumed |
| Action | Execute an action | LOW - Assumed |

## Example: Guard Behavior (Reconstructed)

**Confidence:** LOW - This is pseudocode reconstructed from string analysis, not actual game behavior.

```
Selector
├── Sequence: Alert
│   ├── Condition: PlayerSpotted
│   ├── Action: GORadio("enemy_spotted")
│   └── Action: GOAttack(player)
├── Sequence: Patrol
│   ├── Condition: HasPatrolPoints
│   ├── Action: GOMoveTo(patrol_point)
│   └── Action: GORotate(random_angle)
└── Sequence: Idle
    ├── Action: GOAnimate("idle")
    └── Action: GOSound("ambient")
```

## NPC Types (From QVM scripts)

| Type | Script | Description | Confidence | Method |
|------|--------|-------------|------------|--------|
| GUARD_AK/PISTOL/SPAS/UZI | guard.qvm | Stationary guards with alarm system | MEDIUM | Filename + content |
| PATROL_AK/PISTOL/SPAS/UZI | patrol.qvm | Patrolling guards | MEDIUM | Filename + content |
| GUNNER | gunner.qvm | Vehicle/fortification gunners | MEDIUM | Filename + content |
| SNIPER | sniper.qvm | Long-range snipers | MEDIUM | Filename + content |
| RPG | rpg.qvm | Rocket launcher soldiers | MEDIUM | Filename + content |
| CIVILIAN | civilian.qvm | Panicking civilians | MEDIUM | Filename + content |
| PRIBOI/EKK/ANYA | priboi.qvm/ekk.qvm/anya.qvm | Named characters | MEDIUM | Filename + content |

## NPC Statistics (Guessed)

**Warning:** These values are guesses based on standard FPS conventions. The actual values are unknown.

| NPC Type | Health | Weapon | Damage | Confidence |
|----------|--------|--------|--------|------------|
| Guard | 100 | Rifle | 10 | LOW - Guessed |
| Sniper | 80 | Sniper rifle | 50 | LOW - Guessed |
| Civilian | 50 | None | 0 | LOW - Guessed |
| Vehicle | 500 | Mounted gun | 25 | LOW - Guessed |

## State Machine (Reconstructed)

**Confidence:** LOW - This is a reconstructed model, not extracted from source.

### States

| State | Description | Confidence |
|-------|-------------|------------|
| IDLE | Standing still | LOW - Assumed |
| PATROL | Following waypoints | LOW - Assumed |
| ALERT | Aware of threat | LOW - Assumed |
| ATTACKING | Engaging enemy | LOW - Assumed |
| FLEEING | Running away | LOW - Assumed |
| DEAD | Eliminated | LOW - Assumed |

### State Transitions (Guessed)

```
IDLE → PATROL (timer)
PATROL → ALERT (player spotted)
ALERT → ATTACKING (in range)
ATTACKING → PATROL (target lost)
ATTACKING → DEAD (health = 0)
ALERT → FLEEING (health < 20)
```

## Pathfinding (Guessed)

**Confidence:** LOW - Pathfinding algorithm is assumed from standard game patterns.

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Algorithm | A* (assumed) | LOW | Standard game convention |
| Grid size | 512x512 (assumed) | LOW | Standard game convention |
| Obstacle avoidance | Yes (assumed) | LOW | Standard game convention |

## Navigation Graph

### Format (Partially verified)

```
Header: 0xFFEEDDCC magic (verified via hex dump)
Grid: 5x5 sector system (from file analysis)
Nodes: ~100 nodes per level (estimated from file size)
Edges: uint16 pairs (target, cost) (partially verified)
```

### Node Format

| Offset | Size | Description | Confidence |
|--------|------|-------------|------------|
| 0x00 | 12 | Position (3x float32, -1.0 = unpopulated) | MEDIUM |
| 0x0C | var | Edge list (uint16 pairs: target_node, cost) | MEDIUM |

## Perception (Guessed)

**Warning:** These values are guesses. The actual perception system is unknown.

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Sight range | 50-100 meters | LOW | Standard FPS convention |
| Sight angle | 90 degrees | LOW | Standard FPS convention |
| Sound range | 20-50 meters | LOW | Standard FPS convention |
| Memory duration | 10 seconds | LOW | Standard FPS convention |

## Difficulty Modifiers (Guessed)

**Warning:** These percentages are guesses. The actual difficulty scaling is unknown.

| Difficulty | NPC Health | NPC Damage | Detection | Accuracy | Confidence |
|------------|------------|------------|-----------|----------|------------|
| Easy | 80% | 50% | 50% | 50% | LOW - Guessed |
| Normal | 100% | 100% | 100% | 75% | LOW - Guessed |
| Hard | 120% | 150% | 150% | 100% | LOW - Guessed |

## Performance (Estimated)

| Metric | Estimate | Confidence | Method |
|--------|----------|------------|--------|
| Event processing | ~1ms | LOW | Estimate |
| Behavior update | ~2ms | LOW | Estimate |
| Pathfinding | ~5ms | LOW | Estimate |
| Total AI cost | ~8ms | LOW | Estimate |
| NPCs per level | 20-50 | LOW | Estimate |
| Max NPCs | 100 | LOW | Estimate |

## Known Issues

1. **Architecture unknown** - Behavior trees assumed, but actual implementation unclear
2. **Pathfinding algorithm unverified** - A* assumed, not confirmed
3. **NPC statistics unverified** - Health, damage, perception are guesses
4. **State machine reconstructed** - Not extracted from source
5. **Performance metrics unmeasured** - Estimates only

## References

- AI scripts: PC/MISSIONS/*/AI/*.qvm
- Behavior data: Level editor (not available)
- Analysis tools: String extraction, file structure analysis
