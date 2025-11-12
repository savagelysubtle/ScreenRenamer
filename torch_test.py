print("Starting torch test...")
try:
    import torch

    print("Torch imported successfully")
    print("PyTorch version:", torch.__version__)

    # Check CUDA availability safely
    try:
        cuda_available = torch.cuda.is_available()
        print("CUDA available:", cuda_available)
    except AttributeError:
        print("CUDA available: False (CUDA support not available in this PyTorch installation)")
    print("Test completed")
except Exception as e:
    print("Error:", str(e))
    print("Error type:", type(e).__name__)
