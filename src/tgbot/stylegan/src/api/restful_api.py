import logging
import uvicorn
import io
import numpy as np
import random
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from enum import Enum
from PIL import Image
from src.model import stylegan


logger = logging.getLogger(__name__)


class StatusEnum(Enum):
    success = 'success'
    error = 'error'


# class PatternAlgo(BaseModel):
#     status: StatusEnum
#     data: object | None = None
#     details: str | None = None


app = FastAPI(
    title='StyleGAN API 1.0'
)


@app.post('/generate/')
async def get_portfolio(seed: UploadFile = File(...)):
    """Generate image from seed using NVIDIA StyleGAN3."""
    try:
        content = await seed.read()
        seed_array = np.frombuffer(content, dtype=np.float32)
        image = stylegan.generate_image(seed_array)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type='image/png')
    
    except Exception as e:
        logger.exception('API error in get_data() method!')
        raise HTTPException(status_code=500, detail={
            'status': 'error',
            'data': None,
            'details': str(e)
        })


def fastapi_run():
    """Run FastAPI."""
    uvicorn.run(app, host='0.0.0.0', port=8000)
