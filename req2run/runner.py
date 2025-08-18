"""
Execution environment management for Req2Run evaluations
"""

import os
import time
import json
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import shutil

logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build execution status"""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class DeploymentStatus(Enum):
    """Deployment status"""

    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class BuildResult:
    """Result of build operation"""

    status: BuildStatus
    image_id: Optional[str] = None
    build_time: float = 0.0
    logs: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.logs is None:
            self.logs = []


@dataclass
class DeploymentConfig:
    """Configuration for deployment"""

    image: str
    name: str
    ports: Dict[int, int] = None
    environment: Dict[str, str] = None
    volumes: Dict[str, str] = None
    command: Optional[List[str]] = None
    resources: Dict[str, Any] = None
    healthcheck: Dict[str, Any] = None
    network: Optional[str] = None

    def __post_init__(self):
        if self.ports is None:
            self.ports = {}
        if self.environment is None:
            self.environment = {}
        if self.volumes is None:
            self.volumes = {}
        if self.resources is None:
            self.resources = {}


@dataclass
class DeploymentResult:
    """Result of deployment operation"""

    status: DeploymentStatus
    container_id: Optional[str] = None
    service_url: Optional[str] = None
    deployment_time: float = 0.0
    logs: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.logs is None:
            self.logs = []


@dataclass
class ExecutionResult:
    """Result of command execution"""

    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    timed_out: bool = False


class Runner(ABC):
    """Abstract base class for execution runners"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize runner with configuration

        Args:
            config: Runner-specific configuration
        """
        self.config = config or {}
        self.cleanup_resources = []

    @abstractmethod
    def build(
        self, submission_path: Path, dockerfile_path: Optional[Path] = None
    ) -> BuildResult:
        """
        Build submission into executable artifact

        Args:
            submission_path: Path to submission code
            dockerfile_path: Optional path to Dockerfile

        Returns:
            BuildResult with status and details
        """
        pass

    @abstractmethod
    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """
        Deploy built artifact

        Args:
            config: Deployment configuration

        Returns:
            DeploymentResult with status and details
        """
        pass

    @abstractmethod
    def execute(self, command: str, timeout: int = 60) -> ExecutionResult:
        """
        Execute command in deployed environment

        Args:
            command: Command to execute
            timeout: Execution timeout in seconds

        Returns:
            ExecutionResult with output and status
        """
        pass

    @abstractmethod
    def get_logs(self, container_id: str, tail: int = 100) -> List[str]:
        """
        Retrieve logs from running container

        Args:
            container_id: Container/pod identifier
            tail: Number of lines to retrieve

        Returns:
            List of log lines
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up all created resources"""
        pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup"""
        self.cleanup()


