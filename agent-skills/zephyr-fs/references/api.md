# VFS API Reference

Complete API reference for Zephyr's Virtual File System abstraction.

## Header

```c
#include <zephyr/fs/fs.h>
```

## Data Types

### fs_file_t

File handle structure. Must be initialized with `fs_file_t_init()` before use.

```c
struct fs_file_t file;
fs_file_t_init(&file);  // Required before fs_open()
```

### fs_dir_t

Directory handle structure. Must be initialized with `fs_dir_t_init()` before use.

```c
struct fs_dir_t dir;
fs_dir_t_init(&dir);  // Required before fs_opendir()
```

### fs_dirent

Directory entry information returned by `fs_readdir()` and `fs_stat()`.

```c
struct fs_dirent {
    enum fs_dir_entry_type type;  // FS_DIR_ENTRY_FILE or FS_DIR_ENTRY_DIR
    char name[MAX_FILE_NAME + 1]; // Entry name
    size_t size;                   // File size (0 for directories)
};
```

### fs_statvfs

Volume statistics structure.

```c
struct fs_statvfs {
    unsigned long f_bsize;   // Optimal transfer block size
    unsigned long f_frsize;  // Allocation unit size
    unsigned long f_blocks;  // Size of FS in f_frsize units
    unsigned long f_bfree;   // Number of free blocks
};
```

### fs_mount_t

Mount point structure.

```c
struct fs_mount_t {
    int type;                // FS_FATFS, FS_LITTLEFS, FS_EXT2
    const char *mnt_point;   // Mount point path (e.g., "/lfs")
    void *fs_data;           // FS-specific config (e.g., littlefs_config)
    void *storage_dev;       // Storage device (partition ID or disk name)
    uint8_t flags;           // Mount flags
};
```

## Constants

### File Open Flags

| Flag | Value | Description |
|------|-------|-------------|
| `FS_O_READ` | 0x01 | Open for reading |
| `FS_O_WRITE` | 0x02 | Open for writing |
| `FS_O_RDWR` | 0x03 | Open for read and write |
| `FS_O_CREATE` | 0x10 | Create file if not exists |
| `FS_O_APPEND` | 0x20 | Append to end of file |
| `FS_O_TRUNC` | 0x40 | Truncate file to zero length |

### Seek Whence

| Constant | Value | Description |
|----------|-------|-------------|
| `FS_SEEK_SET` | 0 | Seek from beginning |
| `FS_SEEK_CUR` | 1 | Seek from current position |
| `FS_SEEK_END` | 2 | Seek from end |

### Mount Flags

| Flag | Description |
|------|-------------|
| `FS_MOUNT_FLAG_NO_FORMAT` | Don't format if FS not found |
| `FS_MOUNT_FLAG_READ_ONLY` | Mount read-only |
| `FS_MOUNT_FLAG_AUTOMOUNT` | Auto-mount on boot (fstab only) |
| `FS_MOUNT_FLAG_USE_DISK_ACCESS` | Use Disk Access API (not Flash API) |

### File System Types

| Type | Description |
|------|-------------|
| `FS_FATFS` | FAT/exFAT file system |
| `FS_LITTLEFS` | LittleFS file system |
| `FS_EXT2` | ext2 file system |
| `FS_VIRTIOFS` | VirtioFS (QEMU) |
| `FS_TYPE_EXTERNAL_BASE` | Base for custom FS types |

## File Operations

### fs_file_t_init

Initialize file handle. **Must be called before `fs_open()`.**

```c
static inline void fs_file_t_init(struct fs_file_t *zfp);
```

### fs_open

Open or create a file.

```c
int fs_open(struct fs_file_t *zfp, const char *file_name, fs_mode_t flags);
```

**Parameters:**
- `zfp`: Initialized file handle
- `file_name`: Absolute path (e.g., "/lfs/data.txt")
- `flags`: Combination of `FS_O_*` flags

**Returns:**
- `0` on success
- `-EBUSY` if handle already in use
- `-EINVAL` for invalid path
- `-EROFS` for read-only filesystem
- `-ENOENT` if file not found (and `FS_O_CREATE` not set)
- `-ENOTSUP` if not implemented

**Example:**
```c
struct fs_file_t file;
fs_file_t_init(&file);
int rc = fs_open(&file, "/lfs/config.txt", FS_O_CREATE | FS_O_RDWR);
if (rc < 0) {
    printk("Failed to open: %d\n", rc);
}
```

### fs_close

Close a file.

