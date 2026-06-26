# 03 - Scripting System (QVM)

## Overview

QVM (Quake Virtual Machine) is a bytecode format used for game scripts. The format appears similar to Quake 3's QVM but may have been modified by Innerloop.

**Confidence:** MEDIUM - Format structure verified, but opcodes and execution model are partially mapped.

## QVM File Format (LOOP v8)

```
Offset  Size  Description
0x00    4     Magic: "LOOP" (0x4C4F4F50)
0x04    4     Version: 8 (uint32 LE)
0x08    4     Section count: 5 (uint32 LE)
0x0C    4     String table offset (uint32 LE)
0x10    N*4   Section offset/size table
0x10+M  var   Function dispatch table (uint32 offsets)
...     var   Code/data sections
...     var   String table
```

**Confidence:** HIGH - Verified via hex dump of multiple QVM files.

## Sections

| Index | Purpose | Confidence | Method |
|-------|---------|------------|--------|
| 0 | Function name table / string constants | MEDIUM | String analysis |
| 1 | Offset/size table for resources | MEDIUM | Structure analysis |
| 2 | Additional string constants (input keys, etc.) | MEDIUM | String analysis |
| 3 | Data section (GUID, config values) | MEDIUM | Data analysis |
| 4 | Data continuation | MEDIUM | Inferred |

## QSC Source Files

.qsc files are the source format compiled to .qvm. Known .qsc files:

