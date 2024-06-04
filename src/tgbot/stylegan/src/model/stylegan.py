import logging
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import pickle
import torch
import numpy as np
from PIL import Image


logger = logging.getLogger(__name__)


MODEL_PATH = './res'
MODEL_NAME = 'stylegan3-r-ffhq-1024x1024.pkl'
CLASS_LABEL = None


def generate_image(numpy_seed: np.ndarray) -> Image.Image:
    with open(os.path.join(MODEL_PATH, MODEL_NAME), 'rb') as f:
        loaded_model = pickle.load(f)['G_ema'].cuda()

    # SEED_SIZE = loaded_model.z_dim

    torch_seed = torch.from_numpy(numpy_seed).reshape(1, -1).cuda()

    # image_seed = torch.randn([1, loaded_model.z_dim]).cuda()

    # NCHW, float32, dynamic range [-1, +1], no truncation
    generated_image = loaded_model(torch_seed, CLASS_LABEL)
    generated_image_processed = np.moveaxis(generated_image.cpu().numpy(), 1, -1)
    generated_image_processed = 0.5 * generated_image_processed + 0.5


    return Image.fromarray((generated_image_processed[0] * 255).astype(np.uint8), 'RGB')