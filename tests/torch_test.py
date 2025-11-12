print("Starting torch test...")
try:
    import torch
    print("Torch imported successfully")
    print("PyTorch version:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    print("Test completed")
except Exception as e:
    print("Error:", str(e))
    print("Error type:", type(e).__name__)
