from CollideObjectBase import SphereCollidableObject
from panda3d.core import Loader, NodePath, Vec3, CollisionHandlerEvent, CollisionTraverser
from direct.task.Task import TaskManager
from typing import Callable
from direct.task import Task
from direct.interval.LerpInterval import LerpFunc
from direct.particles.ParticleEffect import ParticleEffect
from SpaceJamClasses import Missile
from direct.gui.OnscreenImage import OnscreenImage
import re


global base

class Spaceship(SphereCollidableObject):
    def __init__(self, loader: Loader, taskMgr: TaskManager, accept: Callable[[str, Callable], None], modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float):
        super(Spaceship, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1)
        self.taskMgr = taskMgr
        self.accept = accept
        self.traverser = CollisionTraverser()
        base.cTrav = self.traverser
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.reloadTime = .25
        self.missileDistance = 4000
        self.missileBay = 1
        self.taskMgr.add(self.CheckIntervals, 'checkMissiles', 34)
        self.cntExplode = 0
        self.explodeIntervals = {}
        self.handler = CollisionHandlerEvent()
        self.handler.addInPattern('into')
        self.accept('into', self.HandleInto)


        self.SetKeyBindings()
        self.EnableHUD()
        self.SetParticles()

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
        self.accept('d', self.DetonateMissile)

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
            self.traverser.addCollider(currentMissile.collisionNode, self.handler)
            self.lastMissile = currentMissile
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
        
    def DetonateMissile(self):
        if hasattr(self, 'lastMissile') and self.lastMissile:
          missilePos = self.lastMissile.modelNode.getPos()
          print("Missile detonated at ", missilePos)
          self.explodeNode.setPos(missilePos)
          self.Explode()
          self.DestroyObject(self.lastMissile.modelNode.getName(), missilePos)
          self.lastMissile = None
        else:
         print("No missile to detonate!")
            
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


    def SetParticles(self):
        base.enableParticles()
        self.explodeEffect = ParticleEffect()
        self.explodeEffect.loadConfig("./Assets/ParticleEffects/Explosions/basic_xpld_efx.ptf")
        self.explodeEffect.setScale(20)
        self.explodeNode = base.render.attachNewNode('ExplosionEffects')

    def HandleInto(self, entry):
        fromNode = entry.getFromNodePath().getName().replace('_cNode', '')  
        print("fromNode: " + fromNode)
        intoNode = entry.getIntoNodePath().getName().replace('_cNode', '')
        print("intoNode: " + intoNode)  
        intoPosition = Vec3(entry.getSurfacePoint(base.render))

        tempVar = fromNode.split('_')
        print("tempVar: " + str(tempVar))
        shooter = tempVar[0]
        print("Shooter: " + str(shooter))
        tempVar = intoNode.split('-')
        print("TempVar1: " + str(tempVar))
        tempvar = intoNode.split('-')
        print("TempVar2: " + str(tempVar))
        victim = tempVar[0]
        print("Victim: " + str(victim))

        pattern = r'[0-9]'
        strippedString = re.sub(pattern, '', victim)
        print(strippedString)
        if (strippedString != "Universe"):
            print(victim, ' hit at ', intoPosition)
            self.DestroyObject(victim, intoPosition)

        print(shooter + ' is DONE.')
        Missile.Intervals[shooter].finish()

    def DestroyObject(self, hitID, hitPosition):
        nodeID = base.render.find(f'**/{hitID}')
        nodeID.detachNode()

        self.explodeNode.setPos(hitPosition)
        self.Explode()

    def Explode(self):
        self.cntExplode += 1
        tag = 'particles-' + str(self.cntExplode)

        self.explodeIntervals[tag] = LerpFunc(self.ExplodeLight, duration = 1.0)
        self.explodeIntervals[tag].start()


    def ExplodeLight(self, t):
        if t == 1.0 and self.explodeEffect:
            self.explodeEffect.disable()

        elif t == 0:
            self.explodeEffect.start(self.explodeNode)