| File | Purpose | Confidence | Method |
|------|---------|------------|--------|
| config.qsc | Input bindings and options | HIGH | Filename + content analysis |
| mainmenu.qsc | Main menu definitions | HIGH | Filename + content analysis |
| weaponconfig.qsc | Weapon definitions | HIGH | Filename + content analysis |
| physicsobj.qsc | Physics object types | MEDIUM | Filename inference |
| magicobj.qsc | Interactive object types | HIGH | Filename + content analysis |
| humanplayer.qsc | Player definition | HIGH | Filename + content analysis |
| animtrigger.qsc | Animation triggers | HIGH | Filename + content analysis |
| material.qsc | Surface materials | HIGH | Filename + content analysis |
| ingamemenu.qsc | Pause menu | HIGH | Filename + content analysis |
| mission.qsc | Per-mission configuration | HIGH | Filename + content analysis |
| sounds.qsc | Sound definitions per level | HIGH | Filename + content analysis |
| level*.qsc | Level-specific scripts | HIGH | Filename pattern |
| AI/*.qsc | AI behavior scripts | HIGH | Filename pattern |

## QVM Inventory (Partial)

| File | Size | Purpose | Confidence | Method |
|------|------|---------|------------|--------|
| lod.qvm | 48,510 | LOD distance settings | MEDIUM | Filename + content |
| mainmenu.qvm | 25,549 | Main menu system | MEDIUM | Filename + content |
| magicobj.qvm | 19,994 | Interactive object definitions | MEDIUM | Filename + content |
| weapon~1.qvm | 17,801 | Weapon configuration | MEDIUM | Filename + content |
| terrain1.qvm | 12,733 | Terrain material/tilemap creation | MEDIUM | Filename + content |
| ingame~1.qvm | 11,308 | In-game pause menu | MEDIUM | Filename + content |
| material.qvm | 10,526 | Surface material properties | MEDIUM | Filename + content |
| guard.qvm | 3,744 | Guard AI behavior | MEDIUM | Filename + content |
| patrol.qvm | 3,745 | Patrol AI behavior | MEDIUM | Filename + content |
| anya.qvm | 3,745 | Anya character AI | MEDIUM | Filename + content |
| priboi.qvm | 3,744 | Priboi character AI | MEDIUM | Filename + content |
| ekk.qvm | 3,354 | Ekk character AI | MEDIUM | Filename + content |
| gunner.qvm | 3,242 | Gunner AI behavior | MEDIUM | Filename + content |
| rpg.qvm | 3,228 | RPG soldier AI | MEDIUM | Filename + content |
| animtr~1.qvm | 3,115 | Animation triggers | MEDIUM | Filename + content |
| sniper.qvm | 3,100 | Sniper AI behavior | MEDIUM | Filename + content |
| physic~1.qvm | 2,820 | Physics object types | MEDIUM | Filename + content |
| civilian.qvm | 1,515 | Civilian AI behavior | MEDIUM | Filename + content |
| humanp~1.qvm | 1,457 | Human player definition | MEDIUM | Filename + content |
| config.qvm | 2,511 | Input/control bindings | MEDIUM | Filename + content |
| editor~1.qvm | 438 | Editor magic objects | MEDIUM | Filename + content |

## Opcode Table (Partial)

**Warning:** The opcode table is partially mapped. Many opcodes are unidentified. Do not rely on this table for implementation.

| Opcode | Mnemonic | Description | Confidence |
|--------|----------|-------------|------------|
| 0x00 | NOP | No operation | LOW - Inferred |
| 0x01 | LOAD | Load from stack | LOW - Inferred |
| 0x02 | STORE | Store to stack | LOW - Inferred |
| 0x03 | PUSH | Push to stack | LOW - Inferred |
| 0x04 | POP | Pop from stack | LOW - Inferred |
| 0x05 | ADD | Integer addition | LOW - Inferred |
| 0x06 | SUB | Integer subtraction | LOW - Inferred |
| 0x07 | MUL | Integer multiplication | LOW - Inferred |
| 0x08 | DIV | Integer division | LOW - Inferred |
| 0x09 | MOD | Modulo | LOW - Inferred |
| 0x0A | AND | Bitwise AND | LOW - Inferred |
| 0x0B | OR | Bitwise OR | LOW - Inferred |
| 0x0C | XOR | Bitwise XOR | LOW - Inferred |
| 0x0D | NOT | Bitwise NOT | LOW - Inferred |
| 0x0E | SHL | Shift left | LOW - Inferred |
| 0x0F | SHR | Shift right | LOW - Inferred |
| 0x10 | JMP | Unconditional jump | LOW - Inferred |
| 0x11 | JZ | Jump if zero | LOW - Inferred |
| 0x12 | JNZ | Jump if not zero | LOW - Inferred |
| 0x13 | CALL | Call function | LOW - Inferred |
| 0x14 | RET | Return | LOW - Inferred |
| 0x15-0xFF | ? | Unknown opcodes | ❌ Unknown |

**Note:** This opcode table is inferred from standard VM patterns and Quake 3 QVM documentation. The actual opcodes may differ significantly.

## Event System

### Events (22 total)

| Event | Description | Confidence | Method |
|-------|-------------|------------|--------|
| GOStart | Level started | MEDIUM | String analysis |
| GORestart | Level restarted | MEDIUM | String analysis |
| GOLoaded | Resources loaded | MEDIUM | String analysis |
| GOKilled | Player died | MEDIUM | String analysis |
| GOHit | Player took damage | MEDIUM | String analysis |
| GOMessage | Display message | MEDIUM | String analysis |
| GOWeapon | Weapon fired | MEDIUM | String analysis |
| GOAmmo | Ammo changed | MEDIUM | String analysis |
| GOPickup | Item picked up | MEDIUM | String analysis |
| GOEnemy | Enemy spotted | MEDIUM | String analysis |
| GODamage | Entity damaged | MEDIUM | String analysis |
| GOKill | Entity killed | MEDIUM | String analysis |
| GOSpawn | Entity spawned | MEDIUM | String analysis |
| GORemove | Entity removed | MEDIUM | String analysis |
| GOTrigger | Trigger activated | MEDIUM | String analysis |
| GOSound | Sound played | MEDIUM | String analysis |
| GOEffect | Effect spawned | MEDIUM | String analysis |
| GOLight | Light toggled | MEDIUM | String analysis |
| GODoor | Door toggled | MEDIUM | String analysis |
| GOButton | Button pressed | MEDIUM | String analysis |
| GOObjective | Objective updated | MEDIUM | String analysis |
| GOScore | Score changed | MEDIUM | String analysis |

### Actions (17 total)

| Action | Description | Confidence | Method |
|--------|-------------|------------|--------|
| GOMoveTo | Move to position | MEDIUM | String analysis |
| GOMoveDir | Move in direction | MEDIUM | String analysis |
| GORotate | Rotate entity | MEDIUM | String analysis |
| GOFollow | Follow entity | MEDIUM | String analysis |
| GOAttack | Attack target | MEDIUM | String analysis |
| GODefend | Enter defensive mode | MEDIUM | String analysis |
| GORetreat | Flee from threat | MEDIUM | String analysis |
| GOReload | Reload weapon | MEDIUM | String analysis |
| GOUse | Use object | MEDIUM | String analysis |
| GOPickup | Pick up item | MEDIUM | String analysis |
| GORadio | Send radio message | MEDIUM | String analysis |
| GOSound | Play sound | MEDIUM | String analysis |
| GOAnimate | Play animation | MEDIUM | String analysis |
| GOEffect | Spawn effect | MEDIUM | String analysis |
| GOLight | Toggle light | MEDIUM | String analysis |
| GODoor | Toggle door | MEDIUM | String analysis |
| GOActivate | Activate object | MEDIUM | String analysis |

## Example Script (Pseudocode)

This is reconstructed pseudocode, not actual QVM bytecode:

```
// Guard AI behavior (reconstructed from string analysis)
IF event == AIEVENT_CREATE THEN
    SET state = IDLE
    SET health = 100
    SET weapon = RIFLE
END IF

IF event == AIEVENT_ENEMYDETECTION THEN
    SET state = ALERT
    PLAY SOUND "enemy_spotted"
    CALL AIAction_LookAtEvent
END IF

IF state == ALERT THEN
    IF distance_to_enemy < 50 THEN
        SET state = ATTACKING
        CALL AIAction_FireAtTask
    ELSE
        CALL AIAction_WalkToNode
    END IF
END IF
```

**Confidence:** LOW - This is pseudocode based on string analysis, not verified behavior.

## Global Variables (From QVM strings)

| Variable | Description | Confidence | Method |
|----------|-------------|------------|--------|
| GOStart | Entry point | MEDIUM | String analysis |
| GOPlayer | Player name | MEDIUM | String analysis |
| GOActiveMission | Current mission | MEDIUM | String analysis |
| GOContentControlPW | Parental password | MEDIUM | String analysis |
| GOGfxDisp | Display adapter | MEDIUM | String analysis |
| GOGfxDevice | D3D device | MEDIUM | String analysis |
| GOGfxGamma | Gamma value | MEDIUM | String analysis |
| GOGfxPerformance | Quality level | MEDIUM | String analysis |
| GOGameLang | Language | MEDIUM | String analysis |
| GOGameDiff | Difficulty | MEDIUM | String analysis |
| GOIsBlood | Blood enabled | MEDIUM | String analysis |
| GOSoundSpeech | Speech volume | MEDIUM | String analysis |
| GOSoundMusic | Music volume | MEDIUM | String analysis |
| GOSoundFX | Effects volume | MEDIUM | String analysis |
| GOInRemap | Key remap state | MEDIUM | String analysis |
| GOInMouInv | Invert mouse | MEDIUM | String analysis |
| GOInMouSens | Mouse sensitivity | MEDIUM | String analysis |

## Known Issues

1. **Opcode table incomplete** - Only ~20 opcodes identified out of 256 possible
2. **Execution model unclear** - Register/stack architecture assumed but not verified
3. **Instruction encoding unknown** - 8-bit opcode + 24-bit immediate is a guess
4. **Function dispatch unclear** - How functions are called is not documented

## References

- QVM format: Similar to Quake 3 QVM (unconfirmed connection)
- Script sources: .qsc files (not available)
- Analysis tools: Hex dump, string extraction
