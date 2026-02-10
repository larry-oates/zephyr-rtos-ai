# Menuconfig Guide

Interactive tool for exploring and modifying Kconfig symbols.

## Launching Menuconfig

```bash
# After initial build
west build -t menuconfig

# GUI version (requires Tk)
west build -t guiconfig
```

**Note:** Run `west build` at least once before using menuconfig.

---

## Navigation

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate items |
| `Enter` | Enter submenu or toggle bool |
| `Esc` (2x) | Go back / Exit |
| `Space` | Toggle bool / Select choice |
| `?` | Show help for current item |
| `/` | **Search** (most useful!) |
| `Y` | Set bool to yes |
| `N` | Set bool to no |
| `M` | Set tristate to module (rarely used in Zephyr) |

### Search (`/`)

The most powerful feature for debugging:

1. Press `/`
2. Type symbol name (without `CONFIG_` prefix)
3. Results show:
   - **Defined at**: Source file and line
   - **Depends on**: What must be enabled
   - **Selected by**: What forces this on
   - **Implied by**: What suggests this
   - **Current value**: y/n/value

**Example search result:**
```
Symbol: LOG
Type  : bool
Prompt: Logging
  Location:
    -> Subsystems and OS Services
  Defined at subsys/logging/Kconfig:1
  Depends on: PRINTK
  Selected by: SHELL [=y]
```

---

## Common Tasks

### Find Why a Symbol is Disabled

1. Press `/`, search for symbol
2. Check "Depends on" — all must be satisfied
3. Trace each dependency recursively

### Find What Enables a Symbol

1. Search for the symbol
2. Check "Selected by" and "Implied by"
3. One of these is forcing the value

### Change a Value

1. Navigate to the symbol
2. For bool: press `Y` or `N`
3. For int/hex/string: press `Enter`, type value

### Save Changes

1. Press `Esc` twice to exit
2. Select "Yes" to save when prompted
3. Changes saved to `build/zephyr/.config`

**Note:** Changes are lost on clean rebuild. Copy to `prj.conf` for persistence:
```bash
grep CONFIG_MY_SETTING build/zephyr/.config >> prj.conf
```

---

## Guiconfig Features

The GUI version (`west build -t guiconfig`) adds:

- Tree view with expand/collapse
- Split view showing symbol info
- Regex search
- Show all symbols (including hidden)
- Jump to definition

---

## Workflow Integration

### Discovery Workflow
1. Build once: `west build -b <board> .`
2. Launch: `west build -t menuconfig`
3. Search and explore symbols
4. Note required settings
5. Add to `prj.conf` for permanence

### Debugging Workflow
1. Encounter Kconfig error
2. Launch menuconfig
3. Search for problematic symbol
4. Trace "Depends on" chain
5. Enable missing dependencies in `prj.conf`

---

## Tips

- **Hidden symbols**: Some symbols have no prompt (internal use). Search can still find them.
- **Gray items**: Dependencies not met. Check what they depend on.
- **[*] vs < >**: `[*]` is selected, `< >` is available but not selected.
- **-->**: Indicates a submenu.
