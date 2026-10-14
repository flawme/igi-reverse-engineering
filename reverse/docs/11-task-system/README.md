# 11 - Task System

## Overview

Everything in the engine is a "Task". Tasks have types, events, and parameters. The task system appears to be the core entity component system.

**Confidence:** MEDIUM - Task type names extracted from string analysis, but descriptions and behavior are inferred.

## Task Types (64 total)

**Confidence:** HIGH for the names and the count - extracted verbatim from `IGI.exe`
(`strings -n 6 IGI.exe | grep '^TASKTYPE_'` returns 64 real names plus one regex
pattern). The descriptions below are descriptive, not from the data.

The complete list, in the order the strings appear:

```
AFTERBURNER            AISTATIONARYGUN        ALARMLIGHT
ALARMLIGHTREFLECTOR    ANIMSOUND              BINOCULAR
BONEMAGICOBJ           BUILDING               CABARREL
CACLIP                 CAR                    CARDOOR
COCKPITSHIELD          CUTSCENE               DEATHZONE
DRAWER                 EDITCAMERA             EDITORMAGICOBJ
EDITRIGIDOBJ           EXPLODEMAGICOBJ        FENCE
GEAR                   GENERICPHYSICSMAGICOBJ GENERICPHYSICSOBJ
GLASS                  GRENADE                GUN
GUNCLIP                GUNDRAGUNOV            GUNFLAME
GUNM16A2               GUNMOVINGPART          GUNMP5SD
GUNSHOT                GUNSHOTEFFECT          GUNSPAS12
GUNX2                  HATCH                  HELI
HELIDOOR               HELIWHEEL              HITZONE
KNIFESTAB              LADDER                 LEVELFLOW
LEVELTIMER             M203                   MAGICOBJ
MEDIPACK               MINE                   MISSILE
MOVERIGIDOBJ           NOISEQTASK             PHYSICSMAGICOBJ
PLANE                  PROXIMITYMINE          RADARDISH
ROCKETPOD              ROTOR                  RUDDER
SCAMERALENSVIEWCONE    SMOKE                  SMOOTHQTASK
WHEEL
```

Earlier revisions of this document split these into guessed "Vehicle / Weapon /
Interactive / System" groups of 15/15/13/15 - that split was invented and only covered
58 of the 64. The names above are the verified complete set.

### Notable groups (descriptive, not from the data)

| Group | Names |
|-------|-------|
| Vehicles | `CAR`, `CARDOOR`, `WHEEL`, `HELI`, `HELIDOOR`, `HELIWHEEL`, `ROTOR`, `PLANE`, `GEAR`, `RUDDER`, `AFTERBURNER`, `HATCH`, `COCKPITSHIELD`, `ROCKETPOD`, `MISSILE` |
| Weapons and effects | `GUN`, `GUNCLIP`, `GUNDRAGUNOV`, `GUNFLAME`, `GUNM16A2`, `GUNMOVINGPART`, `GUNMP5SD`, `GUNSHOT`, `GUNSHOTEFFECT`, `GUNSPAS12`, `GUNX2`, `GRENADE`, `MINE`, `PROXIMITYMINE`, `M203`, `KNIFESTAB`, `AISTATIONARYGUN`, `SMOKE` |
| Interactive props | `FENCE`, `LADDER`, `DRAWER`, `GLASS`, `CABARREL`, `CACLIP`, `MEDIPACK`, `BINOCULAR`, `ALARMLIGHT`, `ALARMLIGHTREFLECTOR`, `SCAMERALENSVIEWCONE`, `RADARDISH`, `BUILDING`, `DEATHZONE`, `HITZONE` |
| System / editor | `LEVELFLOW`, `LEVELTIMER`, `CUTSCENE`, `MAGICOBJ`, `BONEMAGICOBJ`, `EXPLODEMAGICOBJ`, `PHYSICSMAGICOBJ`, `GENERICPHYSICSOBJ`, `GENERICPHYSICSMAGICOBJ`, `MOVERIGIDOBJ`, `EDITRIGIDOBJ`, `EDITCAMERA`, `EDITORMAGICOBJ`, `ANIMSOUND`, `NOISEQTASK`, `SMOOTHQTASK` |

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

## Hit Detection ✅ VERIFIED

The hitzone tables live in `IGI.exe`: 17 x 16-byte entries, first dword = damage
multiplier. Multipliers are `0.5/0.75/1.0` triples, then `1.0` x3, then `100.0` at
indices 15/16 (head). AI table `0x53f9d0`, player table `0x538a00`. The damage formula
is `hitzone_multiplier[hitzone] * DamageFactor` (see
[06-weapons](../06-weapons/README.md)).

## Known Issues

1. **Task descriptions inferred** - Based on type names, not verified behavior
2. **Task architecture reconstructed** - Not extracted from source
3. **Vehicle hierarchy assumed** - From type names, not confirmed
4. **Task count unverified** - 64 is from string analysis, may be incomplete

## References

- Task scripts: PC/HUMANP~1/
- Vehicle physics: PC/PHYSIC~1/
- Magic objects: magicobj.qvm
- Physics objects: physic~1.qvm
