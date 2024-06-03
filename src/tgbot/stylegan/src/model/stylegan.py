import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import pickle
import torch
import numpy as np
from PIL import Image


MODEL_PATH = './res'
MODEL_NAME = 'stylegan3-r-ffhq-1024x1024.pkl'
CLASS_LABEL = None


def generate_image(seed) -> Image.Image:
    with open(os.path.join(MODEL_PATH, MODEL_NAME), 'rb') as f:
        loaded_model = pickle.load(f)['G_ema'].cuda()

    SEED_SIZE = loaded_model.z_dim

    image_seed = torch.randn([1, loaded_model.z_dim]).cuda()

    # NCHW, float32, dynamic range [-1, +1], no truncation
    generated_image = loaded_model(image_seed, CLASS_LABEL)
    generated_image_processed = np.moveaxis(generated_image.cpu().numpy(), 1, -1)
    generated_image_processed = 0.5 * generated_image_processed + 0.5


    return Image.fromarray(generated_image_processed[0], 'RGB')