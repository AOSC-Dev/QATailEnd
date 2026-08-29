from omegaconf import OmegaConf
import os

config = None

if os.path.exists("application.yaml"):
    config = OmegaConf.load("application.yaml")
elif os.path.exists("config/application.yaml"):
    config = OmegaConf.load("config/application.yaml")
else:
    raise FileNotFoundError("application.yaml not found")

__all__ = ["config"]