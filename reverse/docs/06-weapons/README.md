# 06 - Weapons System

## Weapon List

**Confidence:** HIGH for the list itself - it is the actual directory listing of
`pc/weapons/`, one directory per weapon, each holding a `weapon.qvm` parameter script.
Earlier revisions of this document listed 21 guessed weapons (Beretta, P90, G36, FAMAS,
M1014, PSG-1, Barrett, M249, M60, RPG-7, M67...) - **none of those exist in the game**.
The real set is 24 entries:

| Directory | Notes |
|-----------|-------|
| `AK47` | assault rifle |
| `APC` | vehicle-mounted weapon |
| `BINOCULARS` | equipment |
| `COLTANACONDA` | revolver |
| `DESERTEAGLE` | pistol |
| `DRAGUNOV` | sniper rifle |
| `FLASHBANG` | thrown |
| `GLOCK` | pistol |
| `GRENADE` | thrown |
| `JACKHAMMER` | shotgun |
| `KNIFE` | melee |
| `M16A2` | assault rifle |
| `M2HB` | heavy machine gun |
| `MEDIPACK` | equipment |
| `MIL` | (see `weapon.qvm`) |
| `MINIMI` | light machine gun |
| `MP5SD` | suppressed SMG |
| `PROXIMITYMINE` | placed |
| `RPG18` | rocket launcher |
| `SENTRYGUN` | emplacement |
| `SPAS12` | shotgun |
| `UZI` | SMG |
| `UZIX2` | dual SMGs |
| `t80` | tank main gun |

Plus `pc/weapons/weaponconfig.qvm`, the global weapon table.

The weapon display names come from the game's string table
(`language/english/messages.res`, keys under `weapons/strings/`), not from the
directory names.

## Ammo Types

**Confidence:** HIGH for the list - it is the directory listing of `pc/ammo/`. The
earlier "5 ammo types" claim was wrong; there are 14:

| Directory | Calibre |
|-----------|---------|
| `44` | .44 Magnum |
| `357` | .357 Magnum |
| `12` | 12-gauge shell |
| `556` | 5.56 mm |
| `762` | 7.62 mm |
| `919` | 9x19 mm |
| `127` | .127 (12.7 mm) |
| `1000` | 1000-round (see `ammo.qvm`) |
| `DRAGUNOV` | Dragunov rounds |
| `M203` | 40 mm grenade |
| `GRENADE` | hand grenade |
| `FLASHBANG` | flashbang |
| `PROXIMITYMINE` | proximity mine |
| `MEDIPACK` | medical supplies |

Each directory holds an `ammo.qvm` parameter script. The disassembler reads them, e.g.
`ammo/1000/ammo.qvm` decodes to
`DefineAmmoType(13, "AMMO_ID_1000", "<1000>", "<1000DESC>", 1000, 3.5, 250, 200, 0, 255, 255, 0, 0, "115_01_1", "Sound0")`.

## Weapon Parameters ✅ VERIFIED

`weaponconfig.qvm` declares the parameter list by name - these are the game's own
field names, not a reconstruction. Each `weapons/<NAME>/weapon.qvm` is a single
`DefineWeaponType(...)` call carrying the same 50 values in the same order.

The full declaration is at `reverse/data/weapon_parameters.tsv`; the extracted values
for all 24 weapons are at `reverse/data/weapon_table.tsv`.

