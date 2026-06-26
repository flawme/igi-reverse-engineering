# 11 - Task System

## Overview

Everything in the engine is a "Task". Tasks have types, events, and parameters. The task system appears to be the core entity component system.

**Confidence:** MEDIUM - Task type names extracted from string analysis, but descriptions and behavior are inferred.

## Task Types (64 total)

**Confidence:** MEDIUM - Type names extracted from string analysis. Descriptions are guesses based on names.

### Vehicle Tasks (15)

| Task Type | Description | Confidence | Method |
|-----------|-------------|------------|--------|
| TASKTYPE_CAR | Car vehicle | MEDIUM | String analysis |
| TASKTYPE_WHEEL | Vehicle wheel | MEDIUM | String analysis |
| TASKTYPE_HELI | Helicopter | MEDIUM | String analysis |
| TASKTYPE_PLANE | Aircraft | MEDIUM | String analysis |
| TASKTYPE_GEAR | Landing gear | MEDIUM | String analysis |
| TASKTYPE_HATCH | Vehicle hatch | MEDIUM | String analysis |
| TASKTYPE_RUDDER | Flight control | MEDIUM | String analysis |
| TASKTYPE_AFTERBURNER | Jet engine | MEDIUM | String analysis |
| TASKTYPE_ROTOR | Helicopter rotor | MEDIUM | String analysis |
| TASKTYPE_COCKPITSHIELD | Cockpit glass | MEDIUM | String analysis |
| TASKTYPE_CARDOOR | Car door | MEDIUM | String analysis |
| TASKTYPE_HELIWHEEL | Helicopter wheel | MEDIUM | String analysis |
| TASKTYPE_HELIDOOR | Helicopter door | MEDIUM | String analysis |
| TASKTYPE_ROCKETPOD | Rocket launcher | MEDIUM | String analysis |
| TASKTYPE_RADARDISH | Radar dish | MEDIUM | String analysis |

### Weapon/Effect Tasks (15)

| Task Type | Description | Confidence | Method |
|-----------|-------------|------------|--------|
| TASKTYPE_GUN | Weapon system | MEDIUM | String analysis |
| TASKTYPE_GUNSHOT | Bullet projectile | MEDIUM | String analysis |
| TASKTYPE_GUNFLAME | Muzzle flash | MEDIUM | String analysis |
| TASKTYPE_GUNMOVINGPART | Animated weapon parts | MEDIUM | String analysis |
| TASKTYPE_GUNCLIP | Magazine/clip | MEDIUM | String analysis |
| TASKTYPE_GUNX2 | Dual weapons | MEDIUM | String analysis |
| TASKTYPE_GRENADE | Grenade projectile | MEDIUM | String analysis |
| TASKTYPE_MINE | Mine device | MEDIUM | String analysis |
| TASKTYPE_PROXIMITYMINE | Proximity-triggered mine | MEDIUM | String analysis |
| TASKTYPE_MISSILE | Guided missile | MEDIUM | String analysis |
| TASKTYPE_M203 | Grenade launcher | MEDIUM | String analysis |
| TASKTYPE_SMOKE | Smoke effect | MEDIUM | String analysis |
| TASKTYPE_GUNSHOTEFFECT | Shot visual effect | MEDIUM | String analysis |
| TASKTYPE_KNIFESTAB | Knife attack | MEDIUM | String analysis |
| TASKTYPE_AISTATIONARYGUN | AI-controlled turret | MEDIUM | String analysis |

### Interactive Tasks (13)

| Task Type | Description | Confidence | Method |
|-----------|-------------|------------|--------|
| TASKTYPE_FENCE | Fence object | MEDIUM | String analysis |
| TASKTYPE_LADDER | Climbable ladder | MEDIUM | String analysis |
| TASKTYPE_DRAWER | Openable drawer | MEDIUM | String analysis |
| TASKTYPE_BUILDING | Building structure | MEDIUM | String analysis |
| TASKTYPE_GLASS | Breakable glass | MEDIUM | String analysis |
| TASKTYPE_DEATHZONE | Kill trigger | MEDIUM | String analysis |
| TASKTYPE_MEDIPACK | Health pickup | MEDIUM | String analysis |
| TASKTYPE_BINOCULAR | Binoculars item | MEDIUM | String analysis |
| TASKTYPE_CABARREL | Explosive barrel | MEDIUM | String analysis |
| TASKTYPE_CACLIP | Ammo clip pickup | MEDIUM | String analysis |
| TASKTYPE_ALARMLIGHT | Alarm light | MEDIUM | String analysis |
| TASKTYPE_ALARMLIGHTREFLECTOR | Alarm light reflector | MEDIUM | String analysis |
| TASKTYPE_SCAMERALENSVIEWCONE | Security camera | MEDIUM | String analysis |

