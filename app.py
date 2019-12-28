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

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
routes = web.RouteTableDef()
client = boto3.client('route53', aws_access_key_id='******', aws_secret_access_key='&*((&*((&*))))')
app = web.Application()
sio.attach(app)
meta = sa.MetaData()





# async def startup():
#     await database.connect()

@routes.post('/login')
async def login(request):
    data = await request.json()
    print(data)
    return_data = {}
    user_obj = session.query(User).filter(User.email == data.get('email')).first()
    if user_obj:
        if user_obj.password == data.get('password') :
            return_data["login"] = True
            return_data['user_id'] = user_obj.id
            return_data['first_name'] = user_obj.first_name
            return_data['last_name'] = user_obj.last_name
            return_data['avt'] = user_obj.first_name[0] + user_obj.last_name[0]
            return web.json_response(return_data,headers={
                    "Access-Control-Allow-Origin": "*"
                })
    return_data['message'] = "Invalid information"
    return web.json_response(return_data,headers={
                    "Access-Control-Allow-Origin": "*"
                }, status=400)


@routes.post('/workspace')
async def workspace(request):
    data = await request.json()
    print(data)
    return_data = {}
    new_org_url =  data.get('domain', '') + '.vmitr.com'
    user_obj = session.query(Organization).filter(Organization.org_url == new_org_url).first()
    if user_obj:
        return_data["login_url"] = user_obj.org_url
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
    print(data)
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
                                                    'DNSName': 'tt.vmitr.com.',
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
    newuser = User(**data)
    neworg = Organization(**dict(org_url=new_org_url, name='', org_type='', created_on = datetime.now()))
    session.add(newuser)
    session.add(neworg)
    session.commit()
    session.flush()  
    all_rela = Association(**dict(org_id=neworg.id, user_id=newuser.id))
    session.add(all_rela)
    session.commit()
    print(newuser.id,neworg.id)
    return web.Response(text="Nuew User Create",
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
# cors.setup(app, default={
#         "*":
#             aiohttp_cors.ResourceOptions(allow_credentials=False)
#     })


if __name__ == '__main__':
    sio.start_background_task(background_task)
    web.run_app(app)
