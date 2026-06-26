# 06 - Weapons System

## Weapon List (From QVM scripts)

**Confidence:** MEDIUM - Weapon names and categories extracted from QVM analysis. Specific statistics are unverified.

### Pistols

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 1 | Desert Eagle | Unknown | Semi | ACP | Unknown | LOW | QVM analysis |
| 2 | Beretta | Unknown | Semi | ACP | Unknown | LOW | QVM analysis |
| 3 | revolver | Unknown | Semi | Magnum | Unknown | LOW | QVM analysis |

### SMGs

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 4 | Uzi | Unknown | Full | ACP | Unknown | LOW | QVM analysis |
| 5 | MP5 | Unknown | Full | ACP | Unknown | LOW | QVM analysis |
| 6 | P90 | Unknown | Full | FN | Unknown | LOW | QVM analysis |

### Shotguns

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 7 | M1014 | Unknown | Semi | Shell | Unknown | LOW | QVM analysis |
| 8 | SPAS-12 | Unknown | Pump | Shell | Unknown | LOW | QVM analysis |

### Rifles

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 9 | M16 | Unknown | Burst | 5.56 | Unknown | LOW | QVM analysis |
| 10 | AK-47 | Unknown | Full | 7.62 | Unknown | LOW | QVM analysis |
| 11 | G36 | Unknown | Full | 5.56 | Unknown | LOW | QVM analysis |
| 12 | FAMAS | Unknown | Burst | 5.56 | Unknown | LOW | QVM analysis |

### Snipers

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 13 | PSG-1 | Unknown | Semi | 7.62 | Unknown | LOW | QVM analysis |
| 14 | Dragunov | Unknown | Semi | 7.62 | Unknown | LOW | QVM analysis |
| 15 | Barrett | Unknown | Bolt | .50 | Unknown | LOW | QVM analysis |

### Heavy

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 16 | M249 | Unknown | Full | 5.56 | Unknown | LOW | QVM analysis |
| 17 | M60 | Unknown | Full | 7.62 | Unknown | LOW | QVM analysis |
| 18 | RPG-7 | Unknown | Reload | Rocket | Unknown | LOW | QVM analysis |

### Special

| ID | Name | Damage | Fire Rate | Ammo | Magazine | Confidence | Method |
|----|------|--------|-----------|------|----------|------------|--------|
| 19 | M67 Grenade | Unknown | Throw | - | Unknown | LOW | QVM analysis |
| 20 | Flashbang | Unknown | Throw | - | Unknown | LOW | QVM analysis |
| 21 | Smoke | Unknown | Throw | - | Unknown | LOW | QVM analysis |

## Ammo Types

| ID | Name | Weight | Max Carry | Confidence | Method |
|----|------|--------|-----------|------------|--------|
| 1 | ACP (9mm) | Unknown | Unknown | LOW | QVM analysis |
| 2 | 5.56mm | Unknown | Unknown | LOW | QVM analysis |
| 3 | 7.62mm | Unknown | Unknown | LOW | QVM analysis |
| 4 | Shotgun Shell | Unknown | Unknown | LOW | QVM analysis |
| 5 | FN (5.7mm) | Unknown | Unknown | LOW | QVM analysis |

**Note:** Ammo weights and carry limits are unknown. Previous documentation stated specific values, but these are unverified.

## Weapon Properties (Reconstructed)

**Warning:** The following structure is a reconstruction based on common game patterns. The actual weapon data structure is unknown.

```c
struct Weapon {
    int id;
    char name[32];
    int damage;           // Unknown actual values
    float fire_rate;      // Unknown actual values
    int ammo_type;
    int magazine_size;    // Unknown actual values
    float reload_time;    // Unknown actual values
    float spread;         // Unknown actual values
    float range;          // Unknown actual values
    int burst_count;      // Unknown actual values
    float recoil;         // Unknown actual values
    int model_id;
    int sound_fire;
    int sound_reload;
    int sound_empty;
};
```

**Confidence:** LOW - This is a guess at the data structure, not extracted from source.

## Damage Calculation (Guessed)

**Warning:** This damage formula is a guess based on standard FPS patterns. The actual damage system is unknown.

```
final_damage = base_damage * distance_factor * spread_factor

distance_factor = 1.0 - (distance / max_range * 0.5)
spread_factor = 1.0 if hit, 0.5 if miss
```

**Confidence:** LOW - Standard FPS damage model assumption.

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

## Projectile System (Guessed)

### Hitscan Weapons (Assumed)

- Pistols, SMGs, Rifles, Snipers
- Instant hit
- Raycast from camera

**Confidence:** LOW - Standard FPS convention.

### Projectile Weapons (Assumed)

- RPG-7, Grenades
- Physics-based trajectory
- Explosion on impact

**Confidence:** LOW - Standard FPS convention.

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

1. **All weapon statistics unknown** - Damage, fire rate, reload time, spread, range are all unverified
2. **Ammo system unknown** - Weights, carry limits, damage multipliers unknown
3. **Damage calculation unverified** - Formula is a guess
4. **Projectile system unverified** - Hitscan vs projectile classification assumed
5. **Visual effects unverified** - Timing, colors, frequencies are guesses

## References

- Weapon data: weaponconfig.qsc → weapon~1.qvm
- Models: level{N}_models.res
- Sounds: SOUNDS/*.wav
- Configuration: config.qvm
