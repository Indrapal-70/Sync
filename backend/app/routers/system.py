from fastapi import APIRouter
import psutil

router = APIRouter(prefix="/api/system", tags=["System"])

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except ImportError:
    HAS_NVML = False
except Exception:
    HAS_NVML = False

@router.get("/metrics")
def get_system_metrics():
    """
    Returns system metrics like CPU usage, RAM usage, and optionally GPU metrics.
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    
    metrics = {
        "cpu": {
            "percent": cpu_percent
        },
        "ram": {
            "total_gb": round(ram.total / 1e9, 2),
            "used_gb": round(ram.used / 1e9, 2),
            "percent": ram.percent
        }
    }
    
    if HAS_NVML:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            metrics["gpu"] = {
                "name": pynvml.nvmlDeviceGetName(handle),
                "total_gb": round(mem.total / 1e9, 2),
                "used_gb": round(mem.used / 1e9, 2),
                "percent": util.gpu
            }
        except Exception:
            metrics["gpu"] = None
    else:
        metrics["gpu"] = None

    return metrics
