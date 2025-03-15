from CollideObjectBase import SphereCollidableObject
from panda3d.core import Loader, NodePath, Vec3
from direct.task.Task import TaskManager
from typing import Callable
from direct.task import Task
from SpaceJamClasses import Missile
from direct.gui.OnscreenImage import OnscreenImage

global base

class Spaceship(SphereCollidableObject):
    def __init__(self, loader: Loader, taskMgr: TaskManager, accept: Callable[[str, Callable], None], modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Spaceship, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1)
        self.taskMgr = taskMgr
        self.accept = accept
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.reloadTime = .25
        self.missileDistance = 4000
        self.missileBay = 1
        self.taskMgr.add(self.CheckIntervals, 'checkMissiles', 34)

        self.SetKeyBindings()
        self.EnableHUD()

    def SetKeyBindings(self):
        self.accept('space', self.Thrust, [1])
        self.accept('space-up', self.Thrust, [0])
        self.accept('arrow_left', self.LeftTurn, [1])
        self.accept('arrow_left-up', self.LeftTurn, [0])
        self.accept('arrow_right', self.RightTurn, [1])
        self.accept('arrow_right-up', self.RightTurn, [0])
        self.accept('arrow_up', self.UpTurn, [1])
        self.accept('arrow_up-up', self.UpTurn, [0])
        self.accept('arrow_down', self.DownTurn, [1])
        self.accept('arrow_down-up', self.DownTurn, [0])
        self.accept('e', self.RightRotate, [1])
        self.accept('e-up', self.RightRotate, [0])
        self.accept('q', self.LeftRotate, [1])
        self.accept('q-up', self.LeftRotate, [0])
        self.accept('f', self.Fire)

    def Thrust(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyThrust, 'forward-thrust')
        else:
            self.taskMgr.remove('forward-thrust')

    def ApplyThrust(self, task):
        rate = 5
        trajectory = base.render.getRelativeVector(self.modelNode, Vec3.forward())
        trajectory.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * rate)
        return Task.cont

    def Fire(self):
        if self.missileBay:
            travRate = self.missileDistance
            aim = base.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            fireSolution = aim * travRate
            inFront = aim * 150
            travVec = fireSolution + self.modelNode.getPos()
            self.missileBay -= 1
            tag = 'Missile' + str(Missile.missileCount)
            posVec = self.modelNode.getPos() + inFront
            currentMissile = Missile(base.loader, './Assets/Phaser/phaser.egg', base.render, tag, posVec, 4.0)
            Missile.Intervals[tag] = currentMissile.modelNode.posInterval(2.0, travVec, startPos = posVec, fluid = 1)
            Missile.Intervals[tag].start()
        else:
            if not self.taskMgr.hasTaskNamed('reload'):
                print('Initializing reload...')
                self.taskMgr.doMethodLater(0, self.Reload, 'reload')
                return Task.cont

    def EnableHUD(self):
            self.Hud = OnscreenImage(image = './Assets/Hud/Reticle3b.png', pos = Vec3(0, 0, 0,), scale = 0.1)
            self.Hud.setTransparency(True)
            
    def Reload(self, task):
        if task.time > self.reloadTime:
            self.missileBay += 1
            print("Reload complete.")
        if self.missileBay > 1:
            self.missileBay = 1
            return Task.done
        elif task.time <= self.reloadTime:
            print ("Reload proceeding...")
            return Task.cont
            
    def CheckIntervals(self, task):
        for i in Missile.Intervals:
            if not Missile.Intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()
                del Missile.Intervals[i]
                del Missile.fireModels[i]
                del Missile.cNodes[i]
                del Missile.collisionSolids[i]
                print (i + ' has reached the end of its fire solution.')
                break
        return Task.cont

    def LeftTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftTurn, 'left-turn')

        else:
            self.taskMgr.remove('left-turn')

    def ApplyLeftTurn(self, task):
        rate = .5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def RightTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightTurn, 'right-turn')

        else:
            self.taskMgr.remove('right-turn')

    def ApplyRightTurn(self, task):
        rate = -.5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def UpTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyUpTurn, 'up-turn')

        else:
            self.taskMgr.remove('up-turn')

    def ApplyUpTurn(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return Task.cont

    def DownTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyDownTurn, 'down-turn')

        else:
            self.taskMgr.remove('down-turn')

    def ApplyDownTurn(self, task):
        rate = -.5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return Task.cont
    
    def RightRotate(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightRotate, 'right-rotate')

        else:
            self.taskMgr.remove('right-rotate')

    def ApplyRightRotate(self, task):
        rate = .5
        self.modelNode.setR(self.modelNode.getR() + rate)
        return Task.cont

    def LeftRotate(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyLeftRotate, 'left-rotate')

        else:
            self.taskMgr.remove('left-rotate')

    def ApplyLeftRotate(self, task):
        rate = -.5
        self.modelNode.setR(self.modelNode.getR() + rate)
        return Task.cont