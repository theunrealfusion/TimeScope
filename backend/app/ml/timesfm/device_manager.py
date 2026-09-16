"""GPU/CPU device management with memory safety for 4GB VRAM."""
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    AUTO = "auto"
    CUDA = "cuda"
    CPU = "cpu"


@dataclass
class DeviceInfo:
    device: str                  # "cuda:0" or "cpu"
    device_type: str             # "cuda" or "cpu"
    gpu_name: str | None = None
    total_vram_mb: int | None = None
    free_vram_mb: int | None = None
    cuda_available: bool = False
    cuda_version: str | None = None


class DeviceManager:
    """Manages device selection with memory-aware CUDA fallback.

    Conservative for 4GB VRAM (GTX 1650):
    - Reserves ~500MB for system/display
    - Checks free memory before allocating
    - Falls back to CPU gracefully
    """

    def __init__(self, preferred: DeviceType = DeviceType.AUTO,
                 memory_threshold_mb: int = 3500):
        self.preferred = preferred
        self.memory_threshold_mb = memory_threshold_mb

    def select_device(self) -> DeviceInfo:
        """Select the best available device."""
        if self.preferred == DeviceType.CPU:
            return DeviceInfo(device="cpu", device_type="cpu")

        cuda_available = self._check_cuda()

        if not cuda_available:
            if self.preferred == DeviceType.CUDA:
                logger.warning(
                    "CUDA requested but not available. Falling back to CPU."
                )
            return DeviceInfo(device="cpu", device_type="cpu")

        # CUDA is available — check memory
        info = self._get_gpu_info()

        if info.free_vram_mb and info.free_vram_mb < self.memory_threshold_mb:
            logger.warning(
                f"Insufficient GPU memory: {info.free_vram_mb}MB free, "
                f"need {self.memory_threshold_mb}MB. Using CPU."
            )
            if self.preferred == DeviceType.CUDA:
                logger.error(
                    "CUDA explicitly requested but insufficient VRAM. "
                    "Proceeding with CUDA anyway — OOM may occur."
                )
                return info
            return DeviceInfo(device="cpu", device_type="cpu")

        logger.info(
            f"Using CUDA device: {info.gpu_name} "
            f"({info.free_vram_mb}MB free)"
        )
        return info

    def _check_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _get_gpu_info(self) -> DeviceInfo:
        try:
            import torch
            if not torch.cuda.is_available():
                return DeviceInfo(device="cpu", device_type="cpu")

            gpu_name = torch.cuda.get_device_name(0)
            total = torch.cuda.get_device_properties(0).total_mem // (1024**2)
            free = (total - torch.cuda.memory_allocated(0) // (1024**2))

            return DeviceInfo(
                device="cuda:0",
                device_type="cuda",
                gpu_name=gpu_name,
                total_vram_mb=total,
                free_vram_mb=free,
                cuda_available=True,
                cuda_version=torch.version.cuda,
            )
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return DeviceInfo(device="cpu", device_type="cpu")