class DockerRunner(Runner):
    """Docker-based execution runner"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._ensure_docker_available()

    def _ensure_docker_available(self):
        """Check if Docker is available"""
        try:
            import docker

            self.client = docker.from_env()
            self.client.ping()
        except ImportError:
            raise RuntimeError("docker package not installed. Run: pip install docker")
        except Exception as e:
            raise RuntimeError(f"Docker not available: {str(e)}")

    def build(
        self, submission_path: Path, dockerfile_path: Optional[Path] = None
    ) -> BuildResult:
        """Build Docker image from submission"""
        import docker

        start_time = time.time()
        logs = []

        try:
            # Generate Dockerfile if not provided
            if not dockerfile_path:
                dockerfile_path = self._generate_dockerfile(submission_path)

            # Build image
            image_tag = f"req2run-{int(time.time())}"

            logger.info(f"Building Docker image: {image_tag}")
            image, build_logs = self.client.images.build(
                path=str(submission_path),
                dockerfile=str(dockerfile_path.relative_to(submission_path)),
                tag=image_tag,
                rm=True,
                forcerm=True,
            )

            # Collect build logs
            for log in build_logs:
                if "stream" in log:
                    logs.append(log["stream"].strip())

            self.cleanup_resources.append(("image", image.id))

            return BuildResult(
                status=BuildStatus.SUCCESS,
                image_id=image_tag,
                build_time=time.time() - start_time,
                logs=logs,
            )

        except docker.errors.BuildError as e:
            return BuildResult(
                status=BuildStatus.FAILED,
                build_time=time.time() - start_time,
                logs=logs,
                error_message=str(e),
            )
        except Exception as e:
            return BuildResult(
                status=BuildStatus.ERROR,
                build_time=time.time() - start_time,
                logs=logs,
                error_message=str(e),
            )

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy Docker container"""
        import docker

        start_time = time.time()
        logs = []

        try:
            # Prepare container configuration
            container_config = {
                "image": config.image,
                "name": config.name,
                "detach": True,
                "environment": config.environment,
                "ports": config.ports,
                "volumes": config.volumes,
                "auto_remove": False,
            }

            if config.command:
                container_config["command"] = config.command

            if config.resources:
                container_config["mem_limit"] = config.resources.get("memory", "2g")
                container_config["cpu_quota"] = config.resources.get(
                    "cpu_quota", 100000
                )

            if config.network:
                container_config["network"] = config.network

            # Start container
            logger.info(f"Starting container: {config.name}")
            container = self.client.containers.run(**container_config)

            self.cleanup_resources.append(("container", container.id))

            # Wait for container to be ready
            if config.healthcheck:
                ready = self._wait_for_health(container, config.healthcheck)
                if not ready:
                    return DeploymentResult(
                        status=DeploymentStatus.FAILED,
                        container_id=container.id,
                        deployment_time=time.time() - start_time,
                        error_message="Health check failed",
                    )

            # Get service URL
            service_url = self._get_service_url(container, config.ports)

            return DeploymentResult(
                status=DeploymentStatus.READY,
                container_id=container.id,
                service_url=service_url,
                deployment_time=time.time() - start_time,
                logs=logs,
            )

        except docker.errors.ContainerError as e:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                deployment_time=time.time() - start_time,
                logs=logs,
                error_message=str(e),
            )
        except Exception as e:
            return DeploymentResult(
                status=DeploymentStatus.ERROR,
                deployment_time=time.time() - start_time,
                logs=logs,
                error_message=str(e),
            )

    def execute(
        self, command: str, timeout: int = 60, container_id: Optional[str] = None
    ) -> ExecutionResult:
        """Execute command in container"""
        import docker

        start_time = time.time()

        try:
            if container_id:
                container = self.client.containers.get(container_id)
            else:
                # Get the most recent container
                containers = [
                    c
                    for r_type, r_id in self.cleanup_resources
                    if r_type == "container"
                ]
                if not containers:
                    raise RuntimeError("No container available for execution")
                container = self.client.containers.get(containers[-1])

            # Execute command
            result = container.exec_run(command, stdout=True, stderr=True, demux=True)

            stdout = result.output[0].decode() if result.output[0] else ""
            stderr = result.output[1].decode() if result.output[1] else ""

            return ExecutionResult(
                exit_code=result.exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=time.time() - start_time,
                timed_out=False,
            )

        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                timed_out=False,
            )

    def get_logs(self, container_id: str, tail: int = 100) -> List[str]:
        """Get container logs"""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode()
            return logs.split("\n")
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}")
            return []

    def cleanup(self):
        """Clean up Docker resources"""
        for resource_type, resource_id in reversed(self.cleanup_resources):
            try:
                if resource_type == "container":
                    container = self.client.containers.get(resource_id)
                    container.stop(timeout=10)
                    container.remove()
                    logger.info(f"Removed container: {resource_id}")
                elif resource_type == "image":
                    self.client.images.remove(resource_id, force=True)
                    logger.info(f"Removed image: {resource_id}")
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup {resource_type} {resource_id}: {str(e)}"
                )

        self.cleanup_resources.clear()

    def _generate_dockerfile(self, submission_path: Path) -> Path:
        """Generate Dockerfile based on detected language/framework"""
        # Detect language and framework
        language = self._detect_language(submission_path)

        dockerfile_content = self._get_dockerfile_template(language, submission_path)

        # Write Dockerfile
        dockerfile_path = submission_path / "Dockerfile.generated"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        return dockerfile_path

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from project files"""
        if (path / "package.json").exists():
            return "nodejs"
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "python"
        elif (path / "go.mod").exists():
            return "go"
        elif (path / "Cargo.toml").exists():
            return "rust"
        elif (path / "pom.xml").exists() or (path / "build.gradle").exists():
            return "java"
        else:
            return "unknown"

    def _get_dockerfile_template(self, language: str, submission_path: Path) -> str:
        """Get Dockerfile template for language"""
        templates = {
            "python": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt || pip install flask
COPY . .
EXPOSE 3000
CMD ["python", "app.py"]
""",
            "nodejs": """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production || npm install
COPY . .
EXPOSE 3000
CMD ["node", "index.js"]
""",
            "go": """FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 3000
CMD ["./main"]
""",
            "unknown": """FROM ubuntu:22.04
WORKDIR /app
COPY . .
EXPOSE 3000
CMD ["/bin/bash"]
""",
        }

        return templates.get(language, templates["unknown"])

    def _wait_for_health(self, container, healthcheck: Dict) -> bool:
        """Wait for container to be healthy"""
        import requests

        endpoint = healthcheck.get("endpoint", "/health")
        port = healthcheck.get("port", 3000)
        timeout = healthcheck.get("timeout", 30)
        interval = healthcheck.get("interval", 2)

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Get container IP
                container.reload()
                networks = container.attrs["NetworkSettings"]["Networks"]
                if networks:
                    ip = list(networks.values())[0]["IPAddress"]
                    url = f"http://{ip}:{port}{endpoint}"

                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"Container {container.name} is healthy")
                        return True
            except Exception as e:
                logger.debug(f"Health check failed: {str(e)}")

            time.sleep(interval)

        return False

    def _get_service_url(self, container, ports: Dict[int, int]) -> Optional[str]:
        """Get service URL for container"""
        if not ports:
            return None

        # Get first mapped port
        container_port = list(ports.keys())[0]
        host_port = ports[container_port]

        return f"http://localhost:{host_port}"


