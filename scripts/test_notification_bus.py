"""Run under dbus-run-session; uses an isolated bus without replacing XFCE."""
import asyncio
import os
import tempfile
import time
from PySide6.QtWidgets import QApplication
from nova_nexus.notification_center import NotificationCenter
from nova_nexus.notification_bus import NotificationBus
from dbus_next.aio import MessageBus
from dbus_next import Message


async def request():
    bus=await MessageBus().connect()
    try:
        reply=await bus.call(Message(destination='org.freedesktop.Notifications',
            path='/org/freedesktop/Notifications',interface='org.freedesktop.Notifications',
            member='Notify',signature='susssasa{sv}i',body=['QA',0,'','NOVA bus test','Integration message',[],{},0]))
        assert reply.body and type(reply.body[0]) is int,reply
    finally:bus.disconnect()


def main():
    app=QApplication([])
    with tempfile.TemporaryDirectory() as tmp:
        os.environ['HEALTHBAR_DATA_DIR']=tmp
        center=NotificationCenter();center.set_quiet(True)
        service=NotificationBus(center);statuses=[];service.status.connect(statuses.append);service.start()
        end=time.monotonic()+5
        while not statuses and time.monotonic()<end:app.processEvents();time.sleep(.02)
        assert statuses and 'activé' in statuses[-1],statuses
        asyncio.run(request());app.processEvents()
        assert center.history[-1]['title']=='NOVA bus test'
        rival=NotificationBus(center);messages=[];rival.status.connect(messages.append);rival.start()
        end=time.monotonic()+5
        while not messages and time.monotonic()<end:app.processEvents();time.sleep(.02)
        assert messages and 'déjà actif' in messages[-1],messages
        service.stop();service.thread.join(timeout=5)
    print('NOVA_NOTIFICATION_BUS_OK')


if __name__=='__main__':main()