| # | Parameter | Type |
|---|-----------|------|
| 0 | Weapon ID | Int32 |
| 1 | Script ID | String256 |
| 2 | Name | String256 |
| 3 | Manufacturer | String256 |
| 4 | Description | String256 |
| 5 | Weapon Type | EnumInt32 |
| 6 | Sight Display Type | EnumInt32 |
| 7 | Ammo Display Type | EnumInt32 |
| 8 | Mass of Weapon (grams) | Int32 |
| 9 | Calibre ID | Int32 |
| 10 | Damage Factor | Real32 |
| 11 | Penetration Power | Real32 |
| 12 | Reload Time | Real32 |
| 13 | Muzzle Velocity | Real32 |
| 14 | Bullets/Round | Int32 |
| 15 | Rounds/Minute | Int32 |
| 16 | Rounds/Clip | Int32 |
| 17 | Maximum Rounds/Burst | Int32 |
| 18 | Minimum random spread | Real32 |
| 19 | Maximum random spread | Real32 |
| 20-23 | Fixed/Random view change around X and Z (degrees) | Real32 |
| 24 | Type of weapon | String256 |
| 25 | Effective Range of Weapon | Real32 |
| 26 | Weapon Users | String256 |
| 27 | Weapon Length | Int32 |
| 28 | Barrel Length | Int32 |
| 29 | Gun Model | String16 |
| 30 | Casing Model | String16 |
| 31-43 | Animation indices (stand, move, fire x3, reload, upper-body set) | Int32 |
| 44 | Fire Sound Loop/Single Sample | String16 |
| 45 | Fire Sound Loop End Sample | String16 |
| 46 | AI Detection Event Range | EnumReal32 |
| 47 | Projectile Task Type | EnumInt32 |
| 48 | Weapon Task Type | EnumInt32 |
| 49 | Is weapon selectable when empty | bool8 |

### Example: AK47

| Parameter | Value |
|-----------|-------|
| Weapon ID | 5 |
| Script ID | `WEAPON_ID_AK47` |
| Name | AK47 |
| Manufacturer | `<KALASHNIKOV>` |
| Weapon Type | `WEAPONTYPE_GUN` |
| Mass (grams) | 4300 |
| Calibre ID | 762 |
| **Damage Factor** | **0.3** |
| **Penetration Power** | **2** |
| **Reload Time** | **2.0** |
| **Muzzle Velocity** | **710** |
| Bullets/Round | 1 |
| **Rounds/Minute** | **650** |
| **Rounds/Clip** | **30** |
| Maximum Rounds/Burst | 30 |
| Random spread | -3.5 to 3.5 |
| Effective Range | 2000 |
| Weapon Length | 869 |
| Barrel Length | 414 |
| Gun Model | `100_01_1` |
| Casing Model | `113_01_1` |
| Fire Sound | `ak47_loop` / `ak47_loop_e` |
| Projectile Task Type | `TASKTYPE_GUNSHOT` |
| Weapon Task Type | `TASKTYPE_GUN` |

The earlier "struct Weapon { int damage; float fire_rate; ... }" reconstruction was
wrong in its field set and had no values. The real schema has 50 fields, and the
damage field is a **factor** (0.3 for the AK47), not an absolute number.

## Damage formula and parameter binding (IGI.exe)

**Confidence:** ✅ VERIFIED - recovered by static disassembly of `IGI.exe`
(PE32, imagebase `0x400000`). Every claim below cites the VA of the instruction
that proves it. This section supersedes the earlier "Damage Calculation" guess.

### Binding is positional, not by name ✅ VERIFIED

The parameter names used in `weaponconfig.qvm` (`Damage Factor`,
`Penetration Power`, `Rounds/Minute`, `Mass`, `Calibre`, `Spread`) do **not**
exist anywhere in `IGI.exe` - the engine binds the 50 `DefineWeaponType(...)`
values by **argument position**. `DefineWeaponType` is registered as a native
at `0x413ed8`:

```
0x413ed8  push str.DefineWeaponType   ; 0x5393c4
0x413ee2  call 0x4b8740               ; RegisterNative(name, handler, 0, -1)
```

with handler `fcn.00414020` (`0x414020`). The handler reads the 50 arguments positionally
through `0x4b88d0` (int) / `0x4b8900` (float) / `0x4b8930` (string), storing each
at a fixed displacement in a 1768-byte (`0x6e8`) record (argument 49 is never
read - see the structural notes below). The record index is the running weapon
count at `0x57b8dc`:

```
0x414038  mov ecx, dword [0x57b8dc]             ; weapon count
0x414041  lea edx, [ecx + ecx*4]                ; edx = 5*count
0x414044  lea edx, [ecx + edx*2]                ; edx = 11*count
0x414047  lea edx, [edx + edx*4]                ; edx = 55*count
0x41404a  lea edx, [ecx + edx*4]                ; edx = 221*count
0x41404d  mov dword [edx*8 + 0x56e9a8], eax     ; record[count].WeaponID (221*8 = 1768)
```

