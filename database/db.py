import sqlalchemy as sa
from sqlalchemy.sql.ddl import CreateTable
from sqlalchemy_utils import ArrowType
from sqlalchemy_utils import PasswordType, force_auto_coercion
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine  
import asyncio
meta = sa.MetaData()
db_string = "postgres://postgres:8888@vmitr.8***8888.ap-south-1.rds.amazonaws.com/vmitr"

db = create_engine(db_string, pool_size=100, max_overflow=100)
meta = sa.MetaData(db)
Base = declarative_base(metadata=meta)
Session = sessionmaker(bind=db)
session = Session()

force_auto_coercion()

class Association(Base):
    __tablename__ = 'association'
    org_id = sa.Column(sa.Integer, sa.ForeignKey('organization.id'), primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
    extra_data = sa.Column(sa.String(50))
    user = relationship("User")
    #organization = relationship("Organization", back_populates="user_association")

class Organization(Base):
    __tablename__ = 'organization'
    id = sa.Column(sa.Integer, primary_key=True)
    org_url = sa.Column(sa.VARCHAR, nullable=False)
    name = sa.Column(sa.VARCHAR, nullable=True)
    org_type = sa.Column(sa.VARCHAR, nullable=True)
    created_on = sa.Column(sa.DateTime, nullable=True)
    updated_on = sa.Column(sa.DateTime, nullable=True)
    user = relationship("Association")
 

class Channel(Base):
    __tablename__ = 'channel'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.VARCHAR, nullable=True)
    created_on = sa.Column(sa.DateTime, nullable=True)
    organization_id = sa.Column(sa.Integer, sa.ForeignKey('organization.id'))
    organization = relationship("Organization", backref="channel")

class User(Base):
    __tablename__ = 'user'
    id = sa.Column(sa.Integer, primary_key=True)
    first_name = sa.Column(sa.VARCHAR, nullable=True)
    last_name = sa.Column(sa.VARCHAR, nullable=True)  
    email = sa.Column( sa.String(255), nullable=True)
    password = sa.Column(PasswordType(
                schemes=[
                    'pbkdf2_sha512',
                    'md5_crypt'
                ],

                deprecated=['md5_crypt']
            ),
            nullable=False
            )
       
    created_on = sa.Column(sa.DateTime, nullable=True)
    updated_on = sa.Column(sa.DateTime, nullable=True)




# with db.connect() as conn:
#     # Create
#     #Base.metadata.drop_all(bind=db)
#     Base.metadata.create_all(bind=db)

#     # ong_tbl = Organization()
#     # chl_tbl = Channel()
#     # usr_tbl = User()
#     # ong_tbl.create()
#     # chl_tbl.create()
#     # usr_tbl.create()
#     #from datetime import datetime
#     # o = Organization(name='dddd',org_url='ss.ve.com',created_on=datetime.now())
#     # secction.add(o)
#     # a = User(first_name='sjnja', email='sanj@dkkd.com', password='23456')
#     # secction.add(a)
#     #secction.commit()
#     #allq = secction.query(User).filter(User.id==8).first()
#     #print(allq.email)
#     # for i in allq:
#     #     print(i.password == '23456', i.email)
    


print("done")