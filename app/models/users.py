from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from app.models.financials import Base
import datetime

# Junction table for Role-User relationship
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    language = Column(String(10), default='ar') # 'ar' or 'en'
    is_active = Column(Integer, default=1)
    last_login = Column(DateTime)
    
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # 'Admin', 'Accountant', 'Cashier'
    description = Column(String(255))
    
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False) # 'INV_CREATE', 'REPORT_VIEW', 'SND_DELETE'
    description = Column(String(255))