So: **array base `0x56e9a8`, stride `0x6e8` (1768 bytes), count at `0x57b8dc`.**
The accessor `GetWeaponRecord(index)` at `0x413c00` computes the same address
(`lea eax, [eax*8 + 0x56e9a8]` at `0x413c13`), and `GetWeaponCount()` at
`0x413c20` returns `[0x57b8dc]`.

### Argument to field map (record-relative) ✅ VERIFIED

Every argument is read by `push <index>; push ebp; call 0x4b88d0|0x4b8900|0x4b8930`
and stored at a fixed displacement. Offsets are relative to the record base
`0x56e9a8`.

| Arg | Field | Offset | Type | Store VA |
|-----|-------|--------|------|----------|
| 0 | WeaponID | `+0x000` | int32 | `0x41404d` |
| 8 | Mass | `+0x004` | int32 | `0x4141ec` |
| 27 | WeaponLength | `+0x008` | int32 | `0x414442` |
| 28 | BarrelLength | `+0x00c` | int32 | `0x41445d` |
| 1 | ScriptID | `+0x010` | char[256] | `0x4140dd` |
| 2 | Name | `+0x110` | char[256] | `0x4140f5` |
| 4 | Description | `+0x210` | char[256] | `0x414140` |
| 3 | Manufacturer | `+0x310` | char[256] | `0x41411a` |
| 24 | TypeOfWeapon | `+0x410` | char[256] | `0x4143d8` |
| 26 | WeaponUsers | `+0x510` | char[256] | `0x41440e` |
| 5 | WeaponType | `+0x610` | int32 | `0x414189` |
| 6 | SightDisplay | `+0x614` | int32 | `0x4141aa` |
| 7 | AmmoDisplay | `+0x618` | int32 | `0x4141cb` |
| 29 | GunModel | `+0x61c` | char[16] | `0x414463` |
| 30 | CasingModel | `+0x62c` | char[16] | `0x414487` |
| 9 | CalibreID | `+0x63c` | int32 | `0x41420d` |
| 14 | BulletsPerRound | `+0x640` | int32 | `0x4142b1` |
| 15 | RoundsPerMinute | `+0x644` | int32 | `0x4142d2` |
| 16 | RoundsPerClip | `+0x648` | int32 | `0x4142f3` |
| 17 | MaxRoundsPerBurst | `+0x64c` | int32 | `0x414314` |
| 25 | EffectiveRange | `+0x650` | float | `0x414408` |
| **10** | **DamageFactor** | **`+0x654`** | **float** | **`0x41422d`** |
| **11** | **PenetrationPower** | **`+0x658`** | **float** | **`0x41424d`** |
| 12 | ReloadTime | `+0x65c` | float | `0x414270` |
| 13 | MuzzleVelocity | `+0x660` | float | `0x414290` |
| 18 | MinSpread | `+0x664` | float | `0x414334` |
| 19 | MaxSpread | `+0x668` | float | `0x414354` |
| 20 | FixedViewChangeX | `+0x66c` | float | `0x414377` |
| 21 | FixedViewChangeZ | `+0x670` | float | `0x414397` |
| 22 | RandomViewChangeX | `+0x674` | float | `0x4143b9` |
| 23 | RandomViewChangeZ | `+0x678` | float | `0x4143d2` |
| 31 | StandAnim | `+0x67c` | int32 | `0x4144b4` |
| 32 | MoveAnim | `+0x680` | int32 | `0x4144d7` |
| 33 | FireAnim1 | `+0x684` | int32 | `0x4144f9` |
| 34 | FireAnim2 | `+0x688` | int32 | `0x41451a` |
| 35 | FireAnim3 | `+0x68c` | int32 | `0x41453b` |
| 36 | ReloadAnim | `+0x690` | int32 | `0x41455c` |
| 37 | UpperBodyStandAnim | `+0x694` | int32 | `0x41457d` |
| 38 | UpperBodyWalkAnim | `+0x698` | int32 | `0x41459e` |
| 41 | UpperBodyRunAnim | `+0x69c` | int32 | `0x414601` |
| 39 | UpperBodyCrouchAnim | `+0x6a0` | int32 | `0x4145bf` |
| 40 | UpperBodyCrouchRunAnim | `+0x6a4` | int32 | `0x4145e3` |
| 42 | UpperBodyFireAnim | `+0x6a8` | int32 | `0x414625` |
| 43 | UpperBodyReloadAnim | `+0x6ac` | int32 | `0x414640` |
| 44 | FireSoundLoop | `+0x6b0` | char[16] | `0x414652` |
| 45 | FireSoundLoopEnd | `+0x6c0` | char[16] | `0x414675` |
| 46 | AIDetectionRange | `+0x6d0` | float | `0x4146a1` |
| 47 | ProjectileTaskType | `+0x6d4` | int32 | `0x4146b9` |
| 48 | WeaponTaskType | `+0x6d8` | int32 | `0x41478c` |
| - | (constant `1`, not an argument) | `+0x6dc` | byte | `0x414167` |
| - | resolved projectile handler | `+0x6e0` | ptr | `0x41473b` |
| - | resolved weapon handler | `+0x6e4` | ptr | `0x414804` |