```c
int fs_close(struct fs_file_t *zfp);
```

**Returns:** `0` on success, negative errno on error.

### fs_read

Read from file.

```c
ssize_t fs_read(struct fs_file_t *zfp, void *ptr, size_t size);
```

**Returns:** Number of bytes read (may be less than `size`), or negative errno.

**Example:**
```c
char buf[128];
ssize_t bytes = fs_read(&file, buf, sizeof(buf));
if (bytes < 0) {
    printk("Read error: %zd\n", bytes);
} else {
    printk("Read %zd bytes\n", bytes);
}
```

### fs_write

Write to file.

```c
ssize_t fs_write(struct fs_file_t *zfp, const void *ptr, size_t size);
```

**Returns:** Number of bytes written, or negative errno.

**Note:** If return value is less than `size`, check `errno` for disk full condition.

### fs_seek

Move file position.

```c
int fs_seek(struct fs_file_t *zfp, off_t offset, int whence);
```

**Parameters:**
- `offset`: Position offset
- `whence`: `FS_SEEK_SET`, `FS_SEEK_CUR`, or `FS_SEEK_END`

**Returns:** `0` on success, negative errno on error.

### fs_tell

Get current file position.

```c
off_t fs_tell(struct fs_file_t *zfp);
```

**Returns:** Current position, or negative errno on error.

### fs_truncate

Truncate or extend file.

```c
int fs_truncate(struct fs_file_t *zfp, off_t length);
```

**Note:** Extension fills with zeros. If disk full during extension, extends to maximum possible and returns success.

### fs_sync

Flush cached data to storage.

```c
int fs_sync(struct fs_file_t *zfp);
```

**Note:** Not needed before `fs_close()` which flushes automatically.

## Directory Operations

### fs_dir_t_init

Initialize directory handle. **Must be called before `fs_opendir()`.**

```c
static inline void fs_dir_t_init(struct fs_dir_t *zdp);
```

### fs_opendir

Open directory for reading.

```c
int fs_opendir(struct fs_dir_t *zdp, const char *path);
```

### fs_readdir

Read next directory entry.

```c
int fs_readdir(struct fs_dir_t *zdp, struct fs_dirent *entry);
```

**Returns:** `0` on success. End-of-directory when `entry->name[0] == 0`.

**Note:** "." and ".." entries are filtered out for consistency.

**Example:**
```c
struct fs_dir_t dir;
struct fs_dirent entry;

fs_dir_t_init(&dir);
if (fs_opendir(&dir, "/lfs") == 0) {
    while (fs_readdir(&dir, &entry) == 0 && entry.name[0] != 0) {
        const char *type = (entry.type == FS_DIR_ENTRY_DIR) ? "DIR" : "FILE";
        printk("[%s] %s (%zu)\n", type, entry.name, entry.size);
    }
    fs_closedir(&dir);
}
```

### fs_closedir

Close directory.

```c
int fs_closedir(struct fs_dir_t *zdp);
```

### fs_mkdir

Create directory.

```c
int fs_mkdir(const char *path);
```

**Returns:**
- `0` on success
- `-EEXIST` if already exists
- `-EROFS` if read-only

### fs_unlink

Delete file or empty directory.

```c
int fs_unlink(const char *path);
```

### fs_rename

Rename or move file/directory.

```c
int fs_rename(const char *from, const char *to);
```

**Note:** Cannot move between mount points. Destination is overwritten if exists.

### fs_stat

Get file/directory information.

```c
int fs_stat(const char *path, struct fs_dirent *entry);
```

**Example:**
```c
struct fs_dirent entry;
if (fs_stat("/lfs/data.bin", &entry) == 0) {
    printk("Size: %zu bytes\n", entry.size);
}
```

## Mount Operations

### fs_mount

Mount a file system.

```c
int fs_mount(struct fs_mount_t *mp);
```

**Returns:**
- `0` on success
- `-ENOENT` if FS type not registered
- `-ENOTSUP` if mount not supported
- `-EROFS` if format needed but mounted read-only

**Example:**
```c
static struct fs_mount_t lfs_mnt = {
    .type = FS_LITTLEFS,
    .mnt_point = "/lfs",
    .fs_data = &lfs_config,
    .storage_dev = (void *)FIXED_PARTITION_ID(storage_partition),
};

int rc = fs_mount(&lfs_mnt);
```

### fs_unmount

Unmount a file system.

```c
int fs_unmount(struct fs_mount_t *mp);
```

### fs_readmount

Iterate through mount points.

