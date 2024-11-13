from asyncio.log import logger
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends, status, Response, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import requests
import os
from serpapi import GoogleSearch
from services import GenerateLeadsService
from jose import JWTError, jwt
from models import User, UserCreate, Token
from services import (
    verify_password,
    get_password_hash,
    create_access_token,
    OAuth2PasswordBearerCookie
)
from typing import Optional
from dotenv import load_dotenv

app = FastAPI(title="Lead Generation API", description="API to generate leads by location and industry", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="token", cookie_name="access_token")

app.mount("/static", StaticFiles(directory="static"), name="static")

load_dotenv()

SECRET_KEY = "9a8b7c6d5e4f3g2h1i0j0k9l8m7n6o5p4q3r2s1t"
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in environment variables.")


fake_db = {
    "admin": {
        "id": 1,  # Added ID field
        "username": "admin",
        "hashed_password": get_password_hash("password123")
    }
}

def authenticate_user(username: str, password: str):
    user = fake_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return User(**user)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_db.get(username)
    if user is None:
        raise credentials_exception
    return User(**user)

@app.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # Set the JWT token in an HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,      # Set to True in production with HTTPS
        path="/",
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/")
async def create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    if user.username in fake_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = get_password_hash(user.password)
    fake_db[user.username] = {"username": user.username, "hashed_password": hashed_password}
    return {"msg": "User created successfully"}

@app.put("/users/{username}")
async def update_user(username: str, user: UserCreate, current_user: User = Depends(get_current_user)):
    existing_user = fake_db.get(username)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    hashed_password = get_password_hash(user.password)
    fake_db[username] = {"username": user.username, "hashed_password": hashed_password}
    return {"msg": "User updated successfully"}

class LocationData(BaseModel):
    location: str
    industry: str
    min_results: int = 50

@app.post("/generate-leads/", response_class=FileResponse)
async def generate_leads(location_data: LocationData):
    try:
        service = GenerateLeadsService(location_data.location, location_data.industry, location_data.min_results)
        await service.init_db_pool()
        file_path = await service.run()
        await service.close_db_pool()
        if not file_path:
            raise HTTPException(status_code=404, detail="Leads not found for the given parameters.")
        return FileResponse(path=file_path, filename=file_path, media_type='application/octet-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/dashboard/", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
async def read_dashboard():
    """
    Serves the dashboard.html page. Protected by authentication.
    """
    with open("static/dashboard.html") as f:
        content = f.read()
    return HTMLResponse(content=content, status_code=200)
    
@app.get("/proxy-locations/", dependencies=[Depends(get_current_user)])
async def proxy_locations(q: str):
    try:
        response = requests.get(f"https://serpapi.com/locations.json?q={q}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/results-data/", response_class=JSONResponse, dependencies=[Depends(get_current_user)])
async def get_results_data():
    service = GenerateLeadsService(
        None, None, None
    )
    await service.init_db_pool()
    try:
        results = await service.fetch_all_results()
        encoded_results = jsonable_encoder(results)  # Convert datetime to str
        return JSONResponse(content=encoded_results)
    finally:
        await service.close_db_pool()

@app.post("/logout", dependencies=[Depends(get_current_user)])
async def logout(response: Response, request: Request):
    """
    Logs out the current user by deleting the access_token cookie.
    Implements checks to verify if the cookie exists before deletion and logs all actions.
    """
    try:
        # Retrieve the access_token from cookies
        access_token = request.cookies.get("access_token")
        
        if access_token:
            logger.info(f"Logout initiated for user with access_token: {access_token}")
        else:
            logger.warning("Logout attempted, but no access_token cookie was found.")

        # Attempt to delete the access_token cookie
        response.delete_cookie(
            key="access_token",
            path="/",
            httponly=True,
            secure=False,     # Must match the 'secure' value used in set_cookie
            samesite="lax"    # Must match the 'samesite' value used in set_cookie   
        )
        logger.info("access_token cookie deletion attempted.")

        # Since the cookie deletion is handled via Set-Cookie header,
        # we can't verify its removal on the server side immediately.
        # The client is responsible for deleting the cookie upon receiving the response.

        return JSONResponse(content={"msg": "Successfully logged out"})
    
    except Exception as e:
        logger.error(f"An error occurred during logout: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)