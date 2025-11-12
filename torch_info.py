import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version in PyTorch: {torch.version.cuda}")
    print(f"cuDNN available: {torch.backends.cudnn.enabled}")
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA version in PyTorch: N/A")
    print("cuDNN available: N/A")
    print("GPU count: N/A")
    print("GPU name: N/A")