### System Tasks (15)

| Task Type | Description | Confidence | Method |
|-----------|-------------|------------|--------|
| TASKTYPE_LEVELFLOW | Level flow control | MEDIUM | String analysis |
| TASKTYPE_LEVELTIMER | Level timer | MEDIUM | String analysis |
| TASKTYPE_CUTSCENE | Cutscene playback | MEDIUM | String analysis |
| TASKTYPE_MAGICOBJ | Magic/interactive object | MEDIUM | String analysis |
| TASKTYPE_GENERICPHYSICSOBJ | Generic physics object | MEDIUM | String analysis |
| TASKTYPE_GENERICPHYSICSMAGICOBJ | Physics magic object | MEDIUM | String analysis |
| TASKTYPE_EDITRIGIDOBJ | Editor rigid object | MEDIUM | String analysis |
| TASKTYPE_EDITCAMERA | Editor camera | MEDIUM | String analysis |
| TASKTYPE_EDITORMAGICOBJ | Editor magic object | MEDIUM | String analysis |
| TASKTYPE_MOVERIGIDOBJ | Move rigid object | MEDIUM | String analysis |
| TASKTYPE_ANIMSOUND | Animation sound | MEDIUM | String analysis |
| TASKTYPE_BONEMAGICOBJ | Bone magic object | MEDIUM | String analysis |
| TASKTYPE_NOISEQTASK | Noise qtask | MEDIUM | String analysis |
| TASKTYPE_SMOOTHQTASK | Smooth qtask | MEDIUM | String analysis |
| TASKTYPE_HITZONE | Hit detection zone | MEDIUM | String analysis |

## Task Architecture (Reconstructed)

**Confidence:** LOW - This is a reconstructed model, not extracted from source.

```
Task
├── Type (TASKTYPE_*)
├── Event Handler
├── Parameters
├── State
└── Child Tasks
```

## Task Creation (From error strings)

```
HumanAIConfigItem
HumanAIConfig
Unable to create HumanAIConfig task
```

**Confidence:** MEDIUM - Extracted from error messages in binary.

## Task Lifecycle (Reconstructed)

**Confidence:** LOW - This is a reconstructed model, not extracted from source.

1. Task creation (from QVM)
2. Initialization (AIEVENT_CREATE)
3. Update loop (per-frame)
4. Event handling (AIEVENT_*)
5. Destruction (AIEVENT_DELETE)

## Vehicle System (Inferred)

**Confidence:** LOW - Vehicle component hierarchy is assumed from task type names.

Vehicle components are hierarchical tasks:
```
TASKTYPE_CAR
├── TASKTYPE_WHEEL (x4)
├── TASKTYPE_CARDOOR (x2)
├── TASKTYPE_GUN (turret)
├── TASKTYPE_HELIWHEEL (if heli)
└── TASKTYPE_HELIDOOR (if heli)
```

### Vehicle Physics Objects (Observed)

Located in PC/PHYSIC~1/:
```
CARS/       - Car physics
HELIS/      - Helicopter physics
MISSILES/   - Missile physics
PLANES/     - Plane physics
TRAINS/     - Train physics
WEAPONS/    - Weapon physics
```

**Confidence:** HIGH - From filesystem listing.

## Magic Objects (From QVM scripts)

Interactive objects defined in magicobj.qvm:
- Doors, drawers, ladders
- Buttons, switches
- Exploding barrels
- Ammo clips, medipacks

**Confidence:** MEDIUM - From QVM script analysis.

## Hit Detection (Guessed)

**Warning:** These damage multipliers are standard FPS conventions, not verified from the game.

| Zone | Multiplier | Confidence | Method |
|------|------------|------------|--------|
| Head | 2x | LOW | Standard FPS convention |
| Body | 1x | LOW | Standard FPS convention |
| Limb | 0.5x | LOW | Standard FPS convention |

## Known Issues

1. **Task descriptions inferred** - Based on type names, not verified behavior
2. **Task architecture reconstructed** - Not extracted from source
3. **Vehicle hierarchy assumed** - From type names, not confirmed
4. **Hit detection unverified** - Multipliers are guesses
5. **Task count unverified** - 64 is from string analysis, may be incomplete

## References

- Task scripts: PC/HUMANP~1/
- Vehicle physics: PC/PHYSIC~1/
- Magic objects: magicobj.qvm
- Physics objects: physic~1.qvm
