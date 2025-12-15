import logging
import uvicorn
import io
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from src.model import stylegan


logger = logging.getLogger(__name__)


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
