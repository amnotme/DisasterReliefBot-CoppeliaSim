# python
import math
import random


# Function to create a custom UI slider for controlling robot speed
def create_slider():
	xml = '<ui title="' + sim.getObjectAlias(self.bubbleRobBase,
	                                         1) + ' speed slider" closeable="false" resizeable="false" activate="false">'
	xml += '<hslider minimum="0" maximum="100" on-change="speedChange_callback" id="1"/>'
	xml += '<label text="" style="* {margin-left: 300px;}"/></ui>'
	return xml


# This function is executed once at the start of the simulation
def sysCall_init():
	# Retrieve essential handles and initialize attributes
	sim = require('sim')
	simUI = require('simUI')
	self.bubbleRobBase = sim.getObject('.')  # Handle for BubbleRob
	self.leftMotor = sim.getObject("./leftMotor")  # Handle for left motor
	self.rightMotor = sim.getObject("./rightMotor")  # Handle for right motor
	self.noseSensor = sim.getObject("./sensingNose")  # Handle for proximity sensor
	self.personSensor = sim.getObject("./personRadar")  # Handle for person sensor
	self.fireSensor = sim.getObject("./fireRadar")  # Handle for fire sensor

	# Set of unique identifiers for detected people and fires to prevent relogging
	self.detected_people = set()
	self.detected_fires = set()

	# Speed configurations for the motors
	self.minMaxSpeed = [50 * math.pi / 180, 300 * math.pi / 180]
	self.backUntilTime = -1  # Time until which the robot should move backwards

	# Create a collection for the robot and add visual elements for debugging
	self.robotCollection = sim.createCollection(0)
	sim.addItemToCollection(self.robotCollection, sim.handle_tree, self.bubbleRobBase, 0)
	self.distanceSegment = sim.addDrawingObject(sim.drawing_lines, 4, 0, -1, 1, [0, 1, 0])
	self.robotTrace = sim.addDrawingObject(sim.drawing_linestrip + sim.drawing_cyclic, 2, 0, -1, 500, [1, 1, 0], None,
	                                       None, [1, 1, 0])

	# Create and configure the custom UI for speed control
	self.ui = simUI.create(create_slider())
	self.speed = (self.minMaxSpeed[0] + self.minMaxSpeed[1]) / 2
	simUI.setSliderValue(self.ui, 1,
	                     100 * (self.speed - self.minMaxSpeed[0]) / (self.minMaxSpeed[1] - self.minMaxSpeed[0]))


# Regularly called to update sensor readings and visualization
def sysCall_sensing():
	result, distData, *_ = sim.checkDistance(self.robotCollection, sim.handle_all)
	if result > 0:
		# Update visual elements if an object is detected
		sim.addDrawingObjectItem(self.distanceSegment, None)
		sim.addDrawingObjectItem(self.distanceSegment, distData)

	# Update the robot's path trace
	p = sim.getObjectPosition(self.bubbleRobBase)
	sim.addDrawingObjectItem(self.robotTrace, p)


# Callback for speed slider UI element changes
def speedChange_callback(ui, id, newVal):
	self.speed = self.minMaxSpeed[0] + (self.minMaxSpeed[1] - self.minMaxSpeed[0]) * newVal / 100


# Function to handle the collision avoidance behavior
def collision_detection_handler(left_motor_jitter, right_motor_jitter):
	if self.backUntilTime < sim.getSimulationTime():
		# Move forward at the desired speed
		sim.setJointTargetVelocity(self.leftMotor, self.speed)
		sim.setJointTargetVelocity(self.rightMotor, self.speed)
	else:
		# Backup in a curve at reduced speed when an obstacle is detected
		sim.setJointTargetVelocity(self.leftMotor, -self.speed / left_motor_jitter)
		sim.setJointTargetVelocity(self.rightMotor, -self.speed / right_motor_jitter)


# Function to handle the sensing nose
def sensing_object_handler(left_motor_jitter, right_motor_jitter):
	# If we detected something, we set the backward mode:
	result, *_ = sim.readProximitySensor(self.noseSensor)
	if result > 0:
		self.backUntilTime = sim.getSimulationTime() + 1

	collision_detection_handler(left_motor_jitter, right_motor_jitter)


# Function to handle person detection
def sensing_person_handler():
	def find_person(object):
		# Check if the detected object is a person
		for person in range(0, 7):
			if sim.getObjectAlias(object) == f'Person{person}':
				return True
		return False

	# Read the person sensor and handle detection
	person_result, distance, point, object, n = sim.readProximitySensor(self.personSensor)
	if person_result > 0 and object and find_person(object):
		alias_name = sim.getObjectAlias(object)
		if alias_name not in self.detected_people:
			# Log the detection only once
			print(f"{alias_name} has been found at {round(point[0], 4), round(point[1], 4), round(point[2], 4)}")
			self.detected_people.add(alias_name)


# Function to handle fire detection
def sensing_fire_handler(left_motor_jitter, right_motor_jitter):
	def sense_fire(object):
		# Check if the detected object is a fire
		for fire in range(0, 5):
			if sim.getObjectAlias(object) == f'Fire{fire}':
				return True
		return False

	# Read the fire sensor and handle detection
	fire_result, distance, point, object, n = sim.readProximitySensor(self.fireSensor)
	if fire_result > 0 and object and sense_fire(object):
		self.backUntilTime = sim.getSimulationTime() + 0.5
		if sim.getObjectAlias(object) not in self.detected_fires:
			# Log the detection only once
			alias_name = sim.getObjectAlias(object)
			print(
				f"[Alert] - {alias_name} has been spotted at {round(point[0], 4), round(point[1], 4), round(point[2], 4)}")
			self.detected_fires.add(alias_name)

	collision_detection_handler(left_motor_jitter, right_motor_jitter)


# Regularly called to handle actuation based on sensor inputs
def sysCall_actuation():
	# Introduce randomness to the motor behavior to create a more exploratory movement pattern
	left_motor_jitter = random.choice([i for i in range(1, 11)]) / 10
	right_motor_jitter = random.choice([j for j in range(8, 64, 4)])

	# Call sensor handlers
	sensing_object_handler(left_motor_jitter, right_motor_jitter)
	sensing_fire_handler(left_motor_jitter, right_motor_jitter)
	sensing_person_handler()


# Called once when the simulation ends to clean up
def sysCall_cleanup():
	simUI.destroy(self.ui)
