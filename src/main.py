from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/untitled_api_db"
)

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WineRegion(Base):
    __tablename__ = "wine_regions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    country = Column(String(100), nullable=False)
    description = Column(Text)
    climate = Column(String(100))
    soil_type = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Wine(Base):
    __tablename__ = "wines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    vintage = Column(Integer, nullable=False)
    region_id = Column(UUID(as_uuid=True), ForeignKey("wine_regions.id"), nullable=False)
    grape_variety = Column(String(255))
    winery = Column(String(255))
    alcohol_percentage = Column(Float)
    price = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    region = relationship("WineRegion")

class UserWine(Base):
    __tablename__ = "user_wines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    wine_id = Column(UUID(as_uuid=True), ForeignKey("wines.id"), nullable=False)
    quantity = Column(Integer, default=1)
    purchase_date = Column(DateTime)
    purchase_price = Column(Float)
    storage_location = Column(String(255))
    notes = Column(Text)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    wine = relationship("Wine")

class WineTasting(Base):
    __tablename__ = "wine_tastings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    wine_id = Column(UUID(as_uuid=True), ForeignKey("wines.id"), nullable=False)
    tasting_date = Column(DateTime, nullable=False)
    rating = Column(Integer)
    notes = Column(Text)
    aroma_notes = Column(Text)
    taste_notes = Column(Text)
    finish_notes = Column(Text)
    overall_impression = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    wine = relationship("Wine")

# Pydantic models for API
class WineRegionCreate(BaseModel):
    name: str
    country: str
    description: Optional[str] = None
    climate: Optional[str] = None
    soil_type: Optional[str] = None

class WineRegionResponse(BaseModel):
    id: str
    name: str
    country: str
    description: Optional[str]
    climate: Optional[str]
    soil_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WineCreate(BaseModel):
    name: str
    vintage: int
    region_id: str
    grape_variety: Optional[str] = None
    winery: Optional[str] = None
    alcohol_percentage: Optional[float] = None
    price: Optional[float] = None
    description: Optional[str] = None

class WineResponse(BaseModel):
    id: str
    name: str
    vintage: int
    region_id: str
    grape_variety: Optional[str]
    winery: Optional[str]
    alcohol_percentage: Optional[float]
    price: Optional[float]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    region: WineRegionResponse
    
    class Config:
        from_attributes = True

class UserWineCreate(BaseModel):
    user_id: str
    wine_id: str
    quantity: int = 1
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    storage_location: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)

class UserWineResponse(BaseModel):
    id: str
    user_id: str
    wine_id: str
    quantity: int
    purchase_date: Optional[datetime]
    purchase_price: Optional[float]
    storage_location: Optional[str]
    notes: Optional[str]
    rating: Optional[int]
    created_at: datetime
    updated_at: datetime
    wine: WineResponse
    
    class Config:
        from_attributes = True

class WineTastingCreate(BaseModel):
    user_id: str
    wine_id: str
    tasting_date: datetime
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    aroma_notes: Optional[str] = None
    taste_notes: Optional[str] = None
    finish_notes: Optional[str] = None
    overall_impression: Optional[str] = None

class WineTastingResponse(BaseModel):
    id: str
    user_id: str
    wine_id: str
    tasting_date: datetime
    rating: Optional[int]
    notes: Optional[str]
    aroma_notes: Optional[str]
    taste_notes: Optional[str]
    finish_notes: Optional[str]
    overall_impression: Optional[str]
    created_at: datetime
    updated_at: datetime
    wine: WineResponse
    
    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(
    title="Wine Management API",
    description="API for managing wine collections, tastings, and regions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Wine Management API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Wine Regions endpoints
@app.get("/regions", response_model=List[WineRegionResponse])
async def get_regions(db: Session = Depends(get_db)):
    regions = db.query(WineRegion).all()
    return regions

@app.get("/regions/{region_id}", response_model=WineRegionResponse)
async def get_region(region_id: str, db: Session = Depends(get_db)):
    region = db.query(WineRegion).filter(WineRegion.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region

@app.post("/regions", response_model=WineRegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(region: WineRegionCreate, db: Session = Depends(get_db)):
    db_region = WineRegion(**region.dict())
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region

# Wines endpoints
@app.get("/wines", response_model=List[WineResponse])
async def get_wines(
    skip: int = 0, 
    limit: int = 100, 
    region_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Wine)
    if region_id:
        query = query.filter(Wine.region_id == region_id)
    wines = query.offset(skip).limit(limit).all()
    return wines

@app.get("/wines/{wine_id}", response_model=WineResponse)
async def get_wine(wine_id: str, db: Session = Depends(get_db)):
    wine = db.query(Wine).filter(Wine.id == wine_id).first()
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine

@app.post("/wines", response_model=WineResponse, status_code=status.HTTP_201_CREATED)
async def create_wine(wine: WineCreate, db: Session = Depends(get_db)):
    db_wine = Wine(**wine.dict())
    db.add(db_wine)
    db.commit()
    db.refresh(db_wine)
    return db_wine

# User Wines endpoints
@app.get("/users/{user_id}/wines", response_model=List[UserWineResponse])
async def get_user_wines(user_id: str, db: Session = Depends(get_db)):
    user_wines = db.query(UserWine).filter(UserWine.user_id == user_id).all()
    return user_wines

@app.post("/users/{user_id}/wines", response_model=UserWineResponse, status_code=status.HTTP_201_CREATED)
async def add_user_wine(user_id: str, user_wine: UserWineCreate, db: Session = Depends(get_db)):
    user_wine_data = user_wine.dict()
    user_wine_data["user_id"] = user_id
    db_user_wine = UserWine(**user_wine_data)
    db.add(db_user_wine)
    db.commit()
    db.refresh(db_user_wine)
    return db_user_wine

# Wine Tastings endpoints
@app.get("/users/{user_id}/tastings", response_model=List[WineTastingResponse])
async def get_user_tastings(user_id: str, db: Session = Depends(get_db)):
    tastings = db.query(WineTasting).filter(WineTasting.user_id == user_id).all()
    return tastings

@app.post("/users/{user_id}/tastings", response_model=WineTastingResponse, status_code=status.HTTP_201_CREATED)
async def create_tasting(user_id: str, tasting: WineTastingCreate, db: Session = Depends(get_db)):
    tasting_data = tasting.dict()
    tasting_data["user_id"] = user_id
    db_tasting = WineTasting(**tasting_data)
    db.add(db_tasting)
    db.commit()
    db.refresh(db_tasting)
    return db_tasting

# Search endpoints
@app.get("/search/wines")
async def search_wines(
    name: Optional[str] = None,
    vintage: Optional[int] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Wine).join(WineRegion)
    
    if name:
        query = query.filter(Wine.name.ilike(f"%{name}%"))
    if vintage:
        query = query.filter(Wine.vintage == vintage)
    if region:
        query = query.filter(WineRegion.name.ilike(f"%{region}%"))
    
    wines = query.all()
    return wines

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)