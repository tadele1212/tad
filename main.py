from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import ServiceInput, NearestStopInput, StopResponse
from db import DatabaseConnection
from logger import logger
from middleware import error_handler

app = FastAPI()

# CORS configuration - must be first
origins = [
    "http://localhost:5173",    # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:4173",    # Vite preview
    "https://next-bus-stop.onrender.com"  # Production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add error handling middleware
app.middleware("http")(error_handler)

db = DatabaseConnection()

@app.options("/api/{path:path}")
async def options_route(path: str):
    return JSONResponse(
        status_code=200,
        content={"message": "OK"}
    )

@app.post("/api/show_stop", response_model=StopResponse)
async def show_stop(input_data: ServiceInput):
    logger.info(f"Fetching stops for service: {input_data.service_no}")
    try:
        with db.get_cursor() as cursor:
            logger.info("Calling stored procedure Show_Stop")
            cursor.callproc('Show_Stop', [input_data.service_no])
            
            results = next(cursor.stored_results())
            raw_data = results.fetchall()
            logger.info(f"Retrieved {len(raw_data)} bus stops")
            
            # Convert the data to match our model
            formatted_stops = []
            for stop in raw_data:
                formatted_stop = {
                    'Seq': stop['Seq'],
                    'Bus_Stop': stop['Bus Stop'],
                    'KM': float(stop['KM'])
                }
                formatted_stops.append(formatted_stop)
            
            return {"stops": formatted_stops}
    except Exception as e:
        logger.error(f"Error in show_stop endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@app.post("/api/nearest_stop")
async def nearest_stop(input_data: NearestStopInput):
    logger.info(f"Finding nearest stop for service: {input_data.service_no}")
    try:
        with db.get_cursor() as cursor:
            cursor.callproc('Nearest_stop', [
                input_data.service_no,
                input_data.gx,
                input_data.gy,
                input_data.last_stop
            ])
            results = next(cursor.stored_results())
            return results.fetchone()
    except Exception as e:
        logger.error(f"Error finding nearest stop: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        ) 

@app.get("/api/check_procedure")
async def check_procedure():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT ROUTINE_NAME, ROUTINE_TYPE 
                FROM INFORMATION_SCHEMA.ROUTINES 
                WHERE ROUTINE_SCHEMA = 'Bus' 
                AND ROUTINE_NAME = 'Show_Stop'
            """)
            result = cursor.fetchone()
            if result:
                return {"exists": True, "details": result}
            return {"exists": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/api/check_procedure_params")
async def check_procedure_params():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT PARAMETER_NAME, PARAMETER_MODE, DATA_TYPE
                FROM INFORMATION_SCHEMA.PARAMETERS
                WHERE SPECIFIC_SCHEMA = 'Bus'
                AND SPECIFIC_NAME = 'Show_Stop'
                ORDER BY ORDINAL_POSITION
            """)
            params = cursor.fetchall()
            return {"parameters": params}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/api/check_procedure_content")
async def check_procedure_content():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT ROUTINE_DEFINITION
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_SCHEMA = 'Bus'
                AND ROUTINE_NAME = 'Show_Stop'
            """)
            result = cursor.fetchone()
            return {"procedure_definition": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting procedure content: {str(e)}"
        ) 

@app.get("/api/check_data/{service_no}")
async def check_data(service_no: str):
    try:
        with db.get_cursor() as cursor:
            # Adjust table name based on your database schema
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM Bus.stops 
                WHERE service_no = %s
            """, (service_no,))
            result = cursor.fetchone()
            return {"record_count": result['count']}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking data: {str(e)}"
        ) 

@app.get("/api/check_tables")
async def check_tables():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'Bus'
            """)
            tables = cursor.fetchall()
            
            # Get sample data from each table
            table_data = {}
            for table in tables:
                table_name = table['TABLE_NAME']
                cursor.execute(f"SELECT * FROM Bus.{table_name} LIMIT 1")
                sample = cursor.fetchone()
                table_data[table_name] = {
                    "columns": [d[0] for d in cursor.description],
                    "sample": sample
                }
            
            return {
                "tables": tables,
                "table_details": table_data
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking tables: {str(e)}"
        ) 

@app.get("/api/check_permissions")
async def check_permissions():
    try:
        with db.get_cursor() as cursor:
            # Check current user
            cursor.execute("SELECT CURRENT_USER()")
            current_user = cursor.fetchone()

            # Check grants for current user
            cursor.execute("""
                SHOW GRANTS FOR CURRENT_USER()
            """)
            grants = cursor.fetchall()

            # Check specific procedure privileges
            cursor.execute("""
                SELECT * FROM information_schema.user_privileges 
                WHERE GRANTEE LIKE CONCAT("'", SUBSTRING_INDEX(CURRENT_USER(), '@', 1), "%")
            """)
            privileges = cursor.fetchall()

            # Check procedure specific privileges
            cursor.execute("""
                SELECT * FROM information_schema.routine_privileges 
                WHERE routine_schema = 'Bus' 
                AND routine_name = 'Show_Stop' 
                AND GRANTEE LIKE CONCAT("'", SUBSTRING_INDEX(CURRENT_USER(), '@', 1), "%")
            """)
            procedure_privileges = cursor.fetchall()

            return {
                "current_user": current_user,
                "grants": grants,
                "privileges": privileges,
                "procedure_privileges": procedure_privileges
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking permissions: {str(e)}"
        ) 