from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import User
from security import hash_password
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from routers import auth, products, cart

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="O_Shop API",
    description="Online Shop Backend — Product Catalog, Auth, Cart",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)


@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not existing:
            admin = User(
                username=ADMIN_USERNAME,
                email=f"{ADMIN_USERNAME}@oshop.local",
                password_hash=hash_password(ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
