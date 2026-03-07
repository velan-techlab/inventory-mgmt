import logging
import logging.config

from fastapi import FastAPI
from database import engine, Base
from routers import stock

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
})

logger = logging.getLogger(__name__)

logger.info("Initializing database tables")
Base.metadata.create_all(bind=engine)
logger.info("Database tables ready")

app = FastAPI(
    title="Stock Service",
    description="Microservice for managing stock inventory",
    version="1.0.0",
)

app.include_router(stock.router)
logger.info("Stock router registered")


@app.get("/health")
def health_check():
    logger.debug("Health check requested")
    return {"status": "ok"}
