
import msgParser
import carState
import carControl
import keyboard

class Driver(object):
    '''
    A driver object for the SCRC
    '''

    def __init__(self, stage):
        '''Constructor'''
        self.WARM_UP = 0
        self.QUALIFYING = 1
        self.RACE = 2
        self.UNKNOWN = 3
        self.stage = stage
        
        self.parser = msgParser.MsgParser()
        
        self.state = carState.CarState()
        
        self.control = carControl.CarControl()
        
        self.steer_lock = 0.785398
        self.max_speed = 100
        self.prev_rpm = None
    
    def init(self):
        '''Return init string with rangefinder angles'''
        self.angles = [0 for x in range(19)]
        
        for i in range(5):
            self.angles[i] = -90 + i * 15
            self.angles[18 - i] = 90 - i * 15
        
        for i in range(5, 9):
            self.angles[i] = -20 + (i-5) * 5
            self.angles[18 - i] = 20 - (i-5) * 5
        
        return self.parser.stringify({'init': self.angles})
    
    def drive(self, msg):
        '''Control the car using keyboard inputs'''
        self.state.setFromMsg(msg)

        accel = 0.0
        brake = 0.0
        steer = 0.0

        # Read keyboard inputs
        if keyboard.is_pressed('up'):
            accel += 1.0  # Increase acceleration

        if keyboard.is_pressed('down'):
            brake += 0.8  # Apply brakes instead of negative accel

        if keyboard.is_pressed('left'):
            steer += 0.5  # Turn left

        if keyboard.is_pressed('right'):
            steer -= 0.5  # Turn right

        # Set the control values
        self.gear()  # Ensure gear shifting works properly
        self.control.setBrake(brake)
        self.control.setSteer(steer)
        self.control.setAccel(accel)

        return self.control.toMsg()

    
    def steer(self):
        angle = self.state.angle
        dist = self.state.trackPos
        
        self.control.setSteer((angle - dist*0.5)/self.steer_lock)
    
    def gear(self):
        rpm = self.state.getRpm()
        gear = self.state.getGear()

        if gear <= 0:  # Ensure car is always in a valid forward gear
            gear = 1

        if rpm > 7000:
            gear += 1  # Upshift

        elif rpm < 3000 and gear > 1:
            gear -= 1  # Downshift, but not below 1

        self.control.setGear(gear)

    
    def speed(self):
        speed = self.state.getSpeedX()
        accel = self.control.getAccel()
        
        if speed < self.max_speed:
            accel += 0.1
            if accel > 1:
                accel = 1.0
        else:
            accel -= 0.1
            if accel < 0:
                accel = 0.0
        
        self.control.setAccel(accel)
            
        
    def onShutDown(self):
        pass
    
    def onRestart(self):
        pass
        