Two structural notes:

* The **string block order is not the script order**: arg 3 (Manufacturer) goes
  to `+0x310` and arg 4 (Description) to `+0x210`. The engine struct is
  `ScriptID, Name, Description, Manufacturer, TypeOfWeapon, WeaponUsers`.
* **Argument 49 ("Is weapon selectable when empty") is never read.** The last
  getter call in the handler is the one for arg 48; the byte at `+0x6dc` is
  written with the constant `1`:

  ```
  0x414167  mov byte [edx*8 + 0x56f084], 1
  ```

  So the "selectable when empty" flag is hard-coded TRUE regardless of the
  script value. (The only reference to `0x56f084` in `.text` is this store.)

### The damage formula ✅ VERIFIED

The human damage handler is `fcn.0045fcd0`, registered for the base `Human`
task type at `0x45e97b` (`push 0x45fcd0; call 0x4168d0; push eax; push Human;
call 0x401420`). It receives the damage event built by the projectile path and
applies:

```
0x45fd26  fld dword [esi + edi*8 + 0x10]     ; hitzone multiplier
0x45fd2a  fmul dword [ebp + 4]               ; * event->DamageFactor
0x45fd32  fadd dword [esi + edi*8 + 0x0c]    ; accumulate per hitzone
0x45fd3b  fadd dword [esi]                   ; accumulate total
0x45fd3f  fcomp dword [esi + 4]              ; vs max health
0x45fd4f  or ecx, 0x20000                    ; dead flag
```

```
damage_dealt         = hitzone_multiplier[hitzone] * DamageFactor
accumulated[hitzone] += damage_dealt
health.total         += damage_dealt
if (health.total >= health.max)  ->  dead
```

Health struct at `human+0x254`:

| Offset | Contents |
|--------|----------|
| `+0x00` | float total accumulated damage |
| `+0x04` | float max health |
| `+0x08` | pointer to the hitzone definition array (17 x 16-byte entries) |
| `+0x0c + i*8` | float accumulated damage for hitzone i |
| `+0x10 + i*8` | float multiplier for hitzone i |

`0x489aaa` initialises max health to `1.0f` (`mov dword [esi+0x258], 0x3f800000`),
so AI humans die at total damage 1.0. The player's threshold comes from
`DefineHumanPlayerGeneral` argument 7, stashed at `[0x56e954]` (`0x410179`) and
patched into `human+0x258` at `0x410531`.

### Difficulty scaling - player only ✅ VERIFIED

The player's damage path is a second copy of the same formula with one extra factor.
`fcn.004124b0` (which fetches the active player profile at `0x4124cf`) does:

