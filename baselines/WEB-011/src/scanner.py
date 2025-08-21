"""Malware scanning service for uploaded files"""
import asyncio
import tempfile
import os
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
import hashlib
import structlog

try:
    import clamd
    CLAMAV_AVAILABLE = True
except ImportError:
    CLAMAV_AVAILABLE = False

from models import ScanStatus, ScanResult


logger = structlog.get_logger()


class MalwareScanResult:
    """Result of malware scan"""
    
    def __init__(self, 
                 status: ScanStatus, 
                 threats: List[str] = None,
                 scan_engine: str = "unknown",
                 scan_details: Dict[str, Any] = None):
        self.status = status
        self.threats = threats or []
        self.scan_engine = scan_engine
        self.scan_details = scan_details or {}
        self.scanned_at = datetime.utcnow()


class ClamAVScanner:
    """ClamAV-based malware scanner"""
    
    def __init__(self, 
                 clamd_socket: Optional[str] = None,
                 clamd_host: str = "localhost",
                 clamd_port: int = 3310,
                 timeout: int = 60):
        
        self.timeout = timeout
        self.scanner = None
        
        if not CLAMAV_AVAILABLE:
            logger.warning("ClamAV not available, malware scanning disabled")
            return
        
        try:
            if clamd_socket:
                self.scanner = clamd.ClamdUnixSocket(clamd_socket, timeout=timeout)
            else:
                self.scanner = clamd.ClamdNetworkSocket(clamd_host, clamd_port, timeout=timeout)
            
            # Test connection
            self.scanner.ping()
            version = self.scanner.version()
            logger.info("ClamAV scanner initialized", version=version)
            
        except Exception as e:
            logger.error("Failed to initialize ClamAV scanner", error=str(e))
            self.scanner = None
    
    def is_available(self) -> bool:
        """Check if scanner is available"""
        return self.scanner is not None
    
    async def scan_file_content(self, file_content: bytes, filename: str = "") -> MalwareScanResult:
        """Scan file content for malware"""
        if not self.is_available():
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="clamav",
                scan_details={"error": "Scanner not available"}
            )
        
        try:
            # Run scan in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._scan_content_sync, 
                file_content, 
                filename
            )
            
            return result
            
        except Exception as e:
            logger.error("File scan failed", filename=filename, error=str(e))
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="clamav",
                scan_details={"error": str(e)}
            )
    
    def _scan_content_sync(self, file_content: bytes, filename: str) -> MalwareScanResult:
        """Synchronous file content scan"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Scan the temporary file
                scan_result = self.scanner.scan(temp_file_path)
                
                if scan_result is None:
                    # Clean file
                    logger.info("File scan clean", filename=filename)
                    return MalwareScanResult(
                        status=ScanStatus.CLEAN,
                        scan_engine="clamav",
                        scan_details={
                            "file_size": len(file_content),
                            "scan_type": "file_content"
                        }
                    )
                else:
                    # Threats found
                    threats = []
                    for file_path, threat_info in scan_result.items():
                        threat_status, threat_name = threat_info
                        if threat_status == "FOUND":
                            threats.append(threat_name)
                    
                    logger.warning("File scan found threats", 
                                 filename=filename, threats=threats)
                    
                    return MalwareScanResult(
                        status=ScanStatus.INFECTED,
                        threats=threats,
                        scan_engine="clamav",
                        scan_details={
                            "file_size": len(file_content),
                            "scan_type": "file_content",
                            "full_result": scan_result
                        }
                    )
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
        
        except Exception as e:
            logger.error("ClamAV scan error", filename=filename, error=str(e))
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="clamav",
                scan_details={"error": str(e)}
            )
    
    async def scan_file_path(self, file_path: str) -> MalwareScanResult:
        """Scan file by path"""
        if not self.is_available():
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="clamav",
                scan_details={"error": "Scanner not available"}
            )
        
        try:
            # Run scan in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._scan_path_sync, 
                file_path
            )
            
            return result
            
        except Exception as e:
            logger.error("File path scan failed", file_path=file_path, error=str(e))
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="clamav",
                scan_details={"error": str(e)}
            )
    
    def _scan_path_sync(self, file_path: str) -> MalwareScanResult:
        """Synchronous file path scan"""
        try:
            scan_result = self.scanner.scan(file_path)
            file_size = os.path.getsize(file_path)
            
            if scan_result is None:
                return MalwareScanResult(
                    status=ScanStatus.CLEAN,
                    scan_engine="clamav",
                    scan_details={
                        "file_size": file_size,
                        "scan_type": "file_path"
                    }
                )
            else:
                threats = []
                for path, threat_info in scan_result.items():
                    threat_status, threat_name = threat_info
                    if threat_status == "FOUND":
                        threats.append(threat_name)
                
                return MalwareScanResult(
                    status=ScanStatus.INFECTED,
                    threats=threats,
                    scan_engine="clamav",
                    scan_details={
                        "file_size": file_size,
                        "scan_type": "file_path",
                        "full_result": scan_result
                    }
                )
        
        except Exception as e:
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="clamav",
                scan_details={"error": str(e)}
            )


class HashBasedScanner:
    """Simple hash-based malware scanner for testing"""
    
    def __init__(self):
        # Known malware hashes (for testing)
        self.malware_hashes = {
            # EICAR test string hash
            "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "EICAR-Test-File",
            # Add more test hashes as needed
        }
    
    def is_available(self) -> bool:
        """Always available"""
        return True
    
    async def scan_file_content(self, file_content: bytes, filename: str = "") -> MalwareScanResult:
        """Scan file content using hash comparison"""
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check against known malware hashes
            if file_hash in self.malware_hashes:
                threat_name = self.malware_hashes[file_hash]
                logger.warning("Hash-based scan found threat", 
                             filename=filename, 
                             threat=threat_name,
                             hash=file_hash[:16])
                
                return MalwareScanResult(
                    status=ScanStatus.INFECTED,
                    threats=[threat_name],
                    scan_engine="hash_scanner",
                    scan_details={
                        "file_hash": file_hash,
                        "file_size": len(file_content)
                    }
                )
            
            # File is clean
            logger.info("Hash-based scan clean", filename=filename, hash=file_hash[:16])
            return MalwareScanResult(
                status=ScanStatus.CLEAN,
                scan_engine="hash_scanner",
                scan_details={
                    "file_hash": file_hash,
                    "file_size": len(file_content)
                }
            )
        
        except Exception as e:
            logger.error("Hash scan error", filename=filename, error=str(e))
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="hash_scanner",
                scan_details={"error": str(e)}
            )


class CompositeMalwareScanner:
    """Composite scanner that uses multiple scanning engines"""
    
    def __init__(self, 
                 enable_clamav: bool = True,
                 enable_hash_scanner: bool = True,
                 clamd_socket: Optional[str] = None,
                 clamd_host: str = "localhost",
                 clamd_port: int = 3310):
        
        self.scanners = []
        
        # Initialize ClamAV scanner
        if enable_clamav:
            clamav_scanner = ClamAVScanner(
                clamd_socket=clamd_socket,
                clamd_host=clamd_host,
                clamd_port=clamd_port
            )
            if clamav_scanner.is_available():
                self.scanners.append(clamav_scanner)
        
        # Initialize hash-based scanner
        if enable_hash_scanner:
            self.scanners.append(HashBasedScanner())
        
        if not self.scanners:
            logger.warning("No malware scanners available")
        else:
            scanner_names = [scanner.__class__.__name__ for scanner in self.scanners]
            logger.info("Composite scanner initialized", scanners=scanner_names)
    
    def is_available(self) -> bool:
        """Check if any scanner is available"""
        return len(self.scanners) > 0
    
    async def scan_file_content(self, file_content: bytes, filename: str = "") -> List[MalwareScanResult]:
        """Scan file content with all available scanners"""
        if not self.is_available():
            return [MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="composite",
                scan_details={"error": "No scanners available"}
            )]
        
        results = []
        
        # Run all scanners
        for scanner in self.scanners:
            try:
                result = await scanner.scan_file_content(file_content, filename)
                results.append(result)
            except Exception as e:
                logger.error("Scanner failed", 
                           scanner=scanner.__class__.__name__, 
                           filename=filename, 
                           error=str(e))
                results.append(MalwareScanResult(
                    status=ScanStatus.ERROR,
                    scan_engine=scanner.__class__.__name__.lower(),
                    scan_details={"error": str(e)}
                ))
        
        return results
    
    def get_composite_result(self, results: List[MalwareScanResult]) -> MalwareScanResult:
        """Combine multiple scan results into a single result"""
        if not results:
            return MalwareScanResult(
                status=ScanStatus.ERROR,
                scan_engine="composite",
                scan_details={"error": "No scan results"}
            )
        
        # Collect all threats
        all_threats = []
        clean_count = 0
        error_count = 0
        
        scan_details = {
            "scanner_results": [],
            "total_scanners": len(results)
        }
        
        for result in results:
            scan_details["scanner_results"].append({
                "engine": result.scan_engine,
                "status": result.status.value,
                "threats": result.threats,
                "details": result.scan_details
            })
            
            if result.status == ScanStatus.INFECTED:
                all_threats.extend(result.threats)
            elif result.status == ScanStatus.CLEAN:
                clean_count += 1
            elif result.status == ScanStatus.ERROR:
                error_count += 1
        
        # Determine final status
        if all_threats:
            # Any scanner found threats
            final_status = ScanStatus.INFECTED
        elif error_count == len(results):
            # All scanners failed
            final_status = ScanStatus.ERROR
        elif clean_count > 0:
            # At least one scanner says clean
            final_status = ScanStatus.CLEAN
        else:
            # Shouldn't happen, but default to error
            final_status = ScanStatus.ERROR
        
        return MalwareScanResult(
            status=final_status,
            threats=list(set(all_threats)),  # Remove duplicates
            scan_engine="composite",
            scan_details=scan_details
        )