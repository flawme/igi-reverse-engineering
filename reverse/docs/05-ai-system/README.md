# 05 - AI System

## Architecture (Inferred)

**Confidence:** LOW - The AI system architecture is inferred from string analysis and standard game patterns. The actual implementation may differ significantly.

The game appears to use an event-driven AI system. The term "behavior trees" is used in previous documentation, but this is an assumption based on common game AI patterns. The actual implementation could be state machines, rule-based systems, or other patterns.

## Events (24 total)

**Confidence:** HIGH for the names and the count - extracted verbatim from `IGI.exe`
(`strings -n 6 IGI.exe | grep '^AIEVENT_'` returns 24). Earlier revisions claimed 22;
the two missing ones were `AIEVENT_ALERT_RESPONSE` and `AIEVENT_ANIMATION`... in fact
the earlier list had 24 rows but claimed 22 in the heading. The verified set:

```
AIEVENT_ALARMOFF          AIEVENT_ALARMON           AIEVENT_ALERT
AIEVENT_ALERT_RESPONSE    AIEVENT_ANIMATION         AIEVENT_COMBAT
AIEVENT_CREATE            AIEVENT_DEAD              AIEVENT_DELETE
AIEVENT_DOOR              AIEVENT_ENEMYDETECTION    AIEVENT_EXPLOSION
AIEVENT_FENCE             AIEVENT_FLASHBANG         AIEVENT_FRIENDLYDETECTION
AIEVENT_GRENADELAND       AIEVENT_GRENADETHROWN     AIEVENT_GROUNDIMPACT
AIEVENT_GUNSHOT           AIEVENT_GUNSHOTMISS       AIEVENT_IDLE
AIEVENT_LADDER            AIEVENT_TAKINGDAMAGE      AIEVENT_WALK
```

The AI scripts dispatch on these with `GetCurrentEventType()`, e.g.
`level1/ai/1205.qvm` decodes to
`if (GetCurrentEventType() == AIEVENT_CREATE) { DefaultHandler(); }`.

## Actions and functions

**Confidence:** HIGH for the names - extracted verbatim from `IGI.exe`. The earlier
"17 actions" claim was wrong.

| Prefix | Count in `IGI.exe` | Count used by the retail QVM scripts |
|--------|--------------------|--------------------------------------|
| `AIEVENT_` | 24 | 24 |
| `AIAction_` | 18 | 12 |
| `AIFunction_` | 37 | 30 |

`AIAction_*`: `Activate`, `Combat`, `Dead`, `FallFlat`, `FireAtNode`, `FireAtTask`,
`Idle`, `KickGrenade`, `LookAtEvent`, `MoveToEvent`, `Patrol`, `PlayAnimation`,
`PlaySound`, `RunPanicking`, `RunToNode`, `SetCombat`, `Stunned`, `WalkToNode`.

`AIFunction_*` (37): the `Get*`/`Set*` accessors the scripts call, including
`DefaultHandler`, `GetCurrentEventType`, `GetEventDistance`, `IsEventBehind`,
`SetEventPriority`, `SetDeathAnimation`, `SetInvulnerability`, `SetInstantDeath`,
`SendResponse`, and the alarm/view accessors (`GetAlarmControlID`,
`SetAlarmTriggerDistance`, `SetViewLength`, `SetSecondaryViewGamma`, ...).

## Architecture

**Confidence:** MEDIUM - the event/action/function vocabulary is now verified, but the
dispatch mechanism is still inferred. The scripts are QVM bytecode that reads the
current event type and calls named functions; whether the engine drives them through a
state machine, a rule list or a behaviour tree is not established by the data.

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

## Pathfinding

**Confidence:** HIGH for the routing mechanism - the nav `.dat` grid is a precomputed
routing table (see below). The steering layer that consumes it is inferred.

| Property | Value | Confidence | Method |
|----------|-------|------------|--------|
| Algorithm | precomputed next-hop routing table, not A* | ✅ | loader `fcn.004f9d30`, accessor `fcn.00509740`, consumer `0x425dec` |
| Grid | `dim x dim` nodes (100 in most files, 300 in `graph4019.dat`) | ✅ | header `+0x0C` |
| Cell | `{uint32 next_hop, float path_distance}`; `0xFFFFFFFF` = no route | ✅ | 66,408 column-adjacent cells, 0 row-adjacent |

## Navigation Graph ✅ VERIFIED

The `.dat` file is a **routing table**, not an edge list:

```
Header (30 bytes): magic 0xFFEEDDCC, dim at +0x0C, grid byte size at +0x1A
Grid at +0x1E: dim*dim cells, 8 bytes each {uint32 next_hop, float path_distance}
Tail: name-hashed records (nNodeID, tNodePosition, vNodeRadius, nLinkID1/2, eLinkType, ...)
```

The cell's `uint32` is the next hop from the column node toward the row node
(`[destination][source]`); `0xFFFFFFFF` means no route. The record stream after the
grid uses name-hashed keys (`hash("nMaxNodes") = 0x000D3AE6`). See
[16-verified-formats](../16-verified-formats/README.md) for the byte-level proof.

The 7 `level8/graphs/*.dat` files use a second, tag-only layout with no magic.

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
2. **Steering layer** - the routing table is verified; how the AI steers along the next-hop chain is inferred
3. **NPC statistics unverified** - Health, damage, perception are guesses
4. **State machine reconstructed** - Not extracted from source
5. **Performance metrics unmeasured** - Estimates only

## References

- AI scripts: PC/MISSIONS/*/AI/*.qvm
- Behavior data: Level editor (not available)
- Analysis tools: String extraction, file structure analysis