```
0x412512  fld dword [ebp + ebx*8 + 0x10]   ; hitzone multiplier
0x412516  fmul dword [edi + 4]             ; * event->DamageFactor
0x412519  mov ecx, [eax]                   ; difficulty = active player profile +0x00
0x412524  je 0x412548                      ; 0 -> * 0.75   [0x53351c]
0x412527  je 0x412556                      ; 1 -> no multiply (1.0)
0x41252a  je 0x41253c                      ; 2 -> * 1.25   [0x533520]
0x41252c  push "Difficulty level not defined %d"   ; 0x5390d4
0x412563  fadd dword [ebp + ebx*8 + 0x0c]  ; accumulate per hitzone
```

```
damage_dealt     = hitzone_multiplier[hitzone] * DamageFactor * difficulty_scale
difficulty_scale = { 0.75 (easy), 1.0 (normal), 1.25 (hard) }
```

The scale is the first dword of the active player profile (`0x405b80` returns the
profile; `mov ecx, [eax]` at `0x412519`). Two more sites carry the same switch
(`0x412c74`, `0x412e93`), both in functions that fetch the player profile
(`0x412a1e`, `0x412d6d`). The AI handler `fcn.0045fcd0` has **no** difficulty factor -
the scaling is player-only.

### Damage-factor flow ✅ VERIFIED

```
weapon record +0x654 (Damage Factor)
  0x47b5ce  mov eax, dword [ebp + 0x654]     ; SpawnBullet reads it
  0x47b62c  mov dword [eax + 0x38], ecx      ; -> bullet +0x38
  0x47bd47  mov edx, dword [ebp + 0x38]      ; GunShot update reads it
  0x47bd67  mov dword [esp + 0x1ac], edx     ; -> damage event +0x04
  0x47be64  call ecx                         ; handler(obj, &event)
  0x45fd2a  fmul dword [ebp + 4]             ; handler multiplies by hitzone
```

The dispatch at `0x47be5d`/`0x47be64` is
`mov ecx, dword [ecx*4 + 0xa97240]` / `call ecx` - the same
`[category*384 + tasktype]` handler table that `RegisterTaskHandler` fills.
Weapon `+0x654` has exactly two readers in the binary: `0x47b5ce` (bullet spawn)
and `0x46e4e7` (the second damage applier used by `TASKTYPE_KNIFESTAB`).

### Penetration Power ✅ VERIFIED

The only reader of weapon `+0x658` in the binary is the bullet spawn at
`0x47b5c8` (`mov ecx, dword [ebp + 0x658]`). The value is copied to bullet
`+0x3c` and consumed exactly once, in the GunShot update at `0x47c195`:

```
0x47c195  fld dword [ebp + 0x3c]      ; Penetration Power
0x47c198  fsub dword [esi + 0x40]     ; - surface penetration resistance
0x47c19b  fcom dword [0x5333ec]       ; compare with 0.0
0x47c1b5  fcomp dword [0x53369c]      ; compare with 0.6
```

```
diff = PenetrationPower - surface_resistance
diff >= 1.0   ->  bullet continues through the object
diff == 0.0   ->  60% chance to continue
otherwise     ->  bullet stops (per-tick travel set to 0)
```

Constants: `0x5333ec` = `0.0f`, `0x5333e0` = `1.0f`, `0x53369c` = `0.6f`.

Damage is applied **before** this check (`0x47be64` runs before `0x47c195`), so
penetration gates continuation, not damage magnitude.

### Hitzones ✅ VERIFIED

17 entries x 16 bytes; only the first dword of each entry is the damage
multiplier (the other three dwords are model/bone indices). Multipliers are
`0.5/0.75/1.0` triples, then `1.0` x3, then `100.0` at indices 15/16 (head):

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|-----|---|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|----|
| multiplier | 0.5 | 0.75 | 1.0 | 0.5 | 0.75 | 1.0 | 0.5 | 0.75 | 1.0 | 0.5 | 0.75 | 1.0 | 1.0 | 1.0 | 1.0 | 100.0 | 100.0 |

* AI table `0x53f9d0` (passed by `HumanSoldier` at `0x45cf60`)
* player table `0x538a00` (passed at `0x410501`), script-writable via
  `DefineHumanPlayerGeneral` args 9..25 (`0x410195`)

