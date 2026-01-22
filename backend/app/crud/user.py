from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, full_name: str | None, email: str, password_hash: str, role: str = "user") -> User:
    user = User(full_name=full_name, email=email,
                password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
