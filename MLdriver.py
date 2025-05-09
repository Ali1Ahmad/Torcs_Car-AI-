import joblib
import msgParser
import carState
import carControl
import numpy as np

class MLDriver:
    def __init__(self, stage):
        self.stage = stage
        self.parser = msgParser.MsgParser()
        self.state = carState.CarState()
        self.control = carControl.CarControl()
        self.steer_lock = 0.785398

        # Load trained models
        self.reg_model = joblib.load("torcs_reg_model.pkl")
        self.clf_model = joblib.load("torcs_gear_classifier.pkl")

    def init(self):
        angles = [0 for _ in range(19)]
        for i in range(5):
            angles[i] = -90 + i * 15
            angles[18 - i] = 90 - i * 15
        for i in range(5, 9):
            angles[i] = -20 + (i - 5) * 5
            angles[18 - i] = 20 - (i - 5) * 5
        return self.parser.stringify({'init': angles})

    def drive(self, msg):
        self.state.setFromMsg(msg)

        # Extract features
        try:
            features = [
                self.state.getAngle(),
                self.state.getCurLapTime(),
                self.state.getDistFromStart(),
                self.state.getDistRaced(),
                self.state.getFuel(),
                self.state.getGear(),
                self.state.getLastLapTime(),
                self.state.getRacePos(),
                self.state.getRpm(),
                self.state.getSpeedX(),
                self.state.getSpeedY(),
                self.state.getSpeedZ(),
                self.state.getTrackPos(),
                self.state.getZ()
            ] + self.state.getTrack()

            features = np.array(features).reshape(1, -1)

            # Predict control actions
            accel, brake, steer = self.reg_model.predict(features)[0]
            gear = self.clf_model.predict(features)[0]

            # Set controls
            self.control.setAccel(accel)
            self.control.setBrake(brake)
            self.control.setSteer(steer)
            self.control.setGear(gear)

        except Exception as e:
            print(f"⚠️ Prediction error: {e}")
            self.control.setAccel(0.3)
            self.control.setBrake(0)
            self.control.setSteer(0)
            self.control.setGear(1)

        return self.control.toMsg()

    def onShutDown(self):
        pass

    def onRestart(self):
        pass
