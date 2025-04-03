from CollideObjectBase import SphereCollidableObject
from panda3d.core import Loader, NodePath, Vec3, CollisionHandlerEvent, CollisionTraverser
from direct.task.Task import TaskManager
from typing import Callable
from direct.task import Task
from direct.interval.LerpInterval import LerpFunc
from direct.particles.ParticleEffect import ParticleEffect
from SpaceJamClasses import Missile, Drone
from direct.gui.OnscreenImage import OnscreenImage
import re


global base

class Spaceship(SphereCollidableObject):
    def __init__(self, loader: Loader, taskMgr: TaskManager, accept: Callable[[str, Callable], None], modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float, drones: list):
        super(Spaceship, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1)
        self.taskMgr = taskMgr
        self.accept = accept
        self.traverser = base.cTrav
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.reloadTime = .25
        self.MultiShot = False
        self.homingMissiles = False
        self.drones = drones
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

    def InvertedControls(self):
        if not hasattr(self, 'invertedControls'):
            self.invertedControls = False  
        self.InvertedControls = not self.InvertedControls

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
    
    def getClosestDrone(self, drones):
        validDrones = [d for d in drones if not d.modelNode.isEmpty()]

        if not validDrones:
            print("No valid drones found.")
            return None
        closestDrone = min(validDrones, key=lambda d: (self.modelNode.getPos() - d.modelNode.getPos()).length())
        return closestDrone
        
    
    def FireMissile(self, offset=0):
            travRate = self.missileDistance
            aim = base.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            Speed = 1000
            fireSolution = aim * travRate
            inFront = aim * 150 + Vec3(offset, 0, 0)
            self.missileBay -= 1
            tag = 'Missile' + str(Missile.missileCount)
            posVec = self.modelNode.getPos() + inFront
            currentMissile = Missile(base.loader, './Assets/Phaser/phaser.egg', base.render, tag, posVec, 4.0)
            self.traverser.addCollider(currentMissile.collisionNode, self.handler)
            self.activeMissiles.append(currentMissile)
            if self.homingMissiles == False: 
                targetPos = fireSolution + self.modelNode.getPos()
            else: 
                closestDrone = self.getClosestDrone(self.drones)
                if closestDrone:
                    print("Homing missile locked onto:", closestDrone.modelNode.getName())
                    targetPos = closestDrone.modelNode.getPos()
                    Missile.Intervals[tag] = currentMissile.modelNode.posInterval(20, targetPos, startPos=posVec, fluid=1)
                    Missile.Intervals[tag].start()
                else:
                    print("No valid target for homing missile. Firing straight ahead.")
                    targetPos = fireSolution + self.modelNode.getPos()

            distance = (targetPos - posVec).length()
            travelTime = distance / Speed
            Missile.Intervals[tag] = currentMissile.modelNode.posInterval(travelTime, targetPos, startPos=posVec, fluid=1)
            Missile.Intervals[tag].start()

    def Fire(self):
        if self.missileBay:
            self.activeMissiles = []
            if self.MultiShot:
                print("Firing 3 missiles!")
                self.FireMissile(offset=-100)
                self.FireMissile(offset=0)
                self.FireMissile(offset=100)
            else:
                 self.FireMissile(offset=0)
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
        if self.activeMissiles:
            for missile in list(self.activeMissiles):  
                missilePos = missile.modelNode.getPos()
                print("Missile detonated at ", missilePos)
                self.explodeNode.setPos(missilePos)
                self.Explode()
                self.DestroyObject(missile.modelNode.getName(), missilePos)

            self.activeMissiles.clear()  
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
        rate = -.5 if not self.InvertedControls else 0.5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def RightTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyRightTurn, 'right-turn')

        else:
            self.taskMgr.remove('right-turn')

    def ApplyRightTurn(self, task):
        rate = .5 if not self.InvertedControls else -0.5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def UpTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyUpTurn, 'up-turn')

        else:
            self.taskMgr.remove('up-turn')

    def ApplyUpTurn(self, task):
        rate = -.5 if not self.InvertedControls else 0.5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return Task.cont

    def DownTurn(self, keyDown):
        if keyDown:
            self.taskMgr.add(self.ApplyDownTurn, 'down-turn')

        else:
            self.taskMgr.remove('down-turn')

    def ApplyDownTurn(self, task):
        rate = .5 if not self.InvertedControls else -0.5
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

        if intoNode == self.modelNode.getName():
            print("Player spaceship destroyed!")
            self.DestroyObject(intoNode, intoPosition)
            return
        
        if "Inverter" in intoNode:
            self.InvertedControls()
            base.render.find(intoNode).detachNode()
        elif "Multishot" in intoNode:
            self.MultiShot = True
            base.render.find(intoNode).detachNode()
        elif "DroneHoming" in intoNode:
            self.homingMissiles = True
            base.render.find(intoNode).detachNode()


        tempVar = fromNode.split('_')
        print("tempVar: " + str(tempVar))
        shooter = tempVar[0]
        print("Shooter: " + str(shooter))
        tempVar = intoNode.split('-')
        print("TempVar1: " + str(tempVar))
        tempVar = intoNode.split('-')
        print("TempVar2: " + str(tempVar))
        victim = tempVar[0]
        print("Victim: " + str(victim))

        pattern = r'[0-9]'
        strippedString = re.sub(pattern, '', victim)
        print(strippedString)
        if (strippedString != "Universe"):
            print(victim, ' hit at ', intoPosition)
            self.DestroyObject(victim, intoPosition)
        else:
            print("Please don't blow up the universe.")

        print(shooter + ' is DONE.')
        if shooter != "Hero":
            Missile.Intervals[shooter].finish()
        else:
            self.DestroyObject(shooter, intoPosition)

    def DestroyObject(self, hitID, hitPosition):
            nodeID = base.render.find(f'**/{hitID}')
            if not nodeID.isEmpty():
                nodeID.detachNode()
                self.drones = [drone for drone in self.drones if drone.modelNode.getName() != hitID]
                if hitID == self.modelNode.getName():
                    self.explodeNode.setPos(hitPosition)
                    self.Explode()
                    self.modelNode.detachNode()
                    self.taskMgr.remove("forward-thrust")
                    self.taskMgr.remove("left-turn")
                    self.taskMgr.remove("right-turn")
                    self.taskMgr.remove("up-turn")
                    self.taskMgr.remove("down-turn")
                    self.taskMgr.remove("right-rotate")
                    self.taskMgr.remove("left-rotate")
                    return
                

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



