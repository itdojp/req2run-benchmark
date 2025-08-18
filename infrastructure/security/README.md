# Security Sandbox Configuration

This directory contains security sandbox configurations for safely executing untrusted code submissions in the Req2Run benchmark framework.

## Overview

The sandbox provides:
- **Process isolation**: Separate namespaces for PID, network, IPC
- **Resource limits**: CPU, memory, disk, and time constraints
- **Filesystem restrictions**: Read-only system directories, limited write access
- **Network isolation**: No network access by default
- **System call filtering**: Seccomp-BPF policies to restrict dangerous syscalls

## Supported Backends

### 1. nsjail (Recommended)
- Google's lightweight sandboxing tool
- Better performance and security
- Configuration: `nsjail.cfg`

### 2. firejail
- User-friendly sandboxing tool
- Broader compatibility
- Configuration: `firejail.profile`

## Installation

### Ubuntu/Debian
```bash
# nsjail
sudo apt-get install libnl-3-dev libprotobuf-dev protobuf-compiler
git clone https://github.com/google/nsjail.git
cd nsjail && make && sudo make install

# firejail
sudo apt-get install firejail
```

### macOS
```bash
# Use Docker instead (nsjail/firejail are Linux-only)
docker pull ghcr.io/itdojp/req2run-sandbox
```

## Usage

### Python API
```python
from infrastructure.security.sandbox_runner import SandboxRunner

runner = SandboxRunner(backend="auto")  # auto-detect available backend
result = runner.execute(
    command="python main.py",
    submission_path=Path("./submission"),
    problem_id="WEB-001",
    timeout=300,
    memory_limit=2048,
    cpu_limit=2
)

print(f"Success: {result['success']}")
print(f"Output: {result['stdout']}")
```

### Command Line
```bash
# Run with auto-detected backend
python sandbox-runner.py "python main.py" ./submission --problem WEB-001

# Force specific backend
python sandbox-runner.py "node app.js" ./submission --backend nsjail

# With resource limits
python sandbox-runner.py "go run main.go" ./submission \
    --timeout 60 --memory 1024 --cpu 1
```

## Security Policies

### Default Restrictions
- **No network access** (can be enabled per problem)
- **Read-only system directories** (/usr, /lib, /bin)
- **Limited write access** (/app, /tmp only)
- **No privilege escalation**
- **Restricted system calls**

### Resource Limits
| Resource | Default | Maximum |
|----------|---------|---------|
| CPU Time | 5 min | 10 min |
| Memory | 2 GB | 4 GB |
| Disk Write | 100 MB | 500 MB |
| Open Files | 256 | 1024 |
| Processes | 32 | 64 |

### Allowed System Calls
Basic operations only:
- File I/O (read, write, open, close)
- Memory management (mmap, brk)
- Process management (fork, execve, wait)
- Time functions (gettimeofday, clock_gettime)

### Blocked System Calls
Dangerous operations:
- Network operations (socket, connect, bind)
- Privilege changes (setuid, setgid)
- Kernel modules (init_module, delete_module)
- System administration (mount, umount, reboot)

## Problem-Specific Configuration

Problems can specify their requirements in YAML:

```yaml
constraints:
  disallowed_syscalls:
    - network
    - exec
  resource_limits:
    max_cpu_cores: 2
    max_memory_gb: 1
    
non_functional:
  security:
    network_egress: DENY  # or ALLOW for network problems
```

## Docker Alternative

For environments where nsjail/firejail aren't available:

```dockerfile
FROM python:3.11-slim
RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /app
# ... rest of Dockerfile
```

Run with Docker security options:
```bash
docker run \
  --security-opt no-new-privileges \
  --security-opt seccomp=seccomp-profile.json \
  --cap-drop ALL \
  --network none \
  --memory 2g \
  --cpus 2 \
  sandbox-image
```

## Testing Sandbox

Test the sandbox configuration:

```bash
# Test basic execution
python sandbox-runner.py "echo 'Hello, World!'" /tmp --problem test

# Test resource limits
python sandbox-runner.py "python -c 'a = [0] * (10**9)'" /tmp --memory 100

# Test timeout
python sandbox-runner.py "sleep 10" /tmp --timeout 5

# Test network isolation
python sandbox-runner.py "curl google.com" /tmp
```

## Security Considerations

1. **Always validate input** before sandboxing
2. **Monitor resource usage** during execution
3. **Log all executions** for audit trail
4. **Regularly update** sandbox tools
5. **Test escape attempts** periodically

## Troubleshooting

### "No sandbox backend found"
Install nsjail or firejail as described above.

### "Permission denied"
Ensure the sandbox runner has necessary permissions:
```bash
sudo setcap cap_sys_admin+ep /usr/local/bin/nsjail
```

### "Resource limit exceeded"
Adjust limits in configuration files or command line arguments.

## References

- [nsjail Documentation](https://github.com/google/nsjail)
- [firejail Documentation](https://firejail.wordpress.com/)
- [Seccomp BPF](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
- [Linux Namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html)