The hitzone index comes from the model body part via the 30-entry table at
`0x541a04` (`mov edi, dword [eax*4 + 0x541a04]` at `0x489b4c`, bound
`cmp eax, 0x1e` at `0x489b1c`).

### Unresolved ❌

| Item | Status |
|------|--------|
| Identity of `[esi+0x40]` (the trace-result surface's penetration resistance) | ❌ Not identified - not the human health struct, not the `DefineGameMaterial` record (`0x569980`), not the Q-material record (`0x569960`) |
| Consumer of the second player hitzone table at `0x538b10` | ❌ Not located - `DefineHumanPlayerGeneral` fills 34 entries (`0x538a00`..`0x538c20`), `HealthReset` walks only 17 |
| Writer of `[esp+0x84]` in `0x47bb60` | ❌ Not located - gates an early "bullet stops" branch at `0x47bf13` |

## Damage Calculation

**Confidence:** ✅ VERIFIED - the formula has been extracted from `IGI.exe`; see
*Damage formula and parameter binding (IGI.exe)* above. The earlier formula in this
document was invented.

## Fire Rate (Guessed)

| Type | Description | Confidence |
|------|-------------|------------|
| Semi-auto | One shot per click | LOW - Assumed |
| Burst | 3 shots, then pause | LOW - Assumed |
| Full-auto | Continuous while held | LOW - Assumed |

## Spread (Guessed)

| Weapon | Spread | Confidence | Method |
|--------|--------|------------|--------|
| Pistol | 0.02 | LOW | Standard FPS convention |
| SMG | 0.05 | LOW | Standard FPS convention |
| Rifle | 0.03 | LOW | Standard FPS convention |
| Shotgun | 0.15 | LOW | Standard FPS convention |
| Sniper | 0.01 | LOW | Standard FPS convention |

## Weapon Switching (Guessed)

### Slots (Assumed)

| Slot | Weapons | Confidence |
|------|---------|------------|
| 1 | Pistols | LOW - Assumed |
| 2 | SMGs | LOW - Assumed |
| 3 | Shotguns | LOW - Assumed |
| 4 | Rifles | LOW - Assumed |
| 5 | Snipers | LOW - Assumed |
| 6 | Heavy | LOW - Assumed |
| 7 | Special | LOW - Assumed |

### Key Bindings (From config)

| Action | Key | Confidence | Method |
|--------|-----|------------|--------|
| Select slot 1-7 | 1-7 | HIGH | Configuration analysis |
| Previous weapon | Q | HIGH | Configuration analysis |
| Next weapon | E | HIGH | Configuration analysis |
| Reload | R | HIGH | Configuration analysis |
| Fire | Mouse1 | HIGH | Configuration analysis |
| Zoom/Sight | Mouse2 | HIGH | Configuration analysis |

## Reload System (Guessed)

| Weapon | Time (seconds) | Confidence | Method |
|--------|---------------|------------|--------|
| Pistol | 1.5 | LOW | Standard FPS convention |
| SMG | 2.0 | LOW | Standard FPS convention |
| Rifle | 2.5 | LOW | Standard FPS convention |
| Shotgun | 3.0 | LOW | Standard FPS convention |
| Sniper | 3.5 | LOW | Standard FPS convention |
| Heavy | 4.0 | LOW | Standard FPS convention |

## Zoom/Sights (Guessed)

| Weapon | Zoom | FOV | Confidence | Method |
|--------|------|-----|------------|--------|
| Pistol | 1.0x | 75° | LOW | Standard FPS convention |
| SMG | 1.0x | 75° | LOW | Standard FPS convention |
| Rifle | 2.0x | 45° | LOW | Standard FPS convention |
| Sniper | 4.0x | 20° | LOW | Standard FPS convention |
| Heavy | 1.0x | 75° | LOW | Standard FPS convention |

## Projectile System (Partly verified)

**Bullets:** spawned per shot (`SpawnBullet`, `0x47b5ce`) and advanced as per-tick
raycasts - the weapon's Effective Range (`+0x650`) x 4096 sets the per-tick travel
length (`bullet+0x34`, `0x47b5bc`/`0x47b5c2`); the penetration check gates continuation
(`0x47c195`). See *Damage formula and parameter binding (IGI.exe)*.

**Launchers and thrown weapons** (RPG18, M203, GRENADE, FLASHBANG, PROXIMITYMINE): the
trajectory and detonation paths are not traced.

## Explosion (Guessed)

```c
struct Explosion {
    Vec3 position;
    float radius;        // Damage radius
    float force;         // Knockback
    int damage;          // Center damage
    int falloff;         // Damage reduction
};
```

**Confidence:** LOW - Standard explosion structure assumption.

## Weapon Pickup (Guessed)

| Rule | Description | Confidence |
|------|-------------|------------|
| Max weapons | 2 | LOW - Standard FPS convention |
| Same weapon | Refills ammo | LOW - Standard FPS convention |
| Drop weapon | Drops all ammo | LOW - Standard FPS convention |

## Sound Effects (Guessed)

| Sound | Description | Confidence |
|-------|-------------|------------|
| fire | Shooting sound | LOW - Assumed |
| reload | Reload sound | LOW - Assumed |
| empty | Empty magazine click | LOW - Assumed |
| pickup | Weapon pickup | LOW - Assumed |

### Distance (Guessed)

| Property | Value | Confidence |
|----------|-------|------------|
| Max audible | 50 meters | LOW - Standard FPS convention |
| Attenuation | Linear | LOW - Standard FPS convention |

## Visual Effects (Guessed)

### Muzzle Flash (Guessed)

| Property | Value | Confidence |
|----------|-------|------------|
| Sprite at barrel | Yes | LOW - Assumed |
| Duration | 0.05 seconds | LOW - Standard FPS convention |
| Random rotation | Yes | LOW - Assumed |

### Tracers (Guessed)

| Property | Value | Confidence |
|----------|-------|------------|
| Frequency | Every 3rd bullet | LOW - Standard FPS convention |
| Color | Yellow | LOW - Standard FPS convention |
| Duration | 0.1 seconds | LOW - Standard FPS convention |

### Shell Ejection (Guessed)

| Property | Value | Confidence |
|----------|-------|------------|
| Brass casings | Yes | LOW - Assumed |
| Physics-based | Yes | LOW - Assumed |
| Despawn time | 2 seconds | LOW - Standard FPS convention |

## AI Weapon Loadouts (Guessed)

### Guard Loadout (Guessed)

| Slot | Weapon | Confidence |
|------|--------|------------|
| Primary | Rifle (M16 or AK-47) | LOW - Assumed |
| Secondary | Pistol (Beretta) | LOW - Assumed |
| Grenades | 0-2 | LOW - Assumed |

### Sniper Loadout (Guessed)

| Slot | Weapon | Confidence |
|------|--------|------------|
| Primary | Sniper rifle | LOW - Assumed |
| Secondary | Pistol | LOW - Assumed |
| Grenades | 0 | LOW - Assumed |

### Heavy Loadout (Guessed)

| Slot | Weapon | Confidence |
|------|--------|------------|
| Primary | Heavy weapon | LOW - Assumed |
| Secondary | Pistol | LOW - Assumed |
| Grenades | 2-4 | LOW - Assumed |

## Known Issues

1. **Weapon statistics** - all 24 weapons x 50 parameters extracted to `reverse/data/weapon_table.tsv`; the damage formula and penetration are recovered
2. **Ammo system** - the 14 ammo types and their `DefineAmmoType` parameter scripts are extracted; carry limits and pickup rules are not traced
3. **Damage calculation** - ✅ resolved, see *Damage formula and parameter binding (IGI.exe)*
4. **Projectile system** - the bullet path is traced (per-tick raycast); launcher/thrown trajectories are not
5. **Visual effects unverified** - Timing, colors, frequencies are guesses

## References

- Weapon data: weaponconfig.qsc → weapon~1.qvm
- Models: level{N}_models.res
- Sounds: SOUNDS/*.wav
- Configuration: config.qvm
