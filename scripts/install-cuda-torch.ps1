# Install PyTorch with CUDA support
# This script must be run AFTER uv sync

Write-Host "Uninstalling CPU-only PyTorch..." -ForegroundColor Yellow
uv pip uninstall torch torchvision

Write-Host "`nInstalling CUDA-enabled PyTorch 2.6.0 with CUDA 12.4 support..." -ForegroundColor Cyan
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

Write-Host "`nVerifying CUDA installation..." -ForegroundColor Green
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

