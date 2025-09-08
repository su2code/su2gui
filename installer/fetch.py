"""
Download utilities with progress tracking
"""
import hashlib
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from contextlib import contextmanager

from .constants import DEFAULT_CHUNK_SIZE, DEFAULT_TIMEOUT, MAX_RETRIES


class DownloadError(Exception):
    """Custom exception for download errors."""
    pass


class ProgressTracker:
    """Simple progress tracking for downloads."""
    
    def __init__(self, total_size: int = 0):
        self.total_size = total_size
        self.downloaded = 0
        self.start_time = time.time()
        
    def update(self, chunk_size: int):
        """Update progress with downloaded chunk size."""
        self.downloaded += chunk_size
        
    def get_progress(self) -> float:
        """Get progress as percentage (0-100)."""
        if self.total_size == 0:
            return 0.0
        return min(100.0, (self.downloaded / self.total_size) * 100.0)
    
    def get_speed(self) -> float:
        """Get download speed in bytes per second."""
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.downloaded / elapsed
    
    def get_eta(self) -> float:
        """Get estimated time to completion in seconds."""
        if self.total_size == 0 or self.downloaded == 0:
            return 0.0
        speed = self.get_speed()
        if speed == 0:
            return 0.0
        remaining = self.total_size - self.downloaded
        return remaining / speed


def format_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_speed(speed_bps: float) -> str:
    """
    Format download speed as human-readable string.
    
    Args:
        speed_bps: Speed in bytes per second
        
    Returns:
        Formatted string (e.g., "1.5 MB/s")
    """
    return f"{format_size(int(speed_bps))}/s"


def format_time(seconds: float) -> str:
    """
    Format time duration as human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


@contextmanager
def download_context(url: str, timeout: int = DEFAULT_TIMEOUT):
    """
    Context manager for URL downloads with proper error handling.
    
    Args:
        url: URL to download
        timeout: Timeout in seconds
        
    Yields:
        urllib response object
    """
    try:
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'SU2GUI-Installer/1.0')
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            yield response
            
    except urllib.error.HTTPError as e:
        raise DownloadError(f"HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise DownloadError(f"URL Error: {e.reason}")
    except Exception as e:
        raise DownloadError(f"Download failed: {str(e)}")


def get_content_length(url: str) -> Optional[int]:
    """
    Get content length from URL headers.
    
    Args:
        url: URL to check
        
    Returns:
        Content length in bytes or None if unavailable
    """
    try:
        with download_context(url) as response:
            content_length = response.info().get('Content-Length')
            return int(content_length) if content_length else None
    except:
        return None


def download_file(
    url: str,
    destination: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[ProgressTracker], None]] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> None:
    """
    Download file with progress tracking.
    
    Args:
        url: URL to download
        destination: Destination file path
        chunk_size: Size of download chunks
        progress_callback: Optional callback for progress updates
        timeout: Download timeout in seconds
        
    Raises:
        DownloadError: If download fails
    """
    print(f"Downloading {url}")
    
    # Ensure destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Get content length for progress tracking
    total_size = get_content_length(url) or 0
    tracker = ProgressTracker(total_size)
    
    try:
        with download_context(url, timeout) as response:
            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    tracker.update(len(chunk))
                    
                    if progress_callback:
                        progress_callback(tracker)
                    
                    # Simple progress output
                    if total_size > 0:
                        progress = tracker.get_progress()
                        speed = tracker.get_speed()
                        print(f"\r  Progress: {progress:.1f}% "
                              f"({format_size(tracker.downloaded)}/{format_size(total_size)}) "
                              f"at {format_speed(speed)}", end='', flush=True)
                
                print()  # New line after progress
                
    except Exception as e:
        # Clean up partial download
        if destination.exists():
            destination.unlink()
        raise DownloadError(f"Download failed: {str(e)}")


def download_with_retry(
    url: str,
    destination: Path,
    max_retries: int = MAX_RETRIES,
    **kwargs
) -> None:
    """
    Download file with retry logic.
    
    Args:
        url: URL to download
        destination: Destination file path
        max_retries: Maximum number of retry attempts
        **kwargs: Additional arguments for download_file
        
    Raises:
        DownloadError: If all retry attempts fail
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"Retrying download (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
            
            download_file(url, destination, **kwargs)
            return
            
        except DownloadError as e:
            last_error = e
            if attempt < max_retries:
                print(f"  Download failed: {e}. Retrying...")
            continue
    
    raise DownloadError(f"Download failed after {max_retries + 1} attempts: {last_error}")


def verify_checksum(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify file checksum.
    
    Args:
        file_path: Path to file to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        True if checksum matches
    """
    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        
        actual_hash = hasher.hexdigest()
        return actual_hash.lower() == expected_hash.lower()
        
    except Exception:
        return False


def fetch(
    url: str,
    destination: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    verify_hash: Optional[str] = None,
    hash_algorithm: str = "sha256",
    progress_callback: Optional[Callable[[ProgressTracker], None]] = None
) -> None:
    """
    High-level fetch function with all features.
    
    Args:
        url: URL to download
        destination: Destination file path
        chunk_size: Download chunk size
        verify_hash: Optional hash for verification
        hash_algorithm: Hash algorithm for verification
        progress_callback: Optional progress callback
        
    Raises:
        DownloadError: If download or verification fails
    """
    # Skip download if file already exists and hash matches
    if destination.exists() and verify_hash:
        if verify_checksum(destination, verify_hash, hash_algorithm):
            print(f"File already exists and verified: {destination}")
            return
    
    # Download with retry
    download_with_retry(
        url, destination, 
        chunk_size=chunk_size,
        progress_callback=progress_callback
    )
    
    # Verify checksum if provided
    if verify_hash:
        print("Verifying checksum...")
        if not verify_checksum(destination, verify_hash, hash_algorithm):
            destination.unlink()  # Remove corrupted file
            raise DownloadError("Checksum verification failed")
        print("Checksum verified")


# Tqdm integration for enhanced progress display
def create_tqdm_progress_callback():
    """
    Create a progress callback that uses tqdm for enhanced display.
    
    Returns:
        Progress callback function
    """
    try:
        import tqdm
        
        pbar = None
        
        def callback(tracker: ProgressTracker):
            nonlocal pbar
            
            if pbar is None:
                pbar = tqdm.tqdm(
                    total=tracker.total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc="Downloading"
                )
            
            # Update progress
            pbar.update(tracker.downloaded - pbar.n)
            
            # Update description with speed
            speed = tracker.get_speed()
            pbar.set_description(f"Downloading ({format_speed(speed)})")
            
            # Close when complete
            if tracker.downloaded >= tracker.total_size:
                pbar.close()
        
        return callback
        
    except ImportError:
        return None