```c
int fs_readmount(int *index, const char **name);
```

**Example:**
```c
int index = 0;
const char *name;
while (fs_readmount(&index, &name) == 0) {
    printk("Mounted: %s\n", name);
}
```

### fs_statvfs

Get volume statistics.

```c
int fs_statvfs(const char *path, struct fs_statvfs *stat);
```

**Example:**
```c
struct fs_statvfs stat;
if (fs_statvfs("/lfs", &stat) == 0) {
    size_t total = stat.f_blocks * stat.f_frsize;
    size_t free = stat.f_bfree * stat.f_frsize;
    printk("Total: %zu bytes, Free: %zu bytes\n", total, free);
}
```

### fs_mkfs

Format storage with file system.

```c
int fs_mkfs(int fs_type, uintptr_t dev_id, void *cfg, int flags);
```

**Requires:** `CONFIG_FILE_SYSTEM_MKFS=y`

**Parameters:**
- `fs_type`: `FS_LITTLEFS`, `FS_FATFS`, etc.
- `dev_id`: Device ID (partition ID or disk name pointer)
- `cfg`: FS-specific config (NULL for defaults)
- `flags`: Additional flags

**Example:**
```c
int rc = fs_mkfs(FS_LITTLEFS,
                  (uintptr_t)FIXED_PARTITION_ID(storage_partition),
                  NULL, 0);
```

### fs_gc

Trigger garbage collection (LittleFS).

```c
int fs_gc(struct fs_mount_t *mp);
```

**Note:** Only meaningful for file systems with garbage collection (LittleFS).

## Registration API

For implementing custom file systems.

### fs_register

Register a file system type.

```c
int fs_register(int type, const struct fs_file_system_t *fs);
```

### fs_unregister

Unregister a file system type.

```c
int fs_unregister(int type, const struct fs_file_system_t *fs);
```

## Fstab Macros

For working with devicetree-defined mount points.

### FSTAB_ENTRY_DT_MOUNT_FLAGS

Get mount flags from fstab node.

```c
#define FSTAB_ENTRY_DT_MOUNT_FLAGS(node_id)
```

### FS_FSTAB_ENTRY

Get the mount structure name for an fstab node.

```c
#define FS_FSTAB_ENTRY(node_id)
```

### FS_FSTAB_DECLARE_ENTRY

Declare an external fstab mount structure.

```c
#define FS_FSTAB_DECLARE_ENTRY(node_id)
```

**Example:**
```c
#define PARTITION_NODE DT_NODELABEL(lfs1)

FS_FSTAB_DECLARE_ENTRY(PARTITION_NODE);

void use_fstab_mount(void) {
    struct fs_mount_t *mp = &FS_FSTAB_ENTRY(PARTITION_NODE);
    // mp is automatically mounted if automount is set
}
```

## Common Error Codes

| Error | Meaning |
|-------|---------|
| `-ENOENT` | File/directory not found |
| `-EEXIST` | Entry already exists |
| `-EBUSY` | Handle already in use |
| `-EINVAL` | Invalid argument/path |
| `-EROFS` | Read-only file system |
| `-ENOSPC` | No space left on device |
| `-ENOTSUP` | Operation not supported |
| `-EBADF` | Bad file descriptor (unopened file) |
| `-EACCES` | Permission denied |

## Usage Patterns

### Safe File Read

```c
int read_file(const char *path, void *buf, size_t buf_size, size_t *bytes_read)
{
    struct fs_file_t file;
    fs_file_t_init(&file);

    int rc = fs_open(&file, path, FS_O_READ);
    if (rc < 0) {
        return rc;
    }

    ssize_t len = fs_read(&file, buf, buf_size);
    fs_close(&file);

    if (len < 0) {
        return len;
    }

    *bytes_read = len;
    return 0;
}
```

### Safe File Write

```c
int write_file(const char *path, const void *data, size_t len)
{
    struct fs_file_t file;
    fs_file_t_init(&file);

    int rc = fs_open(&file, path, FS_O_CREATE | FS_O_WRITE | FS_O_TRUNC);
    if (rc < 0) {
        return rc;
    }

    ssize_t written = fs_write(&file, data, len);
    int close_rc = fs_close(&file);

    if (written < 0) {
        return written;
    }
    if (written != len) {
        return -ENOSPC;
    }

    return close_rc;
}
```

### Check If File Exists

```c
bool file_exists(const char *path)
{
    struct fs_dirent entry;
    return fs_stat(path, &entry) == 0;
}
```
