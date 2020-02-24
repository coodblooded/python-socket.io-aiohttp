import asyncio
import aiohttp_cors

from aiohttp import web
from sqlalchemy.sql.ddl import CreateTable
from database.db import *
import socketio
from aiopg.sa import create_engine
import json
import boto3
from datetime import datetime
from fastapi import FastAPI
from fastapi_mail import FastMail
from fastapi import File, Body,Query, UploadFile

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
routes = web.RouteTableDef()
client = boto3.client('route53', aws_access_key_id='*****', aws_secret_access_key='***')
app = web.Application()
sio.attach(app)
meta = sa.MetaData()

from templates import template

async def send_email(**kargs):
    to_email = kargs.get('to_email')
    login_url = kargs.get('login_url')
    tem = template.resister_html(login_url)
    mail = FastMail(email="patelharishankar126@gmail.com",password="******",tls=True,port="587",service="gmail")

    await  mail.send_message(recipient=to_email,subject="Test email from fastapi-mail", body=tem, text_format="html")
    

# async def startup():
#     await from aiopg.sa import create_engine

async def create_aiopg(app):
    app['pg_engine'] = await create_engine(
        user='**',
        database='vmitr',
        host='vmitr.***.ap-south-1.rds.amazonaws.com',
        port=5432,
        password='**'
    )

async def dispose_aiopg(app):
    app['pg_engine'].close()
    await app['pg_engine'].wait_closed()

app.on_startup.append(create_aiopg)
#app.on_cleanup.append(dispose_aiopg).connect()

@routes.post('/login')
async def login(request):
    data = await request.json()
    request_host = request.host.split(':')[0]
    return_data = {}
    org_obj = session.query(Organization).filter(Organization.org_url == request_host).first()
    user_obj = session.query(User).filter(User.email == data.get('email')).first()
    acco_obj = session.query(Association).filter(Association.org_id == org_obj.id, Association.user_id==user_obj.id).first()
    if user_obj:
        if user_obj.status != 'active':
            return_data['message'] = "Account is not active"
            return web.json_response(return_data,headers={
                            "Access-Control-Allow-Origin": "*"
                }, status=400)            
        if acco_obj.password == data.get('password') :
            return_data["login"] = True
            return_data['user_id'] = user_obj.id
            return_data['first_name'] = user_obj.first_name
            return_data['last_name'] = user_obj.last_name
            return_data['avt'] = user_obj.first_name[0] + user_obj.last_name[0]
            return_data['login_url'] = org_obj.org_url
            return_data['org_id'] = org_obj.id
            return_data['org_name'] = org_obj.name
            return web.json_response(return_data, headers={
                    "Access-Control-Allow-Origin": "*"
                })
    return_data['message'] = "Invalid information"
    return web.json_response(return_data,headers={
                    "Access-Control-Allow-Origin": "*"
                }, status=400)



@routes.get('/channel/{user}/{org}')
async def add_new_channel(request):
    user_id = request.match_info['user']
    org_id = request.match_info['org']
    org_obj = session.query(Channel).filter(Channel.org_id == org_id)
    data =[]
    for da in org_obj: 
        data.append(dict(text=da.name, id=da.id))

    return web.json_response(data,headers={
                    "Access-Control-Allow-Origin": "*"
                },status=200)

@routes.post('/channel_dlt')
async def delete_channel(request):
    data = await request.json()
    print("sandeep patelsdbscs")
    if data:
        chn_id = data.get('chn_id', None)
        chn_obj = session.query(Channel).filter(Channel.id==chn_id).delete()
        print(chn_obj)
        return web.json_response({'message':'Delete New'},headers={
                        "Access-Control-Allow-Origin": '*'
                    },status=203)
    return web.json_response({'message':'Invalid Data'},headers={
                        "Access-Control-Allow-Origin": '*'
                    },status=404)                    





@routes.post('/channel')
async def add_new_channel(request):
    data = await request.json()
    if data.get('name'):
        c_data = dict(name=data.get('name', ''), org_id=data.get('organization_id', ''), created_on=datetime.now(), updated_on=datetime.now())
        chnl_obj = Channel(**c_data)
        session.add(chnl_obj)
        session.commit()
        session.flush() 
        print("Ssss")
    return web.json_response({'message':'Create New'},headers={
                    "Access-Control-Allow-Origin": "*"
                },status=201)



@routes.post('/workspace')
async def workspace(request):
    data = await request.json()
    print(data)
    return_data = {}
    new_org_url =  data.get('domain', '') + '.vmitr.com'
    user_obj = session.query(Organization).filter(Organization.org_url == new_org_url).first()
    if user_obj:
        return_data["login_url"] = user_obj.org_url
        return_data["name"] = user_obj.name
        return web.json_response(return_data,headers={
                "Access-Control-Allow-Origin": "*"
            })
    return_data['message'] = "Invalid information"
    return web.json_response(return_data,headers={
                    "Access-Control-Allow-Origin": "*"
                }, status=400)


@routes.post('/get_details')
async def get_org_details(request):
    data = await request.json()
    print(data)
    return_data = {}
    new_org_url =  data.get('url', '') 
    user_obj = session.query(Organization).filter(Organization.org_url == new_org_url).first()
    if user_obj:
        return_data["login_url"] = user_obj.org_url
        return_data["name"] = user_obj.name
        return_data['org_id'] = user_obj.id
        return web.json_response(return_data,headers={
                "Access-Control-Allow-Origin": "*"
            })
    return_data['message'] = "Invalid information"
    return web.json_response(return_data,headers={
                    "Access-Control-Allow-Origin": "*"
                }, status=400)


