from direct.showbase.ShowBase import ShowBase
import DefensePaths as defensePaths
import SpaceJamClasses as spaceJamClasses
import Player
from panda3d.core import CollisionTraverser, CollisionHandlerPusher

class MyApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)  
        self.cTrav = CollisionTraverser()
        self.cTrav.traverse(self.render)
        self.drones = []
        self.SetupScene() 
        self.pusher = CollisionHandlerPusher()
        self.pusher.addCollider(self.Spaceship.collisionNode, self.Spaceship.modelNode)
        self.cTrav.addCollider(self.Spaceship.collisionNode, self.Spaceship.handler)
        self.cTrav.showCollisions(self.render)
        
    def SetCamera(self):
        self.disableMouse()
        self.camera.reparentTo(self.Spaceship.modelNode)
        self.camera.setFluidPos(0, 1, 0)


    def SetupScene(self):
      self.Universe = spaceJamClasses.Universe(self.loader, "./Assets/Universe/Universe.x", self.render, 'Universe', 'Assets/Universe/universe.jpg', (0, 0, 0), 10000)
      self.PowerUp1 = spaceJamClasses.PowerUp(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Inverter', 'Assets/PowerUps/red.png', (0, 0, 0), 75)
      self.PowerUp2 = spaceJamClasses.PowerUp(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Multishot', 'Assets/PowerUps/yellow.png', (100, 300, 67), 75)
      self.PowerUp3 = spaceJamClasses.PowerUp(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'DroneHoming', 'Assets/PowerUps/blue.png', (300, 100, 67), 75)
      self.Planet1 = spaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Earth', 'Assets/Planets/earth.jpg', (150, 5000, 67), 300)
      self.Planet2 = spaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Mars', 'Assets/Planets/mars.jpg', (1300, 5000, 67), 200)
      self.Planet3 = spaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Jupiter', 'Assets/Planets/jupiter.jpg', (-1350, 5000, 67), 450)
      self.Planet4 = spaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Saturn', 'Assets/Planets/saturn.jpg', (2450, 5000, 67), 350)
      self.Planet5 = spaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Venus', 'Assets/Planets/venus.jpg', (3800, 5000, 67), 300)
      self.Planet6 = spaceJamClasses.Planet(self.loader, "./Assets/Planets/protoPlanet.x", self.render, 'Uranus', 'Assets/Planets/uranus.jpg', (-2500, 5000, 67), 200)
      self.Station = spaceJamClasses.SpaceStation(self.loader, "./Assets/SpaceStation/spaceStation.x", self.render, 'Universe', 'Assets/SpaceStation/SpaceStation1_Dif2.png', (150, 8000, 3000), 25)
      self.Spaceship = Player.Spaceship(self.loader, self.taskMgr, self.accept, "./Assets/Spaceships/Dumbledore.x", self.render, 'Hero', 'Assets/Spaceships/spacejet_C.png', (150, 6000, 1500), 10, self.drones)
      self.Sentinal1 = spaceJamClasses.Orbiter(self.loader, self.taskMgr, "./Assets/DroneDefender/DroneDefender.obj", self.render, "Drone", 6.0, "./Assets/DroneDefender/octotoad1_auv.png", self.Planet1, 300, "MLB", self.Spaceship)
      self.Sentinal2 = spaceJamClasses.Orbiter(self.loader, self.taskMgr, "./Assets/DroneDefender/DroneDefender.obj", self.render, "Drone", 6.0, "./Assets/DroneDefender/octotoad1_auv.png", self.Planet4, 350, "Cloud", self.Spaceship)
      self.SetCamera()
      
      fullCycle = 30
      if spaceJamClasses.Drone.droneCount == 0:
        for j in range(fullCycle):
         spaceJamClasses.Drone.droneCount += 1
         nickName = "Drone" + str(spaceJamClasses.Drone.droneCount)
  
         self.DrawCloudDefense(self.Planet1, nickName)
         self.DrawBaseballSeams(self.Station, nickName, j, fullCycle, 1)
         self.DrawCircle(self.Planet2, nickName + "_X", j, fullCycle, axis='X')
         self.DrawCircle(self.Planet3, nickName + "_Y", j, fullCycle, axis='Y')
         self.DrawCircle(self.Planet4, nickName + "_Z", j, fullCycle, axis='Z')
      
    def DrawBaseballSeams(self, centralObject, droneName, step, numSeams, radius = 1):
     unitVec = defensePaths.BaseballSeams(step, numSeams, B = 0.4)
     unitVec.normalize()
     position = unitVec * radius * 250 + centralObject.modelNode.getPos()
     drone = spaceJamClasses.Drone(self.loader, "./Assets/DroneDefender/DroneDefender.obj", self.render, droneName, "./Assets/DroneDefender/octotoad1_auv.png", position, 5)
     self.drones.append(drone)
    def DrawCloudDefense(self, centralObject, droneName):
     unitVec = defensePaths.Cloud()
     unitVec.normalize()
     position = unitVec * 500 + centralObject.modelNode.getPos()
     drone = spaceJamClasses.Drone(self.loader, "./Assets/DroneDefender/DroneDefender.obj", self.render, droneName, "./Assets/DroneDefender/octotoad1_auv.png", position, 10)
     self.drones.append(drone)
    def DrawCircle(self, centralObject, droneName, step, numDrones, radius = 1, axis = 'X'):
     for i in range(numDrones):
        position = defensePaths.circleMath(i, numDrones, (radius * 500), axis) + centralObject.modelNode.getPos()
        drone = spaceJamClasses.Drone(self.loader, "./Assets/DroneDefender/DroneDefender.obj", self.render, droneName + str(i), "./Assets/DroneDefender/octotoad1_auv.png", position, 5)
        self.drones.append(drone)

app = MyApp()
app.run()
