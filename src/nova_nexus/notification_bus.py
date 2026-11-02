"""Optional freedesktop notifications service. Never replaces an existing owner."""
import asyncio
import threading
from PySide6.QtCore import QObject, Signal


class NotificationBus(QObject):
    incoming=Signal(int,str,str,int,object)
    closing=Signal(int)
    status=Signal(str)

    def __init__(self,center):
        super().__init__(center)
        self.center=center;self.loop=None;self.bus=None;self.service=None
        self.counter=1
        self.incoming.connect(self.display)
        self.closing.connect(center.dismiss)

    def display(self,identifier,title,body,timeout,actions):
        callbacks=[]
        for key,label in actions:
            callbacks.append((label,lambda action=key:self.invoke(identifier,action)))
        self.center.notify(title,body,actions=callbacks,timeout=timeout,replace=identifier)

    def invoke(self,identifier,key):
        if self.loop and self.service:
            self.loop.call_soon_threadsafe(self.service.ActionInvoked,identifier,key)
        self.center.dismiss(identifier)

    def start(self):
        if self.loop:return
        def worker():
            loop=asyncio.new_event_loop();self.loop=loop
            try:loop.run_until_complete(self.serve())
            except Exception as error:self.status.emit(str(error))
            finally:
                if self.bus:self.bus.disconnect()
                self.loop=None
                loop.close()
        self.thread=threading.Thread(target=worker,daemon=True,name='nova-notification-bus');self.thread.start()

    async def serve(self):
        from dbus_next.aio import MessageBus
        from dbus_next.constants import NameFlag,RequestNameReply
        from dbus_next.service import ServiceInterface,method,signal
        owner=self
        class Service(ServiceInterface):
            def __init__(self):super().__init__('org.freedesktop.Notifications')
            @method()
            def GetCapabilities(self)->'as':return ['actions','body','persistence']
            @method()
            def GetServerInformation(self)->'ssss':return ['NOVA NEXUS HD','NovaBar','1.0.0','1.2']
            @method()
            def Notify(self,app_name:'s',replaces_id:'u',app_icon:'s',summary:'s',body:'s',actions:'as',hints:'a{sv}',expire_timeout:'i')->'u':
                identifier=replaces_id or owner.counter
                owner.counter=max(owner.counter,identifier+1)
                owner.incoming.emit(identifier,summary,body,expire_timeout,list(zip(actions[::2],actions[1::2])))
                return identifier
            @method()
            def CloseNotification(self,id:'u'):
                owner.closing.emit(id);self.NotificationClosed(id,3)
            @signal()
            def NotificationClosed(self,id,reason)->'uu':return [id,reason]
            @signal()
            def ActionInvoked(self,id,key)->'us':return [id,key]
        self.bus=await MessageBus().connect()
        reply=await self.bus.request_name('org.freedesktop.Notifications',NameFlag.DO_NOT_QUEUE)
        if reply!=RequestNameReply.PRIMARY_OWNER:
            raise RuntimeError('Le service système de notifications est déjà actif. Il reste inchangé.')
        self.service=Service()
        self.bus.export('/org/freedesktop/Notifications',self.service)
        self.status.emit('Service D-Bus NOVA activé pour cette session')
        await self.bus.wait_for_disconnect()

    def stop(self):
        if self.loop and self.bus:self.loop.call_soon_threadsafe(self.bus.disconnect)
