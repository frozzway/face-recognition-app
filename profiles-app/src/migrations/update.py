from alembic.config import Config
from alembic import command
import time

time.sleep(3)
alembic_cfg = Config('alembic.ini')
command.upgrade(alembic_cfg, "head")