class LocalRunner(Runner):
    """Local process-based execution runner"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.processes = []
        self.temp_dirs = []

    def build(
        self, submission_path: Path, dockerfile_path: Optional[Path] = None
    ) -> BuildResult:
        """Build submission locally"""
        start_time = time.time()
        logs = []

        try:
            # Detect language and install dependencies
            language = self._detect_language(submission_path)

            if language == "python":
                if (submission_path / "requirements.txt").exists():
                    result = subprocess.run(
                        ["pip", "install", "-r", "requirements.txt"],
                        cwd=submission_path,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    logs.extend(result.stdout.split("\n"))
                    if result.returncode != 0:
                        raise RuntimeError(f"pip install failed: {result.stderr}")

            elif language == "nodejs":
                if (submission_path / "package.json").exists():
                    result = subprocess.run(
                        ["npm", "install"],
                        cwd=submission_path,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    logs.extend(result.stdout.split("\n"))
                    if result.returncode != 0:
                        raise RuntimeError(f"npm install failed: {result.stderr}")

            return BuildResult(
                status=BuildStatus.SUCCESS,
                image_id=str(submission_path),
                build_time=time.time() - start_time,
                logs=logs,
            )

        except subprocess.TimeoutExpired:
            return BuildResult(
                status=BuildStatus.TIMEOUT,
                build_time=time.time() - start_time,
                logs=logs,
                error_message="Build timed out",
            )
        except Exception as e:
            return BuildResult(
                status=BuildStatus.FAILED,
                build_time=time.time() - start_time,
                logs=logs,
                error_message=str(e),
            )

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy as local process"""
        start_time = time.time()
        logs = []

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment)

            # Determine command
            submission_path = Path(config.image)
            command = config.command or self._get_default_command(submission_path)

            # Start process
            logger.info(f"Starting local process: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                cwd=submission_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.processes.append(process)

            # Wait for process to be ready
            time.sleep(2)  # Simple wait, could be improved with health check

            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(f"Process exited immediately: {stderr}")

            # Get service URL
            port = list(config.ports.values())[0] if config.ports else 3000
            service_url = f"http://localhost:{port}"

            return DeploymentResult(
                status=DeploymentStatus.READY,
                container_id=str(process.pid),
                service_url=service_url,
                deployment_time=time.time() - start_time,
                logs=logs,
            )

        except Exception as e:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                deployment_time=time.time() - start_time,
                logs=logs,
                error_message=str(e),
            )

    def execute(self, command: str, timeout: int = 60) -> ExecutionResult:
        """Execute command locally"""
        start_time = time.time()

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )

            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=time.time() - start_time,
                timed_out=False,
            )

        except subprocess.TimeoutExpired as e:
            return ExecutionResult(
                exit_code=-1,
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                execution_time=timeout,
                timed_out=True,
            )
        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                timed_out=False,
            )

    def get_logs(self, container_id: str, tail: int = 100) -> List[str]:
        """Get process output"""
        # For local runner, this would need to capture process output
        # Implementation depends on how logs are managed
        return []

    def cleanup(self):
        """Clean up local processes"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.warning(f"Failed to terminate process: {str(e)}")

        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to remove temp dir: {str(e)}")

        self.processes.clear()
        self.temp_dirs.clear()

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from project files"""
        if (path / "package.json").exists():
            return "nodejs"
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "python"
        elif (path / "go.mod").exists():
            return "go"
        else:
            return "unknown"

    def _get_default_command(self, path: Path) -> List[str]:
        """Get default run command for project"""
        language = self._detect_language(path)

        if language == "python":
            if (path / "app.py").exists():
                return ["python", "app.py"]
            elif (path / "main.py").exists():
                return ["python", "main.py"]
        elif language == "nodejs":
            if (path / "index.js").exists():
                return ["node", "index.js"]
            elif (path / "app.js").exists():
                return ["node", "app.js"]

        return ["echo", "No default command found"]


