from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from mysql.connector import Error as MySQLError
from logger import logger

async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except MySQLError as e:
        logger.error(f"Database error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"detail": "Database service unavailable"}
        )
    except HTTPException as e:
        logger.error(f"HTTP error {e.status_code}: {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        ) 