@routes.post('/register')
async def register(request):
    data = await request.json()
    new_org_url = data.get('domain', '') + '.vmitr.com'
    org_obj =session.query(Organization).filter(Organization.org_url == new_org_url).first()
    if org_obj:
        return web.json_response({'message':"Domain Already Exist"},status=404 )

    response = client.change_resource_record_sets(
            HostedZoneId='Z3M44FTVRLT2IU',
            ChangeBatch={
                    'Comment':'cretae new',
                    'Changes':[
                            {
                            'Action':'UPSERT',
                            'ResourceRecordSet': {
                                    'Name': new_org_url,
                                    'Type':'A',
                                    'AliasTarget': {
                                                    'HostedZoneId': 'Z3M44FTVRLT2IU',
                                                    'DNSName': 'vmitr.com.',
                                                    'EvaluateTargetHealth': True|False
                                                },
                                    }
                            
                                    
                            }
                            ]
                    
                    }
            )        
    data_user = data
    data_user.pop('domain', '')
    data_user.pop('confirm_pass', '')
    data['created_on'] = datetime.now()
    neworg = Organization(**dict(org_url=new_org_url, name=data.get('name', ''), created_on = datetime.now()))
    data_user.pop('name', '')
    newuser = User(**dict(first_name=data.get('first_name', ''), last_name=data.get('last_name', ''), email= data.get('email', ''), created_on = datetime.now(), status='active'))
    session.add(newuser)
    session.add(neworg)
    session.commit()
    session.flush()  
    all_rela = Association(**dict(org_id=neworg.id, user_id=newuser.id, password=data.get('password')))
    session.add(all_rela)
    session.commit()
    login_url = new_org_url + '/Login'
    await send_email(**dict(to_email=data.get('email'), login_url=login_url))
    return web.Response(text="New User Create",
    headers={
            "Access-Control-Allow-Origin": "*"
        })

@routes.post('/invite')
async def invite_user(request):
    data = await request.json()
    message = 'Error'
    user_obj = session.query(User).filter(User.email == data.get('user_email')).first()
    print('')
    if user_obj:
        organization_obj = session.query(Association).filter(Association.org_id == data.get('organization_id'), Association.user_id == user_obj.id).first()
        if organization_obj:
            message = 'User Already in your workspace'
        else:
            add_org = Association(**dict(org_id= data.get('organization_id'), user_id=user_obj.id),password='123456', created_on=datetime.now(), updated_on=datetime.now(), status='pending')
            session.add(add_org)
            message = 'Added Successfilly and Send the Reqest user too'
    else:
        user_obj_new = User(email= data.get('user_email', ''), created_on = datetime.now())
        session.add(user_obj_new)
        session.commit()
        session.flush()
        add_org = Association(**dict(org_id= data.get('organization_id'), user_id=user_obj_new.id), password='123456',created_on=datetime.now(), updated_on=datetime.now(), status='pending')
        session.add(add_org)
        session.commit()


    print(data)
    return web.Response(text=message,
    headers={
            "Access-Control-Allow-Origin": "*"
        })
async def background_task():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        await sio.sleep(100)
        count += 1
        # await sio.emit('my_response', {'data': 'Server generated event'})


async def index(request):
    with open('app.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


@sio.event
async def my_event(sid, message):
    await sio.emit('my_response', {'data': message['data']}, room=sid)


@sio.event
async def my_broadcast_event(sid, message):
    await sio.emit('my_response', {'data': message['data']})


@sio.event
async def join(sid, message):
    sio.enter_room(sid, message['room'])
    # await sio.emit('my_response', {'data': 'Entered room: ' + message['room']},
    #                room=sid)


@sio.event
async def leave(sid, message):
    sio.leave_room(sid, message['room'])
    await sio.emit('my_response', {'data': 'Left room: ' + message['room']},
                   room=sid)

@sio.event
async def close_room(sid, message):
    await sio.emit('my_response',
                   {'data': 'Room ' + message['room'] + ' is closing.'},
                   room=message['room'])
    await sio.close_room(message['room'])


@sio.event
async def my_room_event(sid, message):
    print(message)
    if len(message['msg'])>1:
        await sio.emit('my_response', {'data': message},
                    room=message['room'])
    else:
        print("blank msg not allowed")

@sio.event
async def disconnect_request(sid):
    await sio.disconnect(sid)


@sio.event
async def connect(sid, environ):
    pass
    #await sio.emit('my_response', {'data': '', 'count': 0}, room=sid)


@sio.event
def disconnect(sid):
    print('Client disconnected')




# loop = asyncio.get_event_loop()
# loop.run_until_complete(startup())

app.router.add_static('/static', 'static')
app.router.add_get('/', index)

app.add_routes(routes)
app.add_routes([web.post('/channel_dlt', delete_channel)])
# cors.setup(app, default={
#         "*":
#             aiohttp_cors.ResourceOptions(allow_credentials=False)
#     })


if __name__ == '__main__':
    sio.start_background_task(background_task)
    web.run_app(app)
