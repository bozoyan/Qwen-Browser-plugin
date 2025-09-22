import os

here = os.path.dirname(os.path.abspath(__file__))

# 配置上传文件夹和允许的文件扩展名
UPLOAD_FOLDER = os.path.join(here, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB上传限制

# 在这里配置您的API Key和Cookie
OPENAI_API_KEY = ""
MODEL_SCOPE_COOKIE = ""

# 图像生成默认参数
DEFAULT_WIDTH = 928
DEFAULT_HEIGHT = 1664

# GUA V1 - modelVersionId: 332699
# GUA V2 - modelVersionId: 334516
# GUA V8 - modelVersionId: 346999
# GUA V9 - modelVersionId: 365553
# Q_FEI_ckpt-12         310150
# Q_FEIFEI_ckpt-10      313167

LORA_ARGS = [
    # {'modelVersionId': 310150, 'scale': 1},
    {'modelVersionId': 313167, 'scale': 1}
]