class KubernetesRunner(Runner):
    """Kubernetes-based execution runner"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._ensure_kubernetes_available()

    def _ensure_kubernetes_available(self):
        """Check if Kubernetes is available"""
        try:
            from kubernetes import client, config as k8s_config

            # Try to load config
            try:
                k8s_config.load_incluster_config()
            except:
                k8s_config.load_kube_config()

            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()

            # Test connection
            self.v1.list_namespace()

        except ImportError:
            raise RuntimeError(
                "kubernetes package not installed. Run: pip install kubernetes"
            )
        except Exception as e:
            raise RuntimeError(f"Kubernetes not available: {str(e)}")

    def build(
        self, submission_path: Path, dockerfile_path: Optional[Path] = None
    ) -> BuildResult:
        """Build image for Kubernetes (typically using Docker)"""
        # For Kubernetes, we typically build with Docker and push to registry
        # This is a simplified version
        docker_runner = DockerRunner(self.config)
        return docker_runner.build(submission_path, dockerfile_path)

    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy to Kubernetes"""
        from kubernetes import client

        start_time = time.time()
        namespace = self.config.get("namespace", "default")

        try:
            # Create deployment
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(name=config.name),
                spec=client.V1DeploymentSpec(
                    replicas=1,
                    selector=client.V1LabelSelector(match_labels={"app": config.name}),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(labels={"app": config.name}),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=config.name,
                                    image=config.image,
                                    ports=(
                                        [
                                            client.V1ContainerPort(container_port=port)
                                            for port in config.ports.keys()
                                        ]
                                        if config.ports
                                        else None
                                    ),
                                    env=(
                                        [
                                            client.V1EnvVar(name=k, value=v)
                                            for k, v in config.environment.items()
                                        ]
                                        if config.environment
                                        else None
                                    ),
                                    resources=(
                                        client.V1ResourceRequirements(
                                            limits=config.resources
                                        )
                                        if config.resources
                                        else None
                                    ),
                                )
                            ]
                        ),
                    ),
                ),
            )

            self.apps_v1.create_namespaced_deployment(
                namespace=namespace, body=deployment
            )

            self.cleanup_resources.append(("deployment", config.name))

            # Create service if ports are specified
            if config.ports:
                service = client.V1Service(
                    metadata=client.V1ObjectMeta(name=config.name),
                    spec=client.V1ServiceSpec(
                        selector={"app": config.name},
                        ports=[
                            client.V1ServicePort(
                                port=host_port, target_port=container_port
                            )
                            for container_port, host_port in config.ports.items()
                        ],
                        type="NodePort",
                    ),
                )

                self.v1.create_namespaced_service(namespace=namespace, body=service)

                self.cleanup_resources.append(("service", config.name))

            # Wait for deployment to be ready
            ready = self._wait_for_deployment(config.name, namespace)

            if not ready:
                return DeploymentResult(
                    status=DeploymentStatus.FAILED,
                    deployment_time=time.time() - start_time,
                    error_message="Deployment not ready",
                )

            return DeploymentResult(
                status=DeploymentStatus.READY,
                container_id=config.name,
                deployment_time=time.time() - start_time,
            )

        except Exception as e:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                deployment_time=time.time() - start_time,
                error_message=str(e),
            )

    def execute(self, command: str, timeout: int = 60) -> ExecutionResult:
        """Execute command in Kubernetes pod"""
        from kubernetes.stream import stream

        namespace = self.config.get("namespace", "default")
        start_time = time.time()

        try:
            # Get pod name
            pods = self.v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={self.cleanup_resources[-1][1]}",
            )

            if not pods.items:
                raise RuntimeError("No pods found")

            pod_name = pods.items[0].metadata.name

            # Execute command
            resp = stream(
                self.v1.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=command.split(),
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )

            return ExecutionResult(
                exit_code=0,
                stdout=resp,
                stderr="",
                execution_time=time.time() - start_time,
                timed_out=False,
            )

        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                timed_out=False,
            )

    def get_logs(self, container_id: str, tail: int = 100) -> List[str]:
        """Get pod logs"""
        namespace = self.config.get("namespace", "default")

        try:
            logs = self.v1.read_namespaced_pod_log(
                name=container_id, namespace=namespace, tail_lines=tail
            )
            return logs.split("\n")
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}")
            return []

    def cleanup(self):
        """Clean up Kubernetes resources"""
        namespace = self.config.get("namespace", "default")

        for resource_type, resource_name in reversed(self.cleanup_resources):
            try:
                if resource_type == "deployment":
                    self.apps_v1.delete_namespaced_deployment(
                        name=resource_name, namespace=namespace
                    )
                    logger.info(f"Deleted deployment: {resource_name}")
                elif resource_type == "service":
                    self.v1.delete_namespaced_service(
                        name=resource_name, namespace=namespace
                    )
                    logger.info(f"Deleted service: {resource_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup {resource_type} {resource_name}: {str(e)}"
                )

        self.cleanup_resources.clear()

    def _wait_for_deployment(
        self, name: str, namespace: str, timeout: int = 60
    ) -> bool:
        """Wait for deployment to be ready"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=name, namespace=namespace
                )

                if deployment.status.ready_replicas == deployment.spec.replicas:
                    return True

            except Exception as e:
                logger.debug(f"Deployment not ready: {str(e)}")

            time.sleep(2)

        return False


def create_runner(environment: str = "docker", config: Dict[str, Any] = None) -> Runner:
    """
    Factory function to create appropriate runner

    Args:
        environment: Execution environment (docker, kubernetes, local)
        config: Runner-specific configuration

    Returns:
        Runner instance
    """
    runners = {
        "docker": DockerRunner,
        "kubernetes": KubernetesRunner,
        "k8s": KubernetesRunner,
        "local": LocalRunner,
    }

    runner_class = runners.get(environment.lower())
    if not runner_class:
        raise ValueError(f"Unknown environment: {environment}")

    return runner_class